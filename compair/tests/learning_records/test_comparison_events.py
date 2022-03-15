# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import ComparisonTestData, LTITestData, \
    ComparisonFactory, ComparisonCriterionFactory
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask import current_app
from compair.models import PairingAlgorithm, WinningAnswer

from compair.learning_records.capture_events import on_comparison_update

class ComparisonLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = ComparisonTestData()
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

        self.answer1 = self.data.answers[0]
        self.answer2 = self.data.answers[1]

        self.example_comparison = ComparisonFactory(
            assignment=self.assignment,
            user=self.user,
            answer1_id=self.answer1.id,
            answer2_id=self.answer2.id,
            winner=None,
            completed=False
        )
        self.example_comparison_criterion = ComparisonCriterionFactory(
            comparison=self.example_comparison,
            criterion=self.criterion,
            winner=WinningAnswer.answer1,
        )

        self.comparison = ComparisonFactory(
            assignment=self.assignment,
            user=self.user,
            answer1_id=self.answer1.id,
            answer2_id=self.answer2.id,
            winner=None,
            completed=False
        )
        self.comparison_criterion = ComparisonCriterionFactory(
            comparison=self.comparison,
            criterion=self.criterion,
            winner=WinningAnswer.answer1,
        )
        db.session.commit()

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

        self.expected_caliper_answer1_attempt = {
            'assignable': self.expected_caliper_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.answer1.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer1.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer1.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer1.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_answer1 = {
            'attempt': self.expected_caliper_answer1_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid,
            'type': 'Response',
            'dateCreated': self.answer1.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer1.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.answer1.content),
                'content': self.answer1.content,
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

        self.expected_caliper_answer2_attempt = {
            'assignable': self.expected_caliper_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.answer2.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer2.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer2.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer2.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_answer2 = {
            'attempt': self.expected_caliper_answer2_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer2.uuid,
            'type': 'Response',
            'dateCreated': self.answer2.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer2.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.answer2.content),
                'content': self.answer2.content,
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

        self.expected_caliper_comparison_question = {
            'name': "Assignment comparison #1",
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/1",
            'isPartOf': self.expected_caliper_assignment,
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

        self.expected_xapi_answer1_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer1.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.answer1.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.answer1.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer1 = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid,
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer2_attempt = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer2.attempt_uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/attempt',
                'extensions': {
                    'http://id.tincanapi.com/extension/attempt': {
                        'duration': "PT05M00S",
                        'startedAtTime': self.answer2.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': self.answer2.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    }
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer2 = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer2.uuid,
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_comparison_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/1",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': "Assignment comparison #1"}
            },
            'objectType': 'Activity'
        }

    def test_on_comparison_update(self):
        completed_count = 0

        for (is_comparison_example, comparison) in [(True, self.example_comparison), (False, self.comparison)]:
            for completed in [False, True]:
                comparison.completed = completed
                comparison.winner = WinningAnswer.answer1 if completed else None
                db.session.commit()

                on_comparison_update.send(
                    current_app._get_current_object(),
                    event_name=on_comparison_update.name,
                    user=self.user,
                    assignment=self.assignment,
                    comparison=comparison,
                    is_comparison_example=is_comparison_example
                )

                if completed:
                    completed_count += 1
                current_comparison = completed_count if completed else completed_count + 1
                self.expected_caliper_comparison_question['name'] = "Assignment comparison #"+str(current_comparison)
                self.expected_caliper_comparison_question['id'] = "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/"+str(current_comparison)
                self.expected_xapi_comparison_question['definition']['name']['en-US'] = "Assignment comparison #{}".format(current_comparison)
                self.expected_xapi_comparison_question['id'] = "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/"+str(current_comparison)

                expected_caliper_comparison_attempt = {
                    'assignable': self.expected_caliper_comparison_question,
                    'assignee': self.get_compair_caliper_actor(self.user),
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/"+str(current_comparison)+"/attempt/"+comparison.attempt_uuid,
                    'duration': "PT05M00S",
                    'startedAtTime': comparison.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'endedAtTime': comparison.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'type': 'Attempt'
                }

                expected_caliper_comparison = {
                    'attempt': expected_caliper_comparison_attempt,
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/"+comparison.uuid,
                    'type': 'Response',
                    'dateCreated': comparison.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'dateModified': comparison.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'extensions': {
                        'pairingAlgorithm': self.comparison.pairing_algorithm.value,
                        'winner': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid if completed else "Undecided",
                        'criteria': {
                            "https://localhost:8888/app/criterion/"+self.criterion.uuid: "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid,
                        },
                        "answers": [
                            "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid,
                            "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer2.uuid,
                        ],
                        "completed": completed
                    }
                }

                events = self.get_and_clear_caliper_event_log()
                expected_caliper_events = [{
                    'action': 'Completed',
                    'profile': 'AssessmentProfile',
                    'actor': self.get_compair_caliper_actor(self.user),
                    'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                    'object': self.expected_caliper_comparison_question,
                    'generated': expected_caliper_comparison,
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
                        'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comparison.attempt_uuid,
                        'duration': "PT05M00S",
                        'startedAtTime': comparison.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                        'endedAtTime': comparison.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
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

                if not is_comparison_example and completed:
                    expected_caliper_events.append({
                        'action': 'Ranked',
                        'profile': 'GeneralProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_answer1,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'Event'
                    })
                    expected_caliper_events.append({
                        'action': 'Ranked',
                        'profile': 'GeneralProfile',
                        'actor': self.get_compair_caliper_actor(self.user),
                        'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
                        'object': self.expected_caliper_answer2,
                        'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
                        'type': 'Event'
                    })

                self.assertEqual(len(events), len(expected_caliper_events))
                for index, expected_event in enumerate(expected_caliper_events):
                    self.assertEqual(events[index], expected_event)

                expected_xapi_comparison_attempt = {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/"+str(current_comparison)+"/attempt/"+comparison.attempt_uuid,
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/attempt',
                        'extensions': {
                            'http://id.tincanapi.com/extension/attempt': {
                                'duration': "PT05M00S",
                                'startedAtTime': comparison.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                'endedAtTime': comparison.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                            }
                        }
                    },
                    'objectType': 'Activity'
                }

                expected_xapi_comparison = {
                    'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/"+comparison.uuid,
                    'definition': {
                        'type': 'http://id.tincanapi.com/activitytype/solution',
                        'name': { 'en-US': "Assignment comparison" },
                        'extensions': {
                            'http://id.tincanapi.com/extension/completed': completed
                        }
                    },
                    'objectType': 'Activity'
                }


                statements = self.get_and_clear_xapi_statement_log()
                expected_xapi_statements = [{
                    "actor": self.get_compair_xapi_actor(self.user),
                    "verb": {
                        'id': 'http://adlnet.gov/expapi/verbs/completed',
                        'display': {'en-US': 'completed'}
                    },
                    "object": expected_xapi_comparison,
                    "context": {
                        'registration': comparison.attempt_uuid,
                        'contextActivities': {
                            'parent': [self.expected_xapi_comparison_question, self.expected_xapi_answer1, self.expected_xapi_answer2, expected_xapi_comparison_attempt],
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
                        'completion': completed,
                        'response': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid if completed else "Undecided",
                        'extensions': {
                            'http://xapi.learninganalytics.ubc.ca/extension/criteria': {
                                "https://localhost:8888/app/criterion/"+self.criterion.uuid: "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer1.uuid,
                            }
                        }
                    }
                }, {
                    "actor": self.get_compair_xapi_actor(self.user),
                    "verb": {
                        'id': 'http://activitystrea.ms/schema/1.0/submit',
                        'display': {'en-US': 'submitted'}
                    },
                    "object": {
                        'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/attempt/"+comparison.attempt_uuid,
                        'definition': {
                            'type': 'http://adlnet.gov/expapi/activities/attempt',
                            'extensions': {
                                'http://id.tincanapi.com/extension/attempt': {
                                    'duration': "PT05M00S",
                                    'startedAtTime': comparison.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                    'endedAtTime': comparison.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                                }
                            }
                        },
                        'objectType': 'Activity'
                    },
                    "context": {
                        'registration': comparison.attempt_uuid,
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
                        'completion': completed
                    }
                }]

                if not is_comparison_example and completed:
                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'https://w3id.org/xapi/dod-isd/verbs/ranked',
                            'display': {'en-US': 'ranked'}
                        },
                        "object": self.expected_xapi_answer1,
                        "context": {
                            'registration': comparison.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer1_attempt],
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
                            'score': {'raw': 5.0},
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/score-details': {
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
                                }
                            }
                        }
                    })
                    expected_xapi_statements.append({
                        "actor": self.get_compair_xapi_actor(self.user),
                        "verb": {
                            'id': 'https://w3id.org/xapi/dod-isd/verbs/ranked',
                            'display': {'en-US': 'ranked'}
                        },
                        "object": self.expected_xapi_answer2,
                        "context": {
                            'registration': comparison.attempt_uuid,
                            'contextActivities': {
                                'parent': [self.expected_xapi_assignment_question, self.expected_xapi_answer2_attempt],
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
                            'score': {'raw': 5.0},
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/score-details': {
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
                                }
                            }
                        }
                    })

                self.assertEqual(len(statements), len(expected_xapi_statements))
                for index, expected_statement in enumerate(expected_xapi_statements):
                    self.assertEqual(statements[index], expected_statement)
