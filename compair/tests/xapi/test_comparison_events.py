import json

from data.fixtures.test_data import ComparisonTestData, ComparisonFactory, ComparisonCriterionFactory
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app
from compair.models import PairingAlgorithm, WinningAnswer

from compair.xapi.capture_events import on_comparison_update

class ComparisonXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = ComparisonTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]

        self.answer1 = self.data.answers[0]
        self.answer2 = self.data.answers[1]
        self.comparison_example = self.data.comparisons_examples[0]

        self.example_comparison = ComparisonFactory(
            assignment=self.assignment,
            user=self.user,
            answer1_id=self.comparison_example.answer1.id,
            answer2_id=self.comparison_example.answer2.id,
            winner=None,
            completed=False
        )
        self.example_comparison_criteria = []

        self.comparison = ComparisonFactory(
            assignment=self.assignment,
            user=self.user,
            answer1_id=self.answer1.id,
            answer2_id=self.answer2.id,
            winner=None,
            completed=False
        )
        self.comparison_criteria = []

        for criterion in self.assignment.criteria:
            self.example_comparison_criteria.append(ComparisonCriterionFactory(
                comparison=self.example_comparison,
                criterion=criterion,
                winner=WinningAnswer.answer1,
            ))

            self.comparison_criteria.append(ComparisonCriterionFactory(
                comparison=self.comparison,
                criterion=criterion,
                winner=WinningAnswer.answer1,
            ))

        db.session.commit()

        self.maxDiff = None

    def test_on_comparison_update(self):
        completed_count = 0

        for (is_comparison_example, comparison) in [(True, self.example_comparison), (False, self.comparison)]:
            for completed in [False, True]:
                comparison.completed = completed
                comparison.winner = WinningAnswer.answer1 if completed else None
                db.session.commit()

                if completed:
                    completed_count+=1

                # test without tracking
                on_comparison_update.send(
                    current_app._get_current_object(),
                    event_name=on_comparison_update.name,
                    user=self.user,
                    assignment=self.assignment,
                    comparison=comparison,
                    is_comparison_example=is_comparison_example
                )

                statements = self.get_and_clear_statement_log()
                if completed and not is_comparison_example:
                    self.assertEqual(len(statements), len(self.example_comparison_criteria) + 1 + 1 + (2*(len(self.example_comparison_criteria) + 1)))
                else:
                    self.assertEqual(len(statements), len(self.example_comparison_criteria) + 1 + 1)

                index = 0

                self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                if completed:
                    self.assertEqual(statements[index]['verb'], {
                        'id': 'http://activitystrea.ms/schema/1.0/submit',
                        'display': {'en-US': 'submitted'}
                    })
                else:
                    self.assertEqual(statements[index]['verb'], {
                        'id': 'http://xapi.learninganalytics.ubc.ca/verb/draft',
                        'display': {'en-US': 'drafted'}
                    })
                self.assertEqual(statements[index]['object'], {
                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                    'definition': {
                        'type': 'http://id.tincanapi.com/activitytype/solution',
                        'name': {'en-US': 'Assignment comparison' }
                    },
                    'objectType': 'Activity'
                })
                if completed:
                    self.assertEqual(statements[index]['result'], {
                        'response': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                        'success': True
                    })
                else:
                    self.assertEqual(statements[index]['result'], {
                        'response': 'Undecided'
                    })
                self.assertEqual(statements[index]['context'], {
                    'contextActivities': {
                        'grouping': [{
                            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                            'objectType': 'Activity'
                        }],
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                            'objectType': 'Activity'
                        }]
                    }
                })

                index+=1

                for comparison_criterion in comparison.comparison_criteria:
                    self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                    if completed:
                        self.assertEqual(statements[index]['verb'], {
                            'id': 'http://activitystrea.ms/schema/1.0/submit',
                            'display': {'en-US': 'submitted'}
                        })
                    else:
                        self.assertEqual(statements[index]['verb'], {
                            'id': 'http://xapi.learninganalytics.ubc.ca/verb/draft',
                            'display': {'en-US': 'drafted'}
                        })
                    self.assertEqual(statements[index]['object'], {
                        'id': 'https://localhost:8888/app/xapi/comparison/criterion/'+comparison_criterion.uuid,
                        'definition': {
                            'type': 'http://id.tincanapi.com/activitytype/solution',
                            'name': {'en-US': 'Assignment criterion comparison' }
                        },
                        'objectType': 'Activity'
                    })
                    if completed:
                        self.assertEqual(statements[index]['result'], {
                            'response': 'https://localhost:8888/app/xapi/answer/'+comparison_criterion.answer1_uuid,
                            'success': True
                        })
                    else:
                        self.assertEqual(statements[index]['result'], {
                            'response': 'https://localhost:8888/app/xapi/answer/'+comparison_criterion.answer1_uuid
                        })
                    self.assertEqual(statements[index]['context'], {
                        'contextActivities': {
                            'grouping': [{
                                'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                'objectType': 'Activity'
                            }],
                            'parent': [{
                                'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/criterion/'+comparison_criterion.criterion_uuid,
                                'objectType': 'Activity'
                            }]
                        }
                    })

                    index+=1

                self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                if completed:
                    self.assertEqual(statements[index]['verb'], {
                        'id': 'http://adlnet.gov/expapi/verbs/completed',
                        'display': {'en-US': 'completed'}
                    })
                else:
                    self.assertEqual(statements[index]['verb'], {
                        'id': 'http://adlnet.gov/expapi/verbs/suspended',
                        'display': {'en-US': 'suspended'}
                    })
                self.assertEqual(statements[index]['object'], {
                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/question',
                        'name': {'en-US': 'Assignment comparison #'+str(completed_count+1) },
                        'extensions': {
                            'http://xapi.learninganalytics.ubc.ca/extension/comparison': completed_count+1,
                            'http://xapi.learninganalytics.ubc.ca/extension/score-algorithm': PairingAlgorithm.adaptive_min_delta.value
                        }
                    },
                    'objectType': 'Activity'
                })
                self.assertEqual(statements[index]['result'], {
                    'completion': completed,
                    'success': True
                })

                grouping = [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                }]
                for comparison_criterion in comparison.comparison_criteria:
                    grouping.append({
                        'id': 'https://localhost:8888/app/xapi/criterion/'+comparison_criterion.criterion_uuid,
                        'objectType': 'Activity'
                    })
                self.assertEqual(statements[index]['context'], {
                    'contextActivities': {
                        'grouping': grouping,
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                            'objectType': 'Activity'
                        }]
                    }
                })
                index+=1

                if completed and not is_comparison_example:
                    for answer in [self.answer1, self.answer2]:
                        score = answer.score

                        self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                        self.assertEqual(statements[index]['verb'], {
                            'id': 'http://www.tincanapi.co.uk/verbs/evaluated',
                            'display': {'en-US': 'evaluated'}
                        })
                        self.assertEqual(statements[index]['object'], {
                            'id': 'https://localhost:8888/app/xapi/answer/'+answer.uuid,
                            'definition': {
                                'type': 'http://id.tincanapi.com/activitytype/solution',
                                'name': {'en-US': 'Assignment answer' }
                            },
                            'objectType': 'Activity'
                        })
                        self.assertEqual(statements[index]['result'], {
                            'score': { 'raw': float(score.score) },
                            'extensions': {
                                'http://xapi.learninganalytics.ubc.ca/extension/score-details': {
                                    'algorithm': score.scoring_algorithm.value,
                                    'loses': score.loses,
                                    'opponents': score.opponents,
                                    'rounds': score.rounds,
                                    'wins': score.wins,
                                }
                            }
                        })
                        self.assertEqual(statements[index]['context'], {
                            'contextActivities': {
                                'grouping': [{
                                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                    'objectType': 'Activity'
                                }],
                                'other': [{
                                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                    'objectType': 'Activity'
                                }],
                                'parent': [{
                                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                                    'objectType': 'Activity'
                                }]
                            }
                        })
                        index+=1


                        for score in answer.criteria_scores:
                            comparison_criterion = next(comparison_criterion for comparison_criterion in comparison.comparison_criteria \
                                if comparison_criterion.criterion_id == score.criterion_id)

                            self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                            self.assertEqual(statements[index]['verb'], {
                                'id': 'http://www.tincanapi.co.uk/verbs/evaluated',
                                'display': {'en-US': 'evaluated'}
                            })
                            self.assertEqual(statements[index]['object'], {
                                'id': 'https://localhost:8888/app/xapi/answer/'+answer.uuid+'?criterion='+score.criterion_uuid,
                                'definition': {
                                    'type': 'http://id.tincanapi.com/activitytype/solution',
                                    'name': {'en-US': 'Assignment answer based on criterion' }
                                },
                                'objectType': 'Activity'
                            })
                            self.assertEqual(statements[index]['result'], {
                                'score': { 'raw': float(score.score) },
                                'extensions': {
                                    'http://xapi.learninganalytics.ubc.ca/extension/score-details': {
                                        'algorithm': score.scoring_algorithm.value,
                                        'loses': score.loses,
                                        'opponents': score.opponents,
                                        'rounds': score.rounds,
                                        'wins': score.wins,
                                    }
                                }
                            })
                            self.assertEqual(statements[index]['context'], {
                                'contextActivities': {
                                    'grouping': [{
                                        'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                                        'objectType': 'Activity'
                                    }],
                                    'other': [{
                                        'id': 'https://localhost:8888/app/xapi/comparison/criterion/'+comparison_criterion.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                        'objectType': 'Activity'
                                    }],
                                    'parent': [{
                                        'id': 'https://localhost:8888/app/xapi/answer/'+answer.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/criterion/'+score.criterion_uuid,
                                        'objectType': 'Activity'
                                    }]
                                }
                            })
                            index+=1


                # test with tracking
                tracking = self.generate_tracking(with_duration=True)
                tracking_json = json.dumps({ 'tracking':  tracking })
                with self.app.test_request_context(content_type='application/json', method='POST',
                        content_length=len(tracking_json), data=tracking_json):

                    on_comparison_update.send(
                        current_app._get_current_object(),
                        event_name=on_comparison_update.name,
                        user=self.user,
                        assignment=self.assignment,
                        comparison=comparison,
                        is_comparison_example=is_comparison_example
                    )

                    tracking_statements = self.get_and_clear_statement_log()
                    self.assertEqual(len(statements), len(tracking_statements))

                    index = 0

                    self.assertEqual(statements[index]['actor'], tracking_statements[index]['actor'])
                    self.assertEqual(statements[index]['verb'], tracking_statements[index]['verb'])
                    self.assertEqual(statements[index]['object'], tracking_statements[index]['object'])
                    self.assertEqual(statements[index]['result'], tracking_statements[index]['result'])
                    self.assertEqual(tracking_statements[index]['context'], {
                        'registration': tracking.get('registration'),
                        'contextActivities': {
                            'grouping': [{
                                'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                                'objectType': 'Activity'
                            }],
                            'parent': [{
                                'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                'objectType': 'Activity'
                            }]
                        }
                    })

                    index+=1

                    for comparison_criterion in comparison.comparison_criteria:
                        self.assertEqual(statements[index]['actor'], tracking_statements[index]['actor'])
                        self.assertEqual(statements[index]['verb'], tracking_statements[index]['verb'])
                        self.assertEqual(statements[index]['object'], tracking_statements[index]['object'])
                        self.assertEqual(statements[index]['result'], tracking_statements[index]['result'])
                        self.assertEqual(tracking_statements[index]['context'], {
                            'registration': tracking.get('registration'),
                            'contextActivities': {
                                'grouping': [{
                                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                    'objectType': 'Activity'
                                }],
                                'parent': [{
                                    'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/criterion/'+comparison_criterion.criterion_uuid,
                                    'objectType': 'Activity'
                                }]
                            }
                        })

                        index+=1

                    self.assertEqual(statements[index]['actor'], tracking_statements[index]['actor'])
                    self.assertEqual(statements[index]['verb'], tracking_statements[index]['verb'])
                    self.assertEqual(statements[index]['object'], tracking_statements[index]['object'])
                    self.assertEqual(tracking_statements[index]['result'], {
                        'completion': completed,
                        'duration': tracking.get('duration'),
                        'success': True
                    })
                    self.assertEqual(tracking_statements[index]['context'], {
                        'registration': tracking.get('registration'),
                        'contextActivities': {
                            'grouping': grouping,
                            'parent': [{
                                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer1_uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparison.answer2_uuid,
                                'objectType': 'Activity'
                            }]
                        }
                    })
                    index+=1

                    if completed and not is_comparison_example:
                        for answer in [self.answer1, self.answer2]:
                            self.assertEqual(statements[index]['actor'], tracking_statements[index]['actor'])
                            self.assertEqual(statements[index]['verb'], tracking_statements[index]['verb'])
                            self.assertEqual(statements[index]['object'], tracking_statements[index]['object'])
                            self.assertEqual(statements[index]['result'], tracking_statements[index]['result'])
                            self.assertEqual(tracking_statements[index]['context'], {
                                'registration': tracking.get('registration'),
                                'contextActivities': {
                                    'grouping': [{
                                        'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                        'objectType': 'Activity'
                                    }],
                                    'other': [{
                                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                        'objectType': 'Activity'
                                    }],
                                    'parent': [{
                                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                                        'objectType': 'Activity'
                                    }]
                                }
                            })
                            index+=1

                            for score in answer.criteria_scores:
                                comparison_criterion = next(comparison_criterion for comparison_criterion in comparison.comparison_criteria \
                                    if comparison_criterion.criterion_id == score.criterion_id)

                                self.assertEqual(statements[index]['actor'], tracking_statements[index]['actor'])
                                self.assertEqual(statements[index]['verb'], tracking_statements[index]['verb'])
                                self.assertEqual(statements[index]['object'], tracking_statements[index]['object'])
                                self.assertEqual(statements[index]['result'], tracking_statements[index]['result'])
                                self.assertEqual(tracking_statements[index]['context'], {
                                    'registration': tracking.get('registration'),
                                    'contextActivities': {
                                        'grouping': [{
                                            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                                            'objectType': 'Activity'
                                        }],
                                        'other': [{
                                            'id': 'https://localhost:8888/app/xapi/comparison/criterion/'+comparison_criterion.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid+'/question',
                                            'objectType': 'Activity'
                                        }],
                                        'parent': [{
                                            'id': 'https://localhost:8888/app/xapi/answer/'+answer.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/criterion/'+score.criterion_uuid,
                                            'objectType': 'Activity'
                                        }]
                                    }
                                })
                                index+=1