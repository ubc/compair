# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz
import mock
from six import text_type

from data.fixtures.test_data import SimpleAnswersTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from compair.models import AnswerCommentType
from flask import current_app
from compair.learning_records import XAPIStatement, XAPIVerb, XAPIObject, \
    XAPIContext, XAPIResult, XAPI, CaliperEntities, CaliperSensor, CaliperEvent
from tincan import LRSResponse
import caliper

class RemoteLearningRecordTests(ComPAIRLearningRecordTestCase):

    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.app.config['LRS_XAPI_STATEMENT_ENDPOINT'] = 'http://example.com/xapi'
        self.app.config['LRS_XAPI_USERNAME'] = 'lrs_username'
        self.app.config['LRS_XAPI_PASSWORD'] = 'lrs_password'
        self.app.config['LRS_CALIPER_HOST'] = 'http://example.com/caliper'
        self.app.config['LRS_CALIPER_API_KEY'] = 'lrs_api_key'
        self.app.config['LRS_USER_INPUT_FIELD_SIZE_LIMIT'] = 10000 # 10,000 characters

        self.data = SimpleAnswersTestData()
        self.lti_data = LTITestData()
        self.user = self.data.authorized_student
        self.setup_session_data(self.user)
        self.course = self.data.main_course
        self.lti_context = self.lti_data.create_context(
            self.lti_data.lti_consumer,
            compair_course_id=self.course.id,
            lis_course_offering_sourcedid="sis_course_id",
            lis_course_section_sourcedid="sis_section_id",
        )
        self.assignment = self.data.assignments[0]
        self.criterion = self.assignment.criteria[0]
        self.answer = self.data.create_answer(self.assignment, self.user)
        self.answer_comment = self.data.create_answer_comment(self.answer, self.user, AnswerCommentType.public)
        self.sent_xapi_statement = None
        self.sent_caliper_event = None
        self.character_limit = current_app.config.get('LRS_USER_INPUT_FIELD_SIZE_LIMIT')

    @mock.patch('caliper.sensor.Sensor.send')
    def test_send_remote_caliper_event(self, mocked_send_event):
        self.app.config['XAPI_ENABLED'] = False

        def send_event_override(event):
            self.sent_caliper_event = json.loads(event.as_json())
            self._del_empty_caliper_field(self.sent_caliper_event)
            return {}
        mocked_send_event.side_effect = send_event_override

        expected_assignment = {
            'name': self.assignment.name,
            'type': 'Assessment',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'isPartOf': {
                'academicSession': self.course.term,
                'dateCreated': self.course.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'dateModified': self.course.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'id': "https://localhost:8888/app/course/"+self.course.uuid,
                'name': self.course.name,
                'type': 'CourseOffering',
                'otherIdentifiers': [{
                    'identifier': self.lti_context.context_id,
                    'identifierType': 'LtiContextId',
                    'type': 'SystemIdentifier',
                    'extensions': {
                        'lis_course_offering_sourcedid': 'sis_course_id',
                        'lis_course_section_sourcedid': 'sis_section_id',
                        'oauth_consumer_key': self.lti_context.oauth_consumer_key,
                    },
                }],
            },
            'items': [{
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/4",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/6",
                'type': 'AssessmentItem'
            }],
        }

        expected_assignment_question = {
            'name': self.assignment.name,
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToSubmit': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'isPartOf': expected_assignment,
        }

        expected_attempt = {
            'assignable': expected_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        expected_answer = {
            'attempt': expected_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'type': 'Response',
            'dateCreated': self.answer.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.answer.content),
                'content': self.answer.content,
                'isDraft': False,
                'wordCount': len(self.answer.content.split(" ")),
                'scoreDetails': {
                    'algorithm': self.assignment.scoring_algorithm.value,
                    'loses': 0,
                    'opponents': 0,
                    'rounds': 0,
                    'score': 5,
                    'wins': 0,
                    'criteria': {
                        "https://localhost:8888/app/criterion/"+self.criterion.uuid: {
                            'loses': 0,
                            'opponents': 0,
                            'rounds': 0,
                            'score': 5,
                            'wins': 0
                        },
                    }
                },
            }
        }

        expected_answer_comment = {
            'commenter': self.get_compair_caliper_actor(self.user),
            'commentedOn': expected_answer,
            'value': self.answer_comment.content,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.answer_comment.uuid,
            'type': 'Comment',
            'dateCreated': self.answer_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.answer_comment.content),
                'isDraft': False,
                'type': 'Public',
                'wordCount': len(self.answer_comment.content.split(" ")),
            },
        }

        expected_event = {
            'action': 'Completed',
            'profile': 'AssessmentProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'generated': expected_answer,
            'object': expected_assignment_question,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'AssessmentItemEvent'
        }

        # test with answer normal content
        event = caliper.events.AssessmentItemEvent(
            action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
            profile=caliper.constants.CALIPER_PROFILES["ASSESSMENT"],
            object=CaliperEntities.assignment_question(self.answer.assignment),
            generated=CaliperEntities.answer(self.answer),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))
        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)
        self.assertEqual(self.sent_caliper_event, expected_event)

        # test with extremely long answer content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        content = "c" * (self.character_limit + 100)

        self.answer.content = content
        db.session.commit()

        # expected_answer content should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_answer['extensions']['content'] = ("c" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_answer['extensions']['wordCount'] = 1
        expected_answer['extensions']['characterCount'] = len(content)
        expected_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        event = caliper.events.AssessmentItemEvent(
            action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
            profile=caliper.constants.CALIPER_PROFILES["ASSESSMENT"],
            object=CaliperEntities.assignment_question(self.answer.assignment),
            generated=CaliperEntities.answer(self.answer),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))
        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)
        self.assertEqual(self.sent_caliper_event, expected_event)



        # test with answer comment normal content
        event = caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES["GENERAL"],
            object=CaliperEntities.answer_comment(self.answer_comment),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))

        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)

        expected_event = {
            'action': 'Modified',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': expected_answer_comment,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(self.sent_caliper_event, expected_event)

        # test with extremely long answer comment content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        content = "d" * (self.character_limit + 100)

        self.answer_comment.content = content
        db.session.commit()

        # expected_assignment name and description should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_answer_comment['value'] = ("d" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_answer_comment['extensions']['wordCount'] = 1
        expected_answer_comment['extensions']['characterCount'] = len(content)
        expected_answer_comment['dateModified'] = self.answer_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        event = caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES["GENERAL"],
            object=CaliperEntities.answer_comment(self.answer_comment),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))
        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)
        self.assertEqual(self.sent_caliper_event, expected_event)

        # test with assignment normal content
        event = caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES["GENERAL"],
            object=CaliperEntities.assignment(self.assignment),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))

        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)

        expected_event = {
            'action': 'Modified',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': expected_assignment,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(self.sent_caliper_event, expected_event)

        # test with extremely long assignment content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        name = "a" * (self.character_limit + 100)
        description = "b" * (self.character_limit + 100)

        self.assignment.name = name
        self.assignment.description = description
        db.session.commit()

        # expected_assignment name and description should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_assignment['name'] = ("a" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_assignment['description'] = ("b" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_assignment['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        event = caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES["GENERAL"],
            object=CaliperEntities.assignment(self.assignment),
            **CaliperEvent._defaults(self.user, self.course)
        )

        CaliperSensor._emit_to_lrs(json.loads(event.as_json()))

        self._validate_and_cleanup_caliper_event(self.sent_caliper_event)

        self.assertEqual(self.sent_caliper_event, expected_event)


    @mock.patch('tincan.RemoteLRS.save_statement')
    def test_send_remote_xapi_statement(self, mocked_save_statement):
        self.app.config['CALIPER_ENABLED'] = False

        def save_statement_override(statement):
            self.sent_xapi_statement = json.loads(statement.to_json(XAPI._version))

            return LRSResponse(
                success=True,
                request=None,
                response=None,
                data=json.dumps(["123"]),
            )
        mocked_save_statement.side_effect = save_statement_override

        expected_course = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name}
            },
            'objectType': 'Activity'
        }

        expected_assignment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

        expected_assignment_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

        expected_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        expected_answer = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        expected_answer_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.answer_comment.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/comment',
                'name': { 'en-US': "Assignment answer comment" },
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False,
                    'http://id.tincanapi.com/extension/type': self.answer_comment.comment_type.value
                }
            },
            'objectType': 'Activity'
        }

        expected_verb = {
            'id': 'http://activitystrea.ms/schema/1.0/submit',
            'display': {'en-US': 'submitted'}
        }

        expected_context = {
            'contextActivities': {
                'parent': [expected_assignment_question, expected_attempt],
                'grouping': [expected_assignment, expected_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_result = {
            'success': True,
            'response': self.answer.content,
            'extensions': {
                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
            }
        }

        expected_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_verb,
            "object": expected_answer,
            "context": expected_context,
            "result": expected_result
        }

        # test with answer normal content
        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.answer(self.answer),
            context=XAPIContext.answer(self.answer),
            result=XAPIResult.basic_content(self.answer.content, success=True)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)

        # test with extremely long answer content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        content = "c" * (self.character_limit + 100)
        self.answer.content = content
        db.session.commit()

        # expected_answer content should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_result['response'] = ("c" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_result['extensions']['http://xapi.learninganalytics.ubc.ca/extension/word-count'] = 1
        expected_result['extensions']['http://xapi.learninganalytics.ubc.ca/extension/character-count'] = len(content)

        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.answer(self.answer),
            context=XAPIContext.answer(self.answer),
            result=XAPIResult.basic_content(self.answer.content, success=True)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)

        expected_verb = {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        }

        expected_result = {
            'response': self.answer_comment.content,
            'extensions': {
                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer_comment.content),
                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer_comment.content.split(" "))
            }
        }

        expected_context = {
            'contextActivities': {
                'parent': [expected_answer],
                'grouping': [expected_assignment_question, expected_assignment, expected_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_verb,
            "object": expected_answer_comment,
            "context": expected_context,
            "result": expected_result
        }

        # test with answer comment normal content
        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.answer_comment(self.answer_comment),
            context=XAPIContext.answer_comment(self.answer_comment),
            result=XAPIResult.basic_content(self.answer_comment.content)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)


        # test with extremely long answer comment content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        content = "d" * (self.character_limit + 100)

        self.answer_comment.content = content
        db.session.commit()

        # expected_assignment name and description should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_result['response'] = ("d" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_result['extensions']['http://xapi.learninganalytics.ubc.ca/extension/word-count'] = 1
        expected_result['extensions']['http://xapi.learninganalytics.ubc.ca/extension/character-count'] = len(content)

        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.answer_comment(self.answer_comment),
            context=XAPIContext.answer_comment(self.answer_comment),
            result=XAPIResult.basic_content(self.answer_comment.content)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)

        expected_context = {
            'contextActivities': {
                'parent': [expected_course],
                'grouping': []
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_verb,
            "object": expected_assignment,
            "context": expected_context
        }

        # test with assignment normal content
        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.assignment(self.assignment),
            context=XAPIContext.assignment(self.assignment)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)

        # test with extremely long answer content

        # content should be ~ LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + 100 characters
        name = "a" * (self.character_limit + 100)
        description = "b" * (self.character_limit + 100)

        self.assignment.name = name
        self.assignment.description = description
        db.session.commit()

        # expected_assignment name and description should be <= LRS_USER_INPUT_FIELD_SIZE_LIMIT bytes long + " [TEXT TRIMMED]..."
        expected_assignment['definition']['name']['en-US'] = ("a" * self.character_limit) + " [TEXT TRIMMED]..."
        expected_assignment['definition']['description']['en-US'] = ("b" * self.character_limit) + " [TEXT TRIMMED]..."

        statement = XAPIStatement.generate(
            user=self.user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.assignment(self.assignment),
            context=XAPIContext.assignment(self.assignment)
        )

        XAPI._emit_to_lrs(json.loads(statement.to_json(XAPI._version)))
        self._validate_and_cleanup_xapi_statement(self.sent_xapi_statement)
        self.assertEqual(self.sent_xapi_statement, expected_statement)
