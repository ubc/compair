import json

from data.fixtures.test_data import SimpleAssignmentTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_assignment_create, \
    on_assignment_modified, on_assignment_delete

class AssignmentXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]

    def test_on_assignment_create(self):
        on_assignment_create.send(
            current_app._get_current_object(),
            event_name=on_assignment_create.name,
            user=self.user,
            assignment=self.assignment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/author',
            'display': {'en-US': 'authored'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name },
                'description': {'en-US': self.assignment.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
            }
        })



    def test_on_assignment_modified(self):
        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=self.user,
            assignment=self.assignment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name },
                'description': {'en-US': self.assignment.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
            }
        })

    def test_on_assignment_delete(self):
        on_assignment_delete.send(
            current_app._get_current_object(),
            event_name=on_assignment_delete.name,
            user=self.user,
            assignment=self.assignment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/delete',
            'display': {'en-US': 'deleted'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name },
                'description': {'en-US': self.assignment.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
            }
        })