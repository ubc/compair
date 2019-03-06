# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import SimpleAnswersTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask_login import current_app

from compair.learning_records.capture_events import on_answer_modified, \
    on_answer_delete, on_answer_create

class AnswerLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
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

        self.expected_caliper_course = {
            'academicSession': self.course.term,
            'dateCreated': self.course.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.course.modified.replace(tzinfo=pytz.utc).isoformat(),
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'name': self.course.name,
            'type': 'CourseOffering',
            'extensions': {
                'ltiContexts': [{
                    'context_id': self.lti_context.context_id,
                    'oauth_consumer_key': self.lti_data.lti_consumer.oauth_consumer_key,
                    'lis_course_offering_sourcedid': "sis_course_id",
                    'lis_course_section_sourcedid': "sis_section_id",
                }]
            }
        }

        self.expected_caliper_assignment = {
            'name': self.assignment.name,
            'type': 'Assessment',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).isoformat(),
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).isoformat(),
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'isPartOf': self.expected_caliper_course,
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

        self.expected_caliper_assignment_question = {
            'name': self.assignment.name,
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).isoformat(),
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).isoformat(),
            'dateToSubmit': self.assignment.answer_end.replace(tzinfo=pytz.utc).isoformat(),
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'isPartOf': self.expected_caliper_assignment,
        }

        self.expected_caliper_answer_attempt = {
            'assignable': self.expected_caliper_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
            'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
            'type': 'Attempt'
        }

        self.expected_caliper_answer = {
            'attempt': self.expected_caliper_answer_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'type': 'Response',
            'dateCreated': self.answer.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.answer.modified.replace(tzinfo=pytz.utc).isoformat(),
            'extensions': {
                'characterCount': len(self.answer.content),
                'content': self.answer.content,
                'isDraft': False,
                'wordCount': 8,
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

        self.expected_xapi_course = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name}
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_sis_course = {
            'id': 'https://localhost:8888/course/'+self.lti_context.lis_course_offering_sourcedid,
            'objectType': 'Activity'
        }

        self.expected_xapi_sis_section = {
            'id': 'https://localhost:8888/course/'+self.lti_context.lis_course_offering_sourcedid+'/section/'+self.lti_context.lis_course_section_sourcedid,
            'objectType': 'Activity'
        }

        self.expected_xapi_assignment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_assignment_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
                        'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

    def test_on_answer_create(self):
        for draft in [True, False]:
            self.answer.draft = draft
            db.session.commit()

            self.expected_xapi_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_caliper_answer['extensions']['isDraft'] = draft
            self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).isoformat()

            # test without tracking
            on_answer_create.send(
                current_app._get_current_object(),
                event_name=on_answer_create.name,
                user=self.user,
                answer=self.answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment_question,
                'generated': self.expected_caliper_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment,
                'generated': {
                    'assignable': self.expected_caliper_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
                    'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }]

            self.assertEqual(len(events), len(expected_caliper_events))
            for index, expected_event in enumerate(expected_caliper_events):
                self.assertEqual(events[index], expected_event)


            statements = self.get_and_clear_xapi_statement_log()
            expected_xapi_statements = [{
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://adlnet.gov/expapi/verbs/completed',
                    'display': {'en-US': 'completed'}
                },
                "object": self.expected_xapi_answer,
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer_attempt],
                        'grouping': [self.expected_xapi_assignment, self.expected_xapi_course, self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                    }
                },
                "result": {
                    'success': True,
                    'duration': "PT05M00S",
                    'completion': not draft,
                    'response': self.answer.content,
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
                    }
                }
            }, {
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                },
                "object": {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/attempt',
                        'extensions': {
                            'http://id.tincanapi.com/extension/attempt': {
                                'duration': "PT05M00S",
                                'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
                                'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment],
                        'grouping': [self.expected_xapi_course, self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                    }
                },
                "result": {
                    'success': True,
                    'completion': not draft
                }
            }]

            self.assertEqual(len(statements), len(expected_xapi_statements))
            for index, expected_statement in enumerate(expected_xapi_statements):
                self.assertEqual(statements[index], expected_statement)

    def test_on_answer_modified(self):
        for draft in [True, False]:
            self.answer.draft = draft
            db.session.commit()

            self.expected_xapi_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_caliper_answer['extensions']['isDraft'] = draft
            self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).isoformat()

            # test without tracking
            on_answer_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_modified.name,
                user=self.user,
                answer=self.answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment_question,
                'generated': self.expected_caliper_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment,
                'generated': {
                    'assignable': self.expected_caliper_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
                    'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }]

            self.assertEqual(len(events), len(expected_caliper_events))
            for index, expected_event in enumerate(expected_caliper_events):
                self.assertEqual(events[index], expected_event)


            statements = self.get_and_clear_xapi_statement_log()
            expected_xapi_statements = [{
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://adlnet.gov/expapi/verbs/completed',
                    'display': {'en-US': 'completed'}
                },
                "object": self.expected_xapi_answer,
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer_attempt],
                        'grouping': [self.expected_xapi_assignment, self.expected_xapi_course, self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                    }
                },
                "result": {
                    'success': True,
                    'duration': "PT05M00S",
                    'completion': not draft,
                    'response': self.answer.content,
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
                    }
                }
            }, {
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                },
                "object": {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/attempt',
                        'extensions': {
                            'http://id.tincanapi.com/extension/attempt': {
                                'duration': "PT05M00S",
                                'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).isoformat(),
                                'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).isoformat(),
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment],
                        'grouping': [self.expected_xapi_course, self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                    }
                },
                "result": {
                    'success': True,
                    'completion': not draft
                }
            }]

            self.assertEqual(len(statements), len(expected_xapi_statements))
            for index, expected_statement in enumerate(expected_xapi_statements):
                self.assertEqual(statements[index], expected_statement)


    def test_on_answer_delete(self):
        # send delete
        on_answer_delete.send(
            current_app._get_current_object(),
            event_name=on_answer_delete.name,
            user=self.user,
            answer=self.answer
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Deleted',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': self.expected_caliper_answer,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/delete',
                'display': {'en-US': 'deleted'}
            },
            "object": self.expected_xapi_answer,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer_attempt],
                    'grouping': [self.expected_xapi_assignment, self.expected_xapi_course, self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            },
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)