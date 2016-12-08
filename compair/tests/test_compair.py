from contextlib import contextmanager
import copy
import json
import unittest
import mock
import uuid

from flask_testing import TestCase
from os.path import dirname
from flask.testing import FlaskClient
from six import wraps

from compair import create_app
from compair.manage.database import populate
from compair.core import db
from compair.models import User, XAPILog
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


class ComPAIRTestCase(TestCase):
    def create_app(self):
        app = create_app(settings_override=test_app_settings)
        app.config['ENFORCE_SSL'] = False
        return app

    def setUp(self):
        db.create_all()
        populate(default_data=True)
        # reset login settings in case tests fail
        self.app.config['APP_LOGIN_ENABLED'] = True
        self.app.config['CAS_LOGIN_ENABLED'] = True
        self.app.config['LTI_LOGIN_ENABLED'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class ComPAIRXAPITestCase(ComPAIRTestCase):
    compair_source_category = {
        'id': 'http://xapi.ubc.ca/category/compair',
        'definition': {'type': 'http://id.tincanapi.com/activitytype/source'},
        'objectType': 'Activity'
    }

    def generate_tracking(self, with_duration=False, **kargs):
        tracking = {
            'registration': str(uuid.uuid4())
        }
        if with_duration:
            tracking['duration'] = "PT02.475S"

        if kargs:
            tracking.update(kargs)

        return tracking

    def get_and_clear_statement_log(self, has_request=False):
        statements = []
        for xapi_log in XAPILog.query.all():
            statement = json.loads(xapi_log.statement)

            # check categories
            categories = statement['context']['contextActivities']['category']
            self.assertIn(self.compair_source_category, categories)
            categories.remove(self.compair_source_category)

            if len(categories) == 0:
                del statement['context']['contextActivities']['category']
            if len(statement['context']['contextActivities']) == 0:
                del statement['context']['contextActivities']
            if len(statement['context']) == 0:
                del statement['context']

            # check timestamp
            self.assertIsNotNone(statement['timestamp'])

            statements.append(statement)
        XAPILog.query.delete()
        return statements

    def get_cas_actor(self, user):
        pass

    def get_compair_actor(self, user):
        return {
            'account': {'homePage': 'https://localhost:8888/', 'name': user.uuid },
            'name': user.fullname,
            'objectType': 'Agent'
        }

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
    def cas_login(self, cas_username):
        with mock.patch('flask_cas.CAS.username', new_callable=mock.PropertyMock) as mocked_cas_username:
            mocked_cas_username.return_value = cas_username
            rv = self.client.get('/api/auth/cas', data={}, content_type='application/json', follow_redirects=True)
            self.assert200(rv)
            yield rv
            self.client.delete('/api/logout', follow_redirects=True)

    @contextmanager
    def lti_launch(self, lti_consumer, lti_resource_link_id,
                         assignment_uuid=None, nonce=None, timestamp=None, follow_redirects=True,
                         **kwargs):
        launch_params = kwargs.copy()
        launch_params['resource_link_id'] = lti_resource_link_id
        if assignment_uuid:
            launch_params['custom_assignment'] = assignment_uuid

        tool_consumer = ToolConsumer(
            lti_consumer.oauth_consumer_key,
            lti_consumer.oauth_consumer_secret,
            params=launch_params,
            #launch_url not actually used. Just needed for validation
            launch_url='http://localhost/api/lti/auth'
        )

        launch_request = tool_consumer.generate_launch_request(nonce=nonce, timestamp=timestamp)
        launch_data = parse_qs(launch_request.body.decode('utf-8'))
        rv = self.client.post('/api/lti/auth', data=launch_data, follow_redirects=follow_redirects)
        yield rv
        rv.close()

    def get_url(self, **values):
        return self.api.url_for(self.resource, **values)


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