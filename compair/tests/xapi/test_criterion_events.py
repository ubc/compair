import json

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_criterion_create, \
    on_criterion_update

class CriterionXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student
        self.criterion = self.data.create_criterion(self.user)

    def test_on_criterion_create(self):
        on_criterion_create.send(
            current_app._get_current_object(),
            event_name=on_criterion_create.name,
            user=self.user,
            criterion=self.criterion
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/author',
            'display': {'en-US': 'authored'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/criterion/'+self.criterion.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.criterion.name },
                'description': {'en-US': self.criterion.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])


    def test_on_criterion_update(self):
        on_criterion_update.send(
            current_app._get_current_object(),
            event_name=on_criterion_update.name,
            user=self.user,
            criterion=self.criterion
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/criterion/'+self.criterion.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.criterion.name },
                'description': {'en-US': self.criterion.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])