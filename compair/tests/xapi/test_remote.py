import json
import mock
from six import text_type

from data.fixtures.test_data import SimpleAnswersTestData
from compair.tests.test_compair import ComPAIRXAPITestCase


from compair.core import db
from flask_login import current_app
from compair.xapi import XAPIStatement, XAPIVerb, XAPIObject, \
    XAPIContext, XAPIResult, XAPI
from tincan import LRSResponse

class RemoteXAPITests(ComPAIRXAPITestCase):

    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.app.config['LRS_STATEMENT_ENDPOINT'] = 'http://example.com'
        self.app.config['LRS_USERNAME'] = 'lrs_username'
        self.app.config['LRS_PASSWORD'] = 'lrs_password'
        self.app.config['LRS_USER_INPUT_FIELD_SIZE_LIMIT'] = 200 # 200 bytes

        self.data = SimpleAnswersTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]
        self.answer = self.data.create_answer(self.assignment, self.user)
        self.sent_statement = None
        self.character_limit = int(current_app.config.get('LRS_USER_INPUT_FIELD_SIZE_LIMIT') / len("c".encode('utf-8')))

    @mock.patch('tincan.RemoteLRS.save_statement')
    def test_send_remote_statement(self, mocked_save_statement):

        def save_statement_override(statement):
            self.sent_statement = json.loads(statement.to_json(XAPI._version))

            return LRSResponse(
                success=True,
                request=None,
                response=None,
                data=json.dumps(["123"]),
            )
        mocked_save_statement.side_effect = save_statement_override


        # test with answer normal content
        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.answer(self.answer),
            context=XAPIContext.answer(self.answer),
            result=XAPIResult.answer(self.answer, includeAttachment=True, success=True)
        )

        XAPI._send_lrs_statement(json.loads(statement.to_json(XAPI._version)))

        self._validate_and_cleanup_statement(self.sent_statement)

        self.assertEqual(self.sent_statement['actor'], self.get_compair_actor(self.user))
        self.assertEqual(self.sent_statement['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/submit',
            'display': {'en-US': 'submitted'}
        })
        self.assertEqual(self.sent_statement['object'], {
            'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
            'definition': {'type': 'http://id.tincanapi.com/activitytype/solution', 'name': {'en-US': 'Assignment answer'}},
            'objectType': 'Activity'
        })
        self.assertEqual(self.sent_statement['result'], {
            'extensions': {
                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
            },
            'response': self.answer.content,
            'success': True
        })
        self.assertEqual(self.sent_statement['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                },{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                }],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                    'objectType': 'Activity'
                }]
            }
        })

        # test with extremely long answer content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        content = "c" * (self.character_limit + 100)
        # expected_result_response should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_result_response = ("c" * self.character_limit) + " [TEXT TRIMMED]..."

        self.answer.content = content
        db.session.commit()

        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.answer(self.answer),
            context=XAPIContext.answer(self.answer),
            result=XAPIResult.answer(self.answer, includeAttachment=True, success=True)
        )

        XAPI._send_lrs_statement(json.loads(statement.to_json(XAPI._version)))

        self._validate_and_cleanup_statement(self.sent_statement)

        self.assertEqual(self.sent_statement['actor'], self.get_compair_actor(self.user))
        self.assertEqual(self.sent_statement['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/submit',
            'display': {'en-US': 'submitted'}
        })
        self.assertEqual(self.sent_statement['object'], {
            'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
            'definition': {'type': 'http://id.tincanapi.com/activitytype/solution', 'name': {'en-US': 'Assignment answer'}},
            'objectType': 'Activity'
        })
        self.assertEqual(self.sent_statement['result'], {
            'extensions': {
                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
            },
            'response': expected_result_response,
            'success': True
        })
        self.assertEqual(self.sent_statement['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                },{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                },],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                    'objectType': 'Activity'
                }]
            }
        })

        # test with assignment normal content
        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.assignment(self.assignment),
            context=XAPIContext.assignment(self.assignment)
        )

        XAPI._send_lrs_statement(json.loads(statement.to_json(XAPI._version)))

        self._validate_and_cleanup_statement(self.sent_statement)

        self.assertEqual(self.sent_statement['actor'], self.get_compair_actor(self.user))
        self.assertEqual(self.sent_statement['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(self.sent_statement['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name },
                'description': {'en-US': self.assignment.description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', self.sent_statement)
        self.assertEqual(self.sent_statement['context'], {
            'contextActivities': {
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
            }
        })

        # test with extremely long answer content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        name = "a" * (self.character_limit + 100)
        description = "b" * (self.character_limit + 100)
        # expected_result_response should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_object_name = ("a" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_object_description = ("b" * self.character_limit) + " [TEXT TRIMMED]..."

        self.assignment.name = name
        self.assignment.description = description
        db.session.commit()

        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.assignment(self.assignment),
            context=XAPIContext.assignment(self.assignment)
        )

        XAPI._send_lrs_statement(json.loads(statement.to_json(XAPI._version)))

        self._validate_and_cleanup_statement(self.sent_statement)

        self.assertEqual(self.sent_statement['actor'], self.get_compair_actor(self.user))
        self.assertEqual(self.sent_statement['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(self.sent_statement['object'], {
            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': expected_object_name },
                'description': {'en-US': expected_object_description }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', self.sent_statement)
        self.assertEqual(self.sent_statement['context'], {
            'contextActivities': {
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
            }
        })