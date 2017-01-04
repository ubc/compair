import json

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_login_with_method, on_logout

class AuthenticationXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student

    def test_on_login_with_method(self):
        # no login method provided
        on_login_with_method.send(
            current_app._get_current_object(),
            event_name=on_login_with_method.name,
            user=self.user
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'https://brindlewaye.com/xAPITerms/verbs/loggedin/',
            'display': {'en-US': 'logged in'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/',
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/service', 'name': {'en-US': 'ComPAIR'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])

        # test with login method
        login_method = "CAS"
        on_login_with_method.send(
            current_app._get_current_object(),
            event_name=on_login_with_method.name,
            user=self.user,
            login_method=login_method
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'https://brindlewaye.com/xAPITerms/verbs/loggedin/',
            'display': {'en-US': 'logged in'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/',
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/service', 'name': {'en-US': 'ComPAIR'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'extensions': {'http://xapi.analytics.ubc.ca/extension/login-method': login_method}
        })

    def test_on_logout(self):
        # not method provided
        on_logout.send(
            current_app._get_current_object(),
            event_name=on_logout.name,
            user=self.user
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'https://brindlewaye.com/xAPITerms/verbs/loggedout/',
            'display': {'en-US': 'logged out'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/',
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/service', 'name': {'en-US': 'ComPAIR'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])
