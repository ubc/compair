# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
import pytz

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from flask import current_app, session as sess
from compair.core import db

from compair.learning_records.capture_events import on_login_with_method, on_logout

class AuthenticationLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student
        self.setup_session_data(self.user)


        self.expected_caliper_object = {
            "id": 'https://localhost:8888',
            "type": "SoftwareApplication",
            "name": "ComPAIR",
            "description": "The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.",
            "version": self.app.config.get("COMPAIR_VERSION")
        }
        self.expected_xapi_object = {
            'id': 'https://localhost:8888',
            'objectType': 'Activity',
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/service',
                'name': {'en-US': 'ComPAIR'},
                'extensions': {
                    'http://id.tincanapi.com/extension/version': self.app.config.get("COMPAIR_VERSION")
                }
            }
        }

    def test_on_login_with_method(self):
        # no login method provided
        on_login_with_method.send(
            current_app._get_current_object(),
            event_name=on_login_with_method.name,
            user=self.user
        )

        expected_caliper_event = {
            'action': 'LoggedIn',
            'profile': 'SessionProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': self.expected_caliper_object,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'SessionEvent'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'https://brindlewaye.com/xAPITerms/verbs/loggedin/',
                'display': {'en-US': 'logged in'}
            },
            "object": self.expected_xapi_object,
            "context": {
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            },
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

        # test with login method
        sess['login_method'] = "SAML"
        on_login_with_method.send(
            current_app._get_current_object(),
            event_name=on_login_with_method.name,
            user=self.user
        )

        expected_caliper_event['session'] = self.get_caliper_session(self.get_compair_caliper_actor(self.user))

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_statement['context']['extensions']['http://id.tincanapi.com/extension/session-info'] = self.get_xapi_session_info()
        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

    def test_on_logout(self):
        sess['end_at'] = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        # not method provided
        on_logout.send(
            current_app._get_current_object(),
            event_name=on_logout.name,
            user=self.user
        )

        expected_caliper_event = {
            'action': 'LoggedOut',
            'profile': 'SessionProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': self.expected_caliper_object,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'SessionEvent'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'https://brindlewaye.com/xAPITerms/verbs/loggedout/',
                'display': {'en-US': 'logged out'}
            },
            "object": self.expected_xapi_object,
            "context": {
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            },
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)