# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import SimpleAnswersTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask import current_app

from compair.learning_records.capture_events import on_answer_modified, \
    on_answer_delete, on_answer_create

class AnswerLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.maxDiff = None
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

        self.group = self.data.create_group(self.course)
        self.data.change_group(self.course, self.user, self.group)
        self.group_assignment = self.data.assignments[2]
        self.group_criterion = self.group_assignment.criteria[0]
        self.group_answer = self.data.create_group_answer(self.group_assignment, self.group)

        self.expected_caliper_course = {
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
                    'oauth_consumer_key': self.lti_data.lti_consumer.oauth_consumer_key,
                },
            }]
        }

        self.expected_caliper_assignment = {
            'name': self.assignment.name,
            'type': 'Assessment',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
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
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToSubmit': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'isPartOf': self.expected_caliper_assignment,
        }

        self.expected_caliper_answer_attempt = {
            'assignable': self.expected_caliper_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_answer = {
            'attempt': self.expected_caliper_answer_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'type': 'Response',
            'dateCreated': self.answer.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
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

        self.expected_caliper_group = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/group/"+self.group.uuid,
            'type': 'Group',
            'name': self.group.name,
            'subOrganizationOf': "https://localhost:8888/app/course/"+self.course.uuid,
            'dateCreated': self.group.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.group.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'members': [
                self.get_compair_caliper_actor(self.user)
            ],
        }

        self.expected_caliper_group_assignment = {
            'name': self.group_assignment.name,
            'type': 'Assessment',
            'dateCreated': self.group_assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.group_assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.group_assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.group_assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid,
            'isPartOf': self.expected_caliper_course,
            'items': [{
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/question",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/comparison/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/comparison/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/4",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/comparison/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/5",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/evaluation/question/6",
                'type': 'AssessmentItem'
            }],
        }

        self.expected_caliper_group_assignment_question = {
            'name': self.group_assignment.name,
            'type': 'AssessmentItem',
            'dateCreated': self.group_assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.group_assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.group_assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToSubmit': self.group_assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.group_assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/question",
            'isPartOf': self.expected_caliper_group_assignment,
        }

        self.expected_caliper_group_answer_attempt = {
            'assignable': self.expected_caliper_group_assignment_question,
            #'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/question/attempt/"+self.group_answer.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt',
            'extensions': {
                'group': self.expected_caliper_group
            }
        }

        self.expected_caliper_group_answer = {
            'attempt': self.expected_caliper_group_answer_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/answer/"+self.group_answer.uuid,
            'type': 'Response',
            'dateCreated': self.group_answer.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.group_answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.group_answer.content),
                'content': self.group_answer.content,
                'isDraft': False,
                'wordCount': 8,
                'scoreDetails': {
                    'algorithm': self.group_assignment.scoring_algorithm.value,
                    'loses': 0,
                    'opponents': 0,
                    'rounds': 0,
                    'score': 5,
                    'wins': 0,
                    'criteria': {
                        "https://localhost:8888/app/criterion/"+self.group_criterion.uuid: {
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
                        'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
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

        self.expected_xapi_group = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/group/"+self.group.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/group',
                'name': {'en-US': self.group.name},
                'extensions': {
                    'http://id.tincanapi.com/extension/members': [
                        self.get_compair_xapi_actor(self.user),
                    ]
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_group_assignment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.group_assignment.name},
                'description': {'en-US': self.group_assignment.description},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_group_assignment_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/question",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.group_assignment.name},
                'description': {'en-US': self.group_assignment.description},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_group_answer_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/question/attempt/"+self.group_answer.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.group_answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.group_answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_group_answer = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/answer/"+self.group_answer.uuid,
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
            self.group_answer.draft = draft
            db.session.commit()

            self.expected_xapi_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_xapi_group_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_caliper_answer['extensions']['isDraft'] = draft
            self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            self.expected_caliper_group_answer['extensions']['isDraft'] = draft
            self.expected_caliper_group_answer['dateModified'] = self.group_answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            # test student without tracking
            on_answer_create.send(
                current_app._get_current_object(),
                event_name=on_answer_create.name,
                user=self.user,
                answer=self.answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment_question,
                'generated': self.expected_caliper_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment,
                'generated': {
                    'assignable': self.expected_caliper_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }, {
                'action': 'Used',
                'profile': 'ToolUseProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': {
                    'id': self.app_base_url.rstrip("/"),
                    'type': 'SoftwareApplication',
                    'name': 'ComPAIR',
                    'description': 'The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.',
                    'version': self.app.config.get('COMPAIR_VERSION', None)
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'ToolUseEvent'
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
                        'grouping': [self.expected_xapi_assignment, self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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
                                'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment],
                        'grouping': [self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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

            # test group without tracking
            on_answer_create.send(
                current_app._get_current_object(),
                event_name=on_answer_create.name,
                user=self.user,
                answer=self.group_answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_group_assignment_question,
                'generated': self.expected_caliper_group_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_group_assignment,
                'generated': {
                    'assignable': self.expected_caliper_group_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/attempt/"+self.group_answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.group_answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'endedAtTime': self.group_answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }, {
                'action': 'Used',
                'profile': 'ToolUseProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': {
                    'id': self.app_base_url.rstrip("/"),
                    'type': 'SoftwareApplication',
                    'name': 'ComPAIR',
                    'description': 'The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.',
                    'version': self.app.config.get('COMPAIR_VERSION', None)
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'ToolUseEvent'
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
                "object": self.expected_xapi_group_answer,
                "context": {
                    'registration': self.group_answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_group_assignment_question, self.expected_xapi_group_answer_attempt, self.expected_xapi_group],
                        'grouping': [self.expected_xapi_group_assignment, self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
                    }
                },
                "result": {
                    'success': True,
                    'duration': "PT05M00S",
                    'completion': not draft,
                    'response': self.group_answer.content,
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.group_answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.group_answer.content.split(" "))
                    }
                }
            }, {
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                },
                "object": {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/attempt/"+self.group_answer.attempt_uuid,
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/attempt',
                        'extensions': {
                            'http://id.tincanapi.com/extension/attempt': {
                                'duration': "PT05M00S",
                                'startedAtTime': self.group_answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                'endedAtTime': self.group_answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.group_answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_group_assignment],
                        'grouping': [self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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
            self.group_answer.draft = draft
            db.session.commit()

            self.expected_xapi_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_xapi_group_answer['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
            self.expected_caliper_answer['extensions']['isDraft'] = draft
            self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            self.expected_caliper_group_answer['extensions']['isDraft'] = draft
            self.expected_caliper_group_answer['dateModified'] = self.group_answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            # test student without tracking
            on_answer_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_modified.name,
                user=self.user,
                answer=self.answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment_question,
                'generated': self.expected_caliper_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_assignment,
                'generated': {
                    'assignable': self.expected_caliper_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+self.answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }, {
                'action': 'Used',
                'profile': 'ToolUseProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': {
                    'id': self.app_base_url.rstrip("/"),
                    'type': 'SoftwareApplication',
                    'name': 'ComPAIR',
                    'description': 'The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.',
                    'version': self.app.config.get('COMPAIR_VERSION', None)
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'ToolUseEvent'
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
                        'grouping': [self.expected_xapi_assignment, self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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
                                'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_assignment],
                        'grouping': [self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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

            # test group without tracking
            on_answer_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_modified.name,
                user=self.user,
                answer=self.group_answer
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_events = [{
                'action': 'Completed',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_group_assignment_question,
                'generated': self.expected_caliper_group_answer,
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentItemEvent'
            }, {
                'action': 'Submitted',
                'profile': 'AssessmentProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': self.expected_caliper_group_assignment,
                'generated': {
                    'assignable': self.expected_caliper_group_assignment,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/attempt/"+self.group_answer.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': self.group_answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'endedAtTime': self.group_answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'type': 'Attempt'
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'AssessmentEvent'
            }, {
                'action': 'Used',
                'profile': 'ToolUseProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': {
                    'id': self.app_base_url.rstrip("/"),
                    'type': 'SoftwareApplication',
                    'name': 'ComPAIR',
                    'description': 'The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.',
                    'version': self.app.config.get('COMPAIR_VERSION', None)
                },
                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                'type': 'ToolUseEvent'
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
                "object": self.expected_xapi_group_answer,
                "context": {
                    'registration': self.group_answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_group_assignment_question, self.expected_xapi_group_answer_attempt, self.expected_xapi_group],
                        'grouping': [self.expected_xapi_group_assignment, self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
                    }
                },
                "result": {
                    'success': True,
                    'duration': "PT05M00S",
                    'completion': not draft,
                    'response': self.group_answer.content,
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.group_answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.group_answer.content.split(" "))
                    }
                }
            }, {
                "actor": self.get_compair_xapi_actor(self.user),
                "verb": {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                },
                "object": {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.group_assignment.uuid+"/attempt/"+self.group_answer.attempt_uuid,
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/attempt',
                        'extensions': {
                            'http://id.tincanapi.com/extension/attempt': {
                                'duration': "PT05M00S",
                                'startedAtTime': self.group_answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                'endedAtTime': self.group_answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            }
                        }
                    },
                    'objectType': 'Activity'
                },
                "context": {
                    'registration': self.group_answer.attempt_uuid,
                    'contextActivities': {
                        'parent': [self.expected_xapi_group_assignment],
                        'grouping': [self.expected_xapi_course]
                    },
                    'extensions': {
                        'http://id.tincanapi.com/extension/browser-info': {},
                        'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                        'sis_courses': [{
                            'id': 'sis_course_id',
                            'section_ids': ['sis_section_id']
                        }]
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
            'action': 'Archived',
            'profile': 'GeneralProfile',
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
                'id': 'https://w3id.org/xapi/dod-isd/verbs/archived',
                'display': {'en-US': 'archived'}
            },
            "object": self.expected_xapi_answer,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer_attempt],
                    'grouping': [self.expected_xapi_assignment, self.expected_xapi_course]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                    'sis_courses': [{
                        'id': 'sis_course_id',
                        'section_ids': ['sis_section_id']
                    }]
                }
            },
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

        # group assignment

        on_answer_delete.send(
            current_app._get_current_object(),
            event_name=on_answer_delete.name,
            user=self.user,
            answer=self.group_answer
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Archived',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': self.expected_caliper_group_answer,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'https://w3id.org/xapi/dod-isd/verbs/archived',
                'display': {'en-US': 'archived'}
            },
            "object": self.expected_xapi_group_answer,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_group_assignment_question, self.expected_xapi_group_answer_attempt, self.expected_xapi_group],
                    'grouping': [self.expected_xapi_group_assignment, self.expected_xapi_course]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                    'sis_courses': [{
                        'id': 'sis_course_id',
                        'section_ids': ['sis_section_id']
                    }]
                }
            },
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)
