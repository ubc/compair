# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import AnswerCommentsTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask import current_app
from compair.models import AnswerCommentType

from compair.learning_records.capture_events import on_answer_comment_create, \
    on_answer_comment_modified, on_answer_comment_delete

class AnswerCommentLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = AnswerCommentsTestData()
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

        self.self_evaluation_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.self_evaluation)
        self.evaluation_comment  = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.evaluation)
        self.public_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.public)
        self.private_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.private)

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

        self.expected_caliper_self_evaluation_question = {
            'name': "Assignment self-evaluation",
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/self-evaluation/question",
            'isPartOf': self.expected_caliper_assignment,
        }

        self.expected_caliper_self_evaluation_attempt = {
            'assignable': self.expected_caliper_self_evaluation_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/self-evaluation/question/attempt/"+self.self_evaluation_comment.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.self_evaluation_comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.self_evaluation_comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_self_evaluation_response = {
            'attempt': self.expected_caliper_self_evaluation_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.self_evaluation_comment.uuid+"/self-evaluation",
            'type': 'Response',
            'dateCreated': self.self_evaluation_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.self_evaluation_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.self_evaluation_comment.content),
                'content': self.self_evaluation_comment.content,
                'isDraft': False,
                'wordCount': 8,
            }
        }

        self.expected_caliper_evaluation_question = {
            'name': "Assignment Answer Evaluation #5",
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5",
            'isPartOf': self.expected_caliper_assignment,
        }

        self.expected_caliper_evaluation_attempt = {
            'assignable': self.expected_caliper_evaluation_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5/attempt/"+self.evaluation_comment.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.evaluation_comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.evaluation_comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_evaluation_response = {
            'attempt': self.expected_caliper_evaluation_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.evaluation_comment.uuid+"/evaluation",
            'type': 'Response',
            'dateCreated': self.evaluation_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.evaluation_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.evaluation_comment.content),
                'content': self.evaluation_comment.content,
                'isDraft': False,
                'wordCount': 8,
            }
        }


        self.expected_caliper_self_evaluation_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.self_evaluation_comment.uuid,
            'type': 'Comment',
            'commenter': self.get_compair_caliper_actor(self.user),
            'commentedOn': self.expected_caliper_answer,
            'value': self.self_evaluation_comment.content,
            'dateCreated': self.self_evaluation_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.self_evaluation_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.self_evaluation_comment.content),
                'type': AnswerCommentType.self_evaluation.value,
                'isDraft': False,
                'wordCount': 8,
            }
        }

        self.expected_caliper_evaluation_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.evaluation_comment.uuid,
            'type': 'Comment',
            'commenter': self.get_compair_caliper_actor(self.user),
            'commentedOn': self.expected_caliper_answer,
            'value': self.evaluation_comment.content,
            'dateCreated': self.evaluation_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.evaluation_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.evaluation_comment.content),
                'type': AnswerCommentType.evaluation.value,
                'isDraft': False,
                'wordCount': 8,
            }
        }

        self.expected_caliper_public_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.public_comment.uuid,
            'type': 'Comment',
            'commenter': self.get_compair_caliper_actor(self.user),
            'commentedOn': self.expected_caliper_answer,
            'value': self.public_comment.content,
            'dateCreated': self.public_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.public_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.public_comment.content),
                'type': AnswerCommentType.public.value,
                'isDraft': False,
                'wordCount': 8,
            }
        }

        self.expected_caliper_private_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.private_comment.uuid,
            'type': 'Comment',
            'commenter': self.get_compair_caliper_actor(self.user),
            'commentedOn': self.expected_caliper_answer,
            'value': self.private_comment.content,
            'dateCreated': self.private_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.private_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.private_comment.content),
                'type': AnswerCommentType.private.value,
                'isDraft': False,
                'wordCount': 8,
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

        self.expected_xapi_self_evaluation_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/self-evaluation/question/attempt/"+self.self_evaluation_comment.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'description': { 'en-US': self.self_evaluation_comment.content },
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.self_evaluation_comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.self_evaluation_comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_self_evaluation_response = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.self_evaluation_comment.uuid+"/self-evaluation",
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_self_evaluation_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/self-evaluation/question",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': "Assignment self-evaluation"},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_evaluation_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5/attempt/"+self.evaluation_comment.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'description': {'en-US': self.evaluation_comment.content},
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.evaluation_comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.evaluation_comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_evaluation_response = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.evaluation_comment.uuid+"/evaluation",
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'description': {'en-US': self.evaluation_comment.content},
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_evaluation_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': "Assignment Answer Evaluation #5"},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_self_evaluation_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.self_evaluation_comment.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/comment',
                'name': {'en-US': 'Assignment answer comment'},
                'extensions': {
                    'http://id.tincanapi.com/extension/type': AnswerCommentType.self_evaluation.value,
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_evaluation_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.evaluation_comment.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/comment',
                'name': {'en-US': 'Assignment answer comment'},
                'extensions': {
                    'http://id.tincanapi.com/extension/type': AnswerCommentType.evaluation.value,
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_public_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.public_comment.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/comment',
                'name': {'en-US': 'Assignment answer comment'},
                'extensions': {
                    'http://id.tincanapi.com/extension/type': AnswerCommentType.public.value,
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_private_comment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid+"/comment/"+self.private_comment.uuid,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/comment',
                'name': {'en-US': 'Assignment answer comment'},
                'extensions': {
                    'http://id.tincanapi.com/extension/type': AnswerCommentType.private.value,
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.comments = [
            (self.self_evaluation_comment, self.expected_caliper_self_evaluation_comment, self.expected_xapi_self_evaluation_comment),
            (self.evaluation_comment, self.expected_caliper_evaluation_comment, self.expected_xapi_evaluation_comment),
            (self.private_comment, self.expected_caliper_private_comment, self.expected_xapi_private_comment),
            (self.public_comment, self.expected_caliper_public_comment, self.expected_xapi_public_comment),
        ]

    def test_on_answer_comment_create(self):
        for (comment, caliper_object, xapi_object) in self.comments:
            for draft in [True, False]:
                comment.draft = draft
                db.session.commit()

                xapi_object['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                caliper_object['extensions']['isDraft'] = draft
                caliper_object['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                if comment.id == self.self_evaluation_comment.id:
                    self.expected_xapi_self_evaluation_response['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                    self.expected_caliper_self_evaluation_response['extensions']['isDraft'] = draft
                    self.expected_caliper_self_evaluation_response['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                elif comment.id == self.evaluation_comment.id:
                    self.expected_xapi_evaluation_response['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                    self.expected_caliper_evaluation_response['extensions']['isDraft'] = draft
                    self.expected_caliper_evaluation_response['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

                evaluation_number = 5 if comment.id == self.evaluation_comment.id else None

                # send create
                on_answer_comment_create.send(
                    current_app._get_current_object(),
                    event_name=on_answer_comment_create.name,
                    user=self.user,
                    answer_comment=comment,
                    evaluation_number=evaluation_number
                )

                if comment.id == self.self_evaluation_comment.id:
                    events = self.get_and_clear_caliper_event_log()
                    expected_caliper_events = []
                    if not draft:
                        expected_caliper_events.append({
                            'action': 'Commented',
                            'profile': 'FeedbackProfile',
                            'actor': self.get_compair_caliper_actor(self.user),
                            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                            'object': self.expected_caliper_answer,
                            'generated': caliper_object,
                            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                            'type': 'FeedbackEvent'
                        })
                    expected_caliper_events.append({
                        'action': 'Completed',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_self_evaluation_question,
                        'generated': self.expected_caliper_self_evaluation_response,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentItemEvent'
                    })
                    expected_caliper_events.append({
                        'action': 'Submitted',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_assignment,
                        'generated': {
                            'assignable': self.expected_caliper_assignment,
                            'assignee': self.get_compair_caliper_actor(self.user),
                            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comment.attempt_uuid,
                            'duration': "PT05M00S",
                            'startedAtTime': comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            'endedAtTime': comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            'type': 'Attempt'
                        },
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentEvent'
                    })
                    expected_caliper_events.append({
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
                    })
                    self.assertEqual(len(events), len(expected_caliper_events))
                    for index, expected_event in enumerate(expected_caliper_events):
                        self.assertEqual(events[index], expected_event)


                    statements = self.get_and_clear_xapi_statement_log()
                    expected_xapi_statements = []
                    if not draft:
                        expected_xapi_statements.append({
                            "actor": self.get_compair_xapi_actor(self.user),
                            "verb": {
                                'id': 'http://adlnet.gov/expapi/verbs/commented',
                                'display': {'en-US': 'commented'}
                            },
                            "object": xapi_object,
                            "context": {
                                'registration': comment.attempt_uuid,
                                'contextActivities': {
                                    'parent': [self.expected_xapi_answer],
                                    'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                                'response': comment.content,
                                'extensions': {
                                    'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                    'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                                }
                            }
                        })


                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://adlnet.gov/expapi/verbs/completed',
                            'display': {'en-US': 'completed'}
                        },
                        "object": self.expected_xapi_self_evaluation_response,
                        "context": {
                            'registration': comment.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_self_evaluation_question, self.expected_xapi_answer, self.expected_xapi_self_evaluation_attempt],
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    })
                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://activitystrea.ms/schema/1.0/submit',
                            'display': {'en-US': 'submitted'}
                        },
                        "object": {
                            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comment.attempt_uuid,
                            'definition': {
                                'type': 'http://adlnet.gov/expapi/activities/attempt',
                                'extensions': {
                                    'http://id.tincanapi.com/extension/attempt': {
                                        'duration': "PT05M00S",
                                        'startedAtTime': comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                        'endedAtTime': comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                    }
                                }
                            },
                            'objectType': 'Activity'
                        },
                        "context": {
                            'registration': comment.attempt_uuid,
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
                    })
                    self.assertEqual(len(statements), len(expected_xapi_statements))
                    for index, expected_statement in enumerate(expected_xapi_statements):
                        self.assertEqual(statements[index], expected_statement)

                elif comment.id == self.evaluation_comment.id:
                    events = self.get_and_clear_caliper_event_log()
                    expected_caliper_events = []
                    if not draft:
                        expected_caliper_events.append({
                            'action': 'Commented',
                            'profile': 'FeedbackProfile',
                            'actor': self.get_compair_caliper_actor(self.user),
                            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                            'object': self.expected_caliper_answer,
                            'generated': caliper_object,
                            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                            'type': 'FeedbackEvent'
                        })
                    expected_caliper_events.append({
                        'action': 'Completed',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_evaluation_question,
                        'generated': self.expected_caliper_evaluation_response,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentItemEvent'
                    })
                    self.assertEqual(len(events), len(expected_caliper_events))
                    for index, expected_event in enumerate(expected_caliper_events):
                        self.assertEqual(events[index], expected_event)


                    statements = self.get_and_clear_xapi_statement_log()
                    expected_xapi_statements = []
                    if not draft:
                        expected_xapi_statements.append({
                            "actor": self.get_compair_xapi_actor(self.user),
                            "verb": {
                                'id': 'http://adlnet.gov/expapi/verbs/commented',
                                'display': {'en-US': 'commented'}
                            },
                            "object": xapi_object,
                            "context": {
                                'registration': comment.attempt_uuid,
                                'contextActivities': {
                                    'parent': [self.expected_xapi_answer],
                                    'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                                'response': comment.content,
                                'extensions': {
                                    'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                    'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                                }
                            }
                        })


                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://adlnet.gov/expapi/verbs/completed',
                            'display': {'en-US': 'completed'}
                        },
                        "object": self.expected_xapi_evaluation_response,
                        "context": {
                            'registration': comment.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_evaluation_question, self.expected_xapi_answer, self.expected_xapi_evaluation_attempt],
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    })
                    self.assertEqual(len(statements), len(expected_xapi_statements))
                    for index, expected_statement in enumerate(expected_xapi_statements):
                        self.assertEqual(statements[index], expected_statement)

                elif comment.id in [self.public_comment.id, self.private_comment.id]:
                    expected_caliper_event = {
                        'action': 'Commented',
                        'profile': 'FeedbackProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_answer,
                        'generated': caliper_object,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'FeedbackEvent'
                    }
                    events = self.get_and_clear_caliper_event_log()
                    self.assertEqual(len(events), 1)
                    self.assertEqual(events[0], expected_caliper_event)

                    expected_xapi_statement = {
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://adlnet.gov/expapi/verbs/commented',
                            'display': {'en-US': 'commented'}
                        },
                        "object": xapi_object,
                        "context": {
                            'contextActivities': {
                                'parent': [self.expected_xapi_answer],
                                'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    }

                    statements = self.get_and_clear_xapi_statement_log()
                    self.assertEqual(len(statements), 1)
                    self.assertEqual(statements[0], expected_xapi_statement)

    def test_on_answer_comment_modified(self):
        commented_verb = {
            'id': 'http://adlnet.gov/expapi/verbs/commented',
            'display': {'en-US': 'commented'}
        }
        updated_verb = {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        }

        for (comment, caliper_object, xapi_object) in self.comments:
            for (draft, was_draft) in [(True, None), (False, True), (False, False)]:
                comment.draft = draft
                db.session.commit()

                xapi_object['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                caliper_object['extensions']['isDraft'] = draft
                caliper_object['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                if comment.id == self.self_evaluation_comment.id:
                    self.expected_xapi_self_evaluation_response['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                    self.expected_caliper_self_evaluation_response['extensions']['isDraft'] = draft
                    self.expected_caliper_self_evaluation_response['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                elif comment.id == self.evaluation_comment.id:
                    self.expected_xapi_evaluation_response['definition']['extensions']['http://id.tincanapi.com/extension/isDraft'] = draft
                    self.expected_caliper_evaluation_response['extensions']['isDraft'] = draft
                    self.expected_caliper_evaluation_response['dateModified'] = comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

                evaluation_number = 5 if comment.id == self.evaluation_comment.id else None

                # send modified
                on_answer_comment_modified.send(
                    current_app._get_current_object(),
                    event_name=on_answer_comment_create.name,
                    user=self.user,
                    answer_comment=comment,
                    evaluation_number=evaluation_number,
                    was_draft=was_draft
                )

                if comment.id == self.self_evaluation_comment.id:
                    events = self.get_and_clear_caliper_event_log()
                    expected_caliper_events = []
                    if not draft:
                        if was_draft:
                            expected_caliper_events.append({
                                'action': 'Commented',
                                'profile': 'FeedbackProfile',
                                'actor': self.get_compair_caliper_actor(self.user),
                                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                                'object': self.expected_caliper_answer,
                                'generated': caliper_object,
                                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                                'type': 'FeedbackEvent'
                            })
                        else:
                            expected_caliper_events.append({
                                'action': 'Modified',
                                'profile': 'GeneralProfile',
                                'actor': self.get_compair_caliper_actor(self.user),
                                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                                'object': caliper_object,
                                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                                'type': 'Event'
                            })
                    expected_caliper_events.append({
                        'action': 'Completed',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_self_evaluation_question,
                        'generated': self.expected_caliper_self_evaluation_response,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentItemEvent'
                    })
                    expected_caliper_events.append({
                        'action': 'Submitted',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_assignment,
                        'generated': {
                            'assignable': self.expected_caliper_assignment,
                            'assignee': self.get_compair_caliper_actor(self.user),
                            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comment.attempt_uuid,
                            'duration': "PT05M00S",
                            'startedAtTime': comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            'endedAtTime': comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            'type': 'Attempt'
                        },
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentEvent'
                    })
                    expected_caliper_events.append({
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
                    })
                    self.assertEqual(len(events), len(expected_caliper_events))
                    for index, expected_event in enumerate(expected_caliper_events):
                        self.assertEqual(events[index], expected_event)


                    statements = self.get_and_clear_xapi_statement_log()
                    expected_xapi_statements = []
                    if not draft:
                        expected_xapi_statements.append({
                            "actor": self.get_compair_xapi_actor(self.user),
                            "verb": commented_verb if was_draft else updated_verb,
                            "object": xapi_object,
                            "context": {
                                'registration': comment.attempt_uuid,
                                'contextActivities': {
                                    'parent': [self.expected_xapi_answer],
                                    'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                                'response': comment.content,
                                'extensions': {
                                    'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                    'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                                }
                            }
                        })


                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://adlnet.gov/expapi/verbs/completed',
                            'display': {'en-US': 'completed'}
                        },
                        "object": self.expected_xapi_self_evaluation_response,
                        "context": {
                            'registration': comment.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_self_evaluation_question, self.expected_xapi_answer, self.expected_xapi_self_evaluation_attempt],
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    })
                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://activitystrea.ms/schema/1.0/submit',
                            'display': {'en-US': 'submitted'}
                        },
                        "object": {
                            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comment.attempt_uuid,
                            'definition': {
                                'type': 'http://adlnet.gov/expapi/activities/attempt',
                                'extensions': {
                                    'http://id.tincanapi.com/extension/attempt': {
                                        'duration': "PT05M00S",
                                        'startedAtTime': comment.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                        'endedAtTime': comment.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                    }
                                }
                            },
                            'objectType': 'Activity'
                        },
                        "context": {
                            'registration': comment.attempt_uuid,
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
                    })
                    self.assertEqual(len(statements), len(expected_xapi_statements))
                    for index, expected_statement in enumerate(expected_xapi_statements):
                        self.assertEqual(statements[index], expected_statement)

                elif comment.id == self.evaluation_comment.id:
                    events = self.get_and_clear_caliper_event_log()
                    expected_caliper_events = []
                    if not draft:
                        if was_draft:
                            expected_caliper_events.append({
                                'action': 'Commented',
                                'profile': 'FeedbackProfile',
                                'actor': self.get_compair_caliper_actor(self.user),
                                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                                'object': self.expected_caliper_answer,
                                'generated': caliper_object,
                                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                                'type': 'FeedbackEvent'
                            })
                        else:
                            expected_caliper_events.append({
                                'action': 'Modified',
                                'profile': 'GeneralProfile',
                                'actor': self.get_compair_caliper_actor(self.user),
                                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                                'object': caliper_object,
                                'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                                'type': 'Event'
                            })
                    expected_caliper_events.append({
                        'action': 'Completed',
                        'profile': 'AssessmentProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_evaluation_question,
                        'generated': self.expected_caliper_evaluation_response,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'AssessmentItemEvent'
                    })
                    self.assertEqual(len(events), len(expected_caliper_events))
                    for index, expected_event in enumerate(expected_caliper_events):
                        self.assertEqual(events[index], expected_event)


                    statements = self.get_and_clear_xapi_statement_log()
                    expected_xapi_statements = []
                    if not draft:
                        expected_xapi_statements.append({
                            "actor": self.get_compair_xapi_actor(self.user),
                            "verb": commented_verb if was_draft else updated_verb,
                            "object": xapi_object,
                            "context": {
                                'registration': comment.attempt_uuid,
                                'contextActivities': {
                                    'parent': [self.expected_xapi_answer],
                                    'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                                'response': comment.content,
                                'extensions': {
                                    'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                    'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                                }
                            }
                        })


                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'http://adlnet.gov/expapi/verbs/completed',
                            'display': {'en-US': 'completed'}
                        },
                        "object": self.expected_xapi_evaluation_response,
                        "context": {
                            'registration': comment.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_evaluation_question, self.expected_xapi_answer, self.expected_xapi_evaluation_attempt],
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    })
                    self.assertEqual(len(statements), len(expected_xapi_statements))
                    for index, expected_statement in enumerate(expected_xapi_statements):
                        self.assertEqual(statements[index], expected_statement)

                elif comment.id in [self.public_comment.id, self.private_comment.id]:
                    expected_caliper_event = {
                        'action': 'Modified',
                        'profile': 'GeneralProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': caliper_object,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'Event'
                    }
                    events = self.get_and_clear_caliper_event_log()
                    self.assertEqual(len(events), 1)
                    self.assertEqual(events[0], expected_caliper_event)

                    expected_xapi_statement = {
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": updated_verb,
                        "object": xapi_object,
                        "context": {
                            'contextActivities': {
                                'parent': [self.expected_xapi_answer],
                                'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
                            'response': comment.content,
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(comment.content),
                                'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(comment.content.split(" "))
                            }
                        }
                    }

                    statements = self.get_and_clear_xapi_statement_log()
                    self.assertEqual(len(statements), 1)
                    self.assertEqual(statements[0], expected_xapi_statement)

    def test_on_answer_comment_delete(self):
        for (comment, caliper_object, xapi_object) in self.comments:
            # send delete
            on_answer_comment_delete.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_delete.name,
                user=self.user,
                answer_comment=comment
            )

            events = self.get_and_clear_caliper_event_log()
            expected_caliper_event = {
                'action': 'Archived',
                'profile': 'GeneralProfile',
                'actor': self.get_compair_caliper_actor(self.user),
                'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                'object': caliper_object,
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
                "object": xapi_object,
                "context": {
                    'contextActivities': {
                        'parent': [self.expected_xapi_answer],
                        'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
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
            }

            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0], expected_xapi_statement)
