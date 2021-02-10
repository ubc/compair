# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from contextlib import contextmanager
import copy
import json
import unittest
import mock
import uuid
import sys
import os
import factory.fuzzy
import pytz
import datetime
from hashlib import md5

from flask import session as sess
from flask_testing import TestCase
from os.path import dirname
from flask.testing import FlaskClient
from six import wraps

from compair import create_app
from compair.manage.database import populate
from compair.core import db
from compair.models import User, XAPILog, CaliperLog
from compair.tests import test_app_settings
from lti import ToolConsumer
from lti.utils import parse_qs

# Tests Checklist
# - Unauthenticated users refused access with 401
# - Authenticated but unauthorized users refused access with 403
# - Non-existent entry errors out with 404
# - If post request, bad input format gets rejected with 400

def json_recorder(filename, key=None):
    """
    This decorator will load the fixture, inject data to the function and write back to the file.

    It also writes the json value (ret_value.json) of the return from wrapped function to the file.

    :param filename: filename to load
    :param key: key to use for the return result
    :return: decorator factory
    """
    def _decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            file_path_name = '{}/../../data/fixtures/{}'.format(dirname(__file__), filename)
            with open(file_path_name, 'r') as f:
                try:
                    data = json.load(f)
                except ValueError:
                    data = {}

            def collect_from_response(resp_key, response):
                data[resp_key] = {
                    'body': response.json,
                    'status_code': response.status_code
                }
                data['_modified'] = True

            ret = func(*(args + (collect_from_response,)), **kwargs)
            if ret is None and '_modified' not in data:
                return
            dict_key = func.__name__ if key is None else key
            if ret is not None:
                collect_from_response(dict_key, ret)

            del data['_modified']
            with open(file_path_name, 'w') as f:
                json.dump(data, f, indent=4)
        return wrapper
    return _decorator

@contextmanager
def suppress_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout

class ComPAIRTestCase(TestCase):
    def create_app(self):
        app = create_app(settings_override=test_app_settings)
        return app

    def setUp(self):
        db.create_all()
        with suppress_stdout():
            populate(default_data=True)
        # reset login settings in case tests fail
        self.app.config['APP_LOGIN_ENABLED'] = True
        self.app.config['CAS_LOGIN_ENABLED'] = True
        self.app.config['SAML_LOGIN_ENABLED'] = True
        self.app.config['LTI_LOGIN_ENABLED'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class ComPAIRAPITestCase(ComPAIRTestCase):
    api = None
    resource = None

    @contextmanager
    def login(self, username, password="password"):
        payload = json.dumps({
            'username': username,
            'password': password
        })
        rv = self.client.post('/api/login', data=payload, content_type='application/json', follow_redirects=True)
        self.assert200(rv)
        yield rv
        self.client.delete('/api/logout', follow_redirects=True)

    @contextmanager
    def cas_login(self, cas_username, follow_redirects=True):
        response_mock = mock.MagicMock()
        response_mock.success = True
        response_mock.user = cas_username
        response_mock.attributes = {}

        with mock.patch('compair.api.login.validate_cas_ticket', return_value=response_mock):
            rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=follow_redirects)
            if follow_redirects:
                self.assert200(rv)
            yield rv
            self.client.delete('/api/logout', follow_redirects=True)

    @contextmanager
    def saml_login(self, saml_unique_identifier, follow_redirects=True):
        response_mock = mock.MagicMock()
        response_mock.get_errors.return_value = []
        response_mock.is_authenticated.return_value = True
        response_mock.get_attributes.return_value = {
            'urn:oid:0.9.2342.19200300.100.1.1': [saml_unique_identifier]
        }
        response_mock.get_nameid.return_value = "saml_mock_nameid"
        response_mock.get_session_index.return_value = "saml_session_index"

        with mock.patch('compair.api.login.get_saml_auth_response', return_value=response_mock):
            rv = self.client.post('/api/saml/auth', follow_redirects=follow_redirects)
            if follow_redirects:
                self.assert200(rv)
            yield rv
            self.client.delete('/api/logout', follow_redirects=True)

    @contextmanager
    def lti_launch(self, lti_consumer, lti_resource_link_id,
                         assignment_uuid=None, query_assignment_uuid=None,
                         nonce=None, timestamp=None, follow_redirects=True,
                         invalid_launch=False, **kwargs):
        launch_url = "http://localhost/api/lti/auth"
        oauth_signature = kwargs.pop('oauth_signature', None)
        launch_params = kwargs.copy()
        launch_params['resource_link_id'] = lti_resource_link_id
        if assignment_uuid:
            launch_params['custom_assignment'] = assignment_uuid
        if query_assignment_uuid:
            launch_url = launch_url+"?assignment="+query_assignment_uuid

        # add basic required launch parameters
        if not 'lti_version' in launch_params:
           launch_params['lti_version'] = "LTI-1p0"

        if not 'lti_message_type' in launch_params:
           launch_params['lti_message_type'] = "basic-lti-launch-request"

        if 'roles' in launch_params and launch_params.get('roles') == None:
            launch_params.pop('roles')

        tool_consumer = ToolConsumer(
            lti_consumer.oauth_consumer_key,
            lti_consumer.oauth_consumer_secret,
            params=launch_params,
            launch_url=launch_url
        )

        # overwrite lti_version and lti_message_type if needed (set by lti.LaunchParams)
        if 'lti_version' in launch_params and launch_params.get('lti_version') == None:
            tool_consumer.launch_params._params.pop('lti_version')

        if 'lti_message_type' in launch_params and launch_params.get('lti_message_type') == None:
            tool_consumer.launch_params._params.pop('lti_message_type')

        if invalid_launch:
            with mock.patch.object(ToolConsumer, 'has_required_params', return_value=True):
                launch_request = tool_consumer.generate_launch_request(nonce=nonce, timestamp=timestamp)
        else:
            launch_request = tool_consumer.generate_launch_request(nonce=nonce, timestamp=timestamp)

        launch_data = parse_qs(launch_request.body.decode('utf-8'))

        # overwrite oauth_signature for tests
        if invalid_launch and oauth_signature:
            launch_data['oauth_signature'] = oauth_signature

        rv = self.client.post('/api/lti/auth', data=launch_data, follow_redirects=follow_redirects)
        yield rv
        rv.close()

    @contextmanager
    def impersonate(self, original_user, target_user):
        with self.login(original_user.username) if original_user else contextlib.suppress():
            rv = self.client.post('/api/impersonate/' + target_user.uuid,
                content_type='application/json', follow_redirects=True)
            self.assert200(rv)
            yield rv
            rv = self.client.delete('/api/impersonate', follow_redirects=True)
            self.assert200(rv)

    def get_url(self, **values):
        return self.api.url_for(self.resource, **values)

class ComPAIRAPIDemoTestCase(ComPAIRAPITestCase):
    def setUp(self):
        db.create_all()
        with suppress_stdout():
            populate(default_data=True, sample_data=True)
        self.app.config['DEMO_INSTALLATION'] = True


class ComPAIRLearningRecordTestCase(ComPAIRTestCase):
    xapi_compair_source_category = {
        'id': 'http://xapi.learninganalytics.ubc.ca/category/compair',
        'definition': {'type': 'http://id.tincanapi.com/activitytype/source'},
        'objectType': 'Activity'
    }
    app_base_url = 'https://localhost:8888/'
    caliper_contexts = [
        'http://purl.imsglobal.org/ctx/caliper/v1p2',
    ]

    def create_app(self):
        settings = test_app_settings.copy()
        settings['XAPI_ENABLED'] = True
        settings['LRS_XAPI_STATEMENT_ENDPOINT'] = 'local'
        settings['CALIPER_ENABLED'] = True
        settings['LRS_CALIPER_HOST'] = 'local'
        # you can certify by uncommenting, running nosetests compair.tests.learning_records, and
        # running a few navigation events on the front end
        # settings['LRS_CALIPER_HOST'] = 'https://caliper-dev.imsglobal.org/caliper/4d7a0b79-0d0f-4127-808d-bfe88b6e037f/message'
        # settings['LRS_CALIPER_API_KEY'] = '4d7a0b79-0d0f-4127-808d-bfe88b6e037f'
        settings['LRS_APP_BASE_URL'] = self.app_base_url
        app = create_app(settings_override=settings)

        # make it easier to debug
        self.maxDiff = None
        return app

    @contextmanager
    def setup_session_data(self, user):
        sess['user_id'] = user.id
        sess['session_token'] = user.generate_session_token()
        sess['session_id'] = md5(sess['session_token'].encode('UTF-8')).hexdigest()
        sess['start_at'] = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def generate_tracking(self, **kargs):
        tracking = {
            'registration': str(uuid.uuid4()),
            'started': datetime.datetime.now() - datetime.timedelta(minutes=7),
            'ended': datetime.datetime.now() - datetime.timedelta(minutes=6),
            'duration': "PT02.475S"
        }

        if kargs:
            tracking.update(kargs)

        return tracking

    def _validate_and_cleanup_xapi_statement(self, statement):
        # check categories
        categories = statement['context']['contextActivities']['category']
        self.assertIn(self.xapi_compair_source_category, categories)
        categories.remove(self.xapi_compair_source_category)

        self.assertEqual(statement['context']['platform'], 'https://localhost:8888')
        del statement['context']['platform']

        if len(categories) == 0:
            del statement['context']['contextActivities']['category']
        if len(statement['context']['contextActivities']) == 0:
            del statement['context']['contextActivities']
        if len(statement['context']) == 0:
            del statement['context']

        # check timestamp
        self.assertEqual(statement['version'], '1.0.3')
        del statement['version']

        self.assertIsNotNone(statement['timestamp'])
        del statement['timestamp']

    def get_and_clear_xapi_statement_log(self):
        statements = []
        for xapi_log in XAPILog.query.all():
            statement = json.loads(xapi_log.statement)

            self._validate_and_cleanup_xapi_statement(statement)

            statements.append(statement)
        XAPILog.query.delete()
        return statements

    def get_unique_identifier_xapi_actor(self, user, homepage, identifier, third_party_users=[], lti_users=[]):
        return {
            'account': {'homePage': homepage, 'name': identifier },
            'name': user.fullname,
            'objectType': 'Agent'
        }

    def get_compair_xapi_actor(self, user, third_party_users=[], lti_users=[]):
        return {
            'account': {'homePage': 'https://localhost:8888/', 'name': user.uuid },
            'name': user.fullname,
            'objectType': 'Agent'
        }

    def get_xapi_session_info(self):
        session_info = {
            'id': 'https://localhost:8888/session/'+sess.get("session_id"),
            'start_at': sess.get('start_at'),
            'login_method': sess.get('login_method')
        }
        if sess.get('end_at'):
            session_info['end_at'] = sess.get('end_at')

        return session_info

    def _del_empty_caliper_field(self, event_dict):
        # this is done in order to trim down all the empty fields that Caliper will throw in
        # makes testing events manageable
        keys_to_delete = []
        for k, v in event_dict.items():
            if k == '@context':
                self.assertIn(v, self.caliper_contexts)
                keys_to_delete.append(k)
            elif isinstance(v, dict):
                # recursively remove empty fields
                self._del_empty_caliper_field(v)

                if len(v.keys()) == 0:
                    keys_to_delete.append(k)
            elif isinstance(v, list):
                list_index_to_remove = []
                # remove empty fields from list objects
                for index, v2 in enumerate(v):
                    if isinstance(v2, dict):
                        self._del_empty_caliper_field(v2)
                        if len(v2.keys()) == 0:
                            list_index_to_remove.append(index)

                for index in reversed(list_index_to_remove):
                    del v[index]

                # remove empty lists
                if len(v) == 0:
                    keys_to_delete.append(k)
            elif v == None:
                keys_to_delete.append(k)

        for k in keys_to_delete:
            del event_dict[k]

    def _validate_and_cleanup_caliper_event(self, event):
        self._del_empty_caliper_field(event)

        if event.get('@context'):
            self.assertIn(event['@context'], self.caliper_contexts)

        self.assertEqual(event['edApp'], {
            'id': self.app_base_url.rstrip("/"),
            'type': 'SoftwareApplication',
            'name': 'ComPAIR',
            'description': 'The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.',
            'version': self.app.config.get('COMPAIR_VERSION', None)
        })
        del event['edApp']

        self.assertIsNotNone(event['eventTime'])
        del event['eventTime']

        self.assertIsNotNone(event['id'])
        del event['id']

        self.assertIsNotNone(event['type'])
        self.assertIsNotNone(event['object'])
        self.assertIsNotNone(event['actor'])
        self.assertIsNotNone(event['session'])

        return event

    def get_and_clear_caliper_event_log(self):
        events = []
        for caliper_log in CaliperLog.query.all():
            event = json.loads(caliper_log.event)

            self._validate_and_cleanup_caliper_event(event)

            events.append(event)
        CaliperLog.query.delete()
        return events

    def get_caliper_session(self, caliper_actor):
        caliper_session = {
            'id': 'https://localhost:8888/session/'+sess.get("session_id"),
            'type': 'Session',
            'user': caliper_actor,
            'dateCreated': sess.get('start_at'),
            'startedAtTime': sess.get('start_at'),
            'client': {
                'id': 'https://localhost:8888/session/'+sess.get("session_id")+'/client',
                'type': 'SoftwareApplication',
                'ipAddress': '', # TODO fake this
                'userAgent': '', # TODO fake this
                'host': 'localhost',
            }
        }

        if sess.get('login_method') != None:
            caliper_session["extensions"] = {
                "login_method": sess.get('login_method')
            }

        if sess.get('end_at'):
            caliper_session['endedAtTime'] = sess.get('end_at')

        return caliper_session

    def get_caliper_membership(self, course, user, lti_context=None):
        membership = {
            'id': "https://localhost:8888/app/course/"+course.uuid+"/user/"+user.uuid,
            'type': "Membership",
            'member': self.get_compair_caliper_actor(user),
            'organization': "https://localhost:8888/app/course/"+course.uuid,
            'roles': ['Learner'],
            'status': 'Active'
        }
        if lti_context:
            membership['extensions'] = {
                'sis_courses': [{
                    'id': lti_context.lis_course_offering_sourcedid,
                    'section_ids': [lti_context.lis_course_section_sourcedid]
                }]
            }

        return membership

    def _add_other_identifiers_to_actor(self, actor, third_party_users=[], lti_users=[]):
        if len(lti_users) > 0 or len(third_party_users) > 0:
            if not actor.get('otherIdentifiers'):
                actor['otherIdentifiers'] = []

            for lti_user in lti_users:
                actor['otherIdentifiers'].append({
                    'identifier': lti_user.user_id,
                    'identifierType': 'LtiUserId',
                    'type': 'SystemIdentifier',
                    'extensions': {
                        'oauth_consumer_key': lti_user.oauth_consumer_key,
                        'global_unique_identifier': lti_user.global_unique_identifier,
                        'student_number': lti_user.student_number,
                        'lis_person_sourcedid': lti_user.lis_person_sourcedid,
                    }
                })

            for third_party_user in third_party_users:
                actor['otherIdentifiers'].append({
                    'identifier': third_party_user.unique_identifier,
                    'identifierType': 'SystemId',
                    'type': 'SystemIdentifier',
                    'extensions': {
                        'third_party_type': third_party_user.third_party_type.value
                    }
                })

    def get_unique_identifier_caliper_actor(self, user, homepage, identifier, third_party_users=[], lti_users=[]):
        if not homepage.endswith('/'):
            homepage += '/'
        actor = {
            'dateCreated': user.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': user.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': homepage+identifier,
            'type': "Person",
            'name': user.fullname,
            'otherIdentifiers': [{
                'identifier': identifier,
                'identifierType': 'SisSourcedId',
                'type': 'SystemIdentifier',
                'source': homepage,
            },{
                'identifier': user.uuid,
                'identifierType': 'SystemId',
                'type': 'SystemIdentifier',
                'source': 'https://localhost:8888',
            }]
        }
        self._add_other_identifiers_to_actor(actor, third_party_users, lti_users)

        return actor

    def get_compair_caliper_actor(self, user, third_party_users=[], lti_users=[]):
        actor = {
            'id': "https://localhost:8888/"+user.uuid,
            'dateCreated': user.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': user.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': "Person",
            'name': user.fullname,
        }
        self._add_other_identifiers_to_actor(actor, third_party_users, lti_users)
        return actor

class SessionTests(ComPAIRAPITestCase):
    def test_loggedin_user_session(self):
        with self.login('root', 'password'):
            rv = self.client.get('/api/session')
            self.assert200(rv)
            root = rv.json
            root_user = User.query.filter_by(username="root").first()
            self.assertEqual(root['id'], root_user.uuid)

    def test_non_loggedin_user_session(self):
        rv = self.client.get('/api/session')
        self.assert401(rv)