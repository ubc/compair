import json

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_user_modified

class UserXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student

    def test_on_user_modified(self):
        # no changes provided
        on_user_modified.send(
            current_app._get_current_object(),
            event_name=on_user_modified.name,
            user=self.user
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/#/user/'+self.user.uuid,
            'definition': {'type': 'http://id.tincanapi.com/activitytype/user-profile', 'name': {'en-US': 'user profile'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])

        # test with changes
        changes = {
            'some_string': 'some_value',
            'some_number': 42,
            'some_dict': {
                'some_string': 'some_value',
                'some_number': 42
            }
        }
        on_user_modified.send(
            current_app._get_current_object(),
            event_name=on_user_modified.name,
            user=self.user,
            data={'changes': changes}
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/#/user/'+self.user.uuid,
            'definition': {'type': 'http://id.tincanapi.com/activitytype/user-profile', 'name': {'en-US': 'user profile'}},
            'objectType': 'Activity'
        })
        self.assertEqual(statements[0]['result'], {
            'extensions': {'http://xapi.learninganalytics.ubc.ca/extension/fields-changed': changes}
        })
        self.assertNotIn('context', statements[0])