import json

from data.fixtures.test_data import AssignmentCommentsTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_assignment_comment_create, \
    on_assignment_comment_modified, on_assignment_comment_delete

class AssignmentCommentXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = AssignmentCommentsTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]
        self.assignment_comment = self.data.create_assignment_comment(self.user, self.assignment)

    def test_on_assignment_comment_create(self):
        on_assignment_comment_create.send(
            current_app._get_current_object(),
            event_name=on_assignment_comment_create.name,
            user=self.user,
            assignment_comment=self.assignment_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://adlnet.gov/expapi/verbs/commented',
            'display': {'en-US': 'commented'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/comment/'+self.assignment_comment.uuid,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment comment'}},
            'objectType': 'Activity'
        })
        self.assertEqual(statements[0]['result'], {
            'extensions': {
                'http://xapi.analytics.ubc.ca/extension/character-count': len(self.assignment_comment.content),
                'http://xapi.analytics.ubc.ca/extension/word-count': len(self.assignment_comment.content.split(" "))
            },
            'response': self.assignment_comment.content
        })
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                }]
            }
        })



    def test_on_assignment_comment_modified(self):
        on_assignment_comment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_comment_modified.name,
            user=self.user,
            assignment_comment=self.assignment_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/comment/'+self.assignment_comment.uuid,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment comment'}},
            'objectType': 'Activity'
        })
        self.assertEqual(statements[0]['result'], {
            'extensions': {
                'http://xapi.analytics.ubc.ca/extension/character-count': len(self.assignment_comment.content),
                'http://xapi.analytics.ubc.ca/extension/word-count': len(self.assignment_comment.content.split(" "))
            },
            'response': self.assignment_comment.content
        })
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                }]
            }
        })

    def test_on_assignment_comment_delete(self):
        on_assignment_comment_delete.send(
            current_app._get_current_object(),
            event_name=on_assignment_comment_delete.name,
            user=self.user,
            assignment_comment=self.assignment_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/delete',
            'display': {'en-US': 'deleted'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/comment/'+self.assignment_comment.uuid,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment comment'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                }]
            }
        })