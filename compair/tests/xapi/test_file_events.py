import json

from data.fixtures.test_data import SimpleAssignmentTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from data.factories import AnswerFactory
from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_get_file

class FileXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.user = self.data.authorized_student
        self.assignment = self.data.assignments[0]

    def test_on_get_file(self):
        # not report or attachment
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="none",
            file_name="some_file"
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 0)

        # test report
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="report",
            file_name="some_report.csv"
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://id.tincanapi.com/verb/downloaded',
            'display': {'en-US': 'downloaded'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/report/some_report.csv',
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/file', 'name': {'en-US': 'Report'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])

        # test attachment without file record
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name="some_file"
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 0)

        # test attachment file record (not linked to assignments or answers)
        file_record = self.data.create_file(self.user)
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 0)

        # test attachment file record (assignment)
        self.assignment.file = file_record
        db.session.commit()

        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://id.tincanapi.com/verb/downloaded',
            'display': {'en-US': 'downloaded'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/attachment/'+file_record.name,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/file', 'name': {'en-US': 'Assignment attachment'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'parent': [
                    {'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid, 'objectType': 'Activity'}
                ],
                'grouping': [
                    {'id': 'https://localhost:8888/app/xapi/course/'+self.data.main_course.uuid, 'objectType': 'Activity'}
                ]
            }
        })

        # test attachment file record (answer)
        self.assignment.file = None
        answer = AnswerFactory(
            assignment=self.assignment,
            user=self.user,
            file=file_record
        )
        db.session.commit()

        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://id.tincanapi.com/verb/downloaded',
            'display': {'en-US': 'downloaded'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/attachment/'+file_record.name,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/file', 'name': {'en-US': 'Assignment answer attachment'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'parent': [
                    {'id': 'https://localhost:8888/app/xapi/answer/'+answer.uuid, 'objectType': 'Activity'}
                ],
                'grouping': [
                    {'id': 'https://localhost:8888/app/xapi/course/'+self.data.main_course.uuid, 'objectType': 'Activity'},
                    {'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid, 'objectType': 'Activity'},
                    {'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question', 'objectType': 'Activity'}
                ]
            }
        })