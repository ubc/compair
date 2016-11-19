import json

from data.fixtures.test_data import ComparisonTestData, ComparisonFactory
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app
from compair.models import PairingAlgorithm

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

        self.example_comparisons = []
        self.comparisons = []
        for criterion in self.assignment.criteria:
            self.example_comparisons.append(ComparisonFactory(
                assignment=self.assignment,
                criterion=criterion,
                user=self.user,
                answer1_id=self.comparison_example.answer1.id,
                answer2_id=self.comparison_example.answer2.id,
                winner_id=self.comparison_example.answer1.id,
                completed=False
            ))

            self.comparisons.append(ComparisonFactory(
                assignment=self.assignment,
                criterion=criterion,
                user=self.user,
                answer1_id=self.answer1.id,
                answer2_id=self.answer2.id,
                winner_id=self.answer1.id,
                completed=False
            ))
        db.session.commit()

    def test_on_comparison_update(self):
        completed_count = 0

        for (is_comparison_example, comparisons) in [(True, self.example_comparisons), (False, self.comparisons)]:
            answer_uuids = [comparisons[0].answer1_uuid, comparisons[0].answer2_uuid]
            answer_uuids.sort()

            for completed in [False, True]:
                for comparison in comparisons:
                    comparison.completed = completed
                db.session.commit()
                if completed:
                    completed_count+=1

                # test without tracking
                on_comparison_update.send(
                    current_app._get_current_object(),
                    event_name=on_comparison_update.name,
                    user=self.user,
                    assignment=self.assignment,
                    comparisons=comparisons,
                    is_comparison_example=is_comparison_example
                )

                statements = self.get_and_clear_statement_log()
                if completed and not is_comparison_example:
                    self.assertEqual(len(statements), len(comparisons) + 1 + (2*len(comparisons)))
                else:
                    self.assertEqual(len(statements), len(comparisons) + 1)

                index = 0
                for comparison in comparisons:
                    self.assertEqual(statements[index]['actor'], self.get_compair_actor(self.user))
                    if completed:
                        self.assertEqual(statements[index]['verb'], {
                            'id': 'http://activitystrea.ms/schema/1.0/submit',
                            'display': {'en-US': 'submitted'}
                        })
                    else:
                        self.assertEqual(statements[index]['verb'], {
                            'id': 'http://xapi.ubc.ca/verb/draft',
                            'display': {'en-US': 'drafted'}
                        })
                    self.assertEqual(statements[index]['object'], {
                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                        'definition': {
                            'type': 'http://id.tincanapi.com/activitytype/solution',
                            'name': {'en-US': 'Assignment criteria comparison' }
                        },
                        'objectType': 'Activity'
                    })
                    if completed:
                        self.assertEqual(statements[index]['result'], {
                            'response': 'https://localhost:8888/app/xapi/answer/'+comparison.winner_uuid,
                            'success': True
                        })
                    else:
                        self.assertEqual(statements[index]['result'], {
                            'response': 'https://localhost:8888/app/xapi/answer/'+comparison.winner_uuid
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
                                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/comparison?pair='+answer_uuids[0]+','+answer_uuids[1],
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/criterion/'+comparison.criterion_uuid,
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
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/comparison?pair='+answer_uuids[0]+','+answer_uuids[1],
                    'definition': {
                        'type': 'http://adlnet.gov/expapi/activities/question',
                        'name': {'en-US': 'Assignment comparison #'+str(completed_count+1) },
                        'extensions': {
                            'http://xapi.ubc.ca/extension/comparison': completed_count+1,
                            'http://xapi.ubc.ca/extension/score-algorithm': PairingAlgorithm.random.value
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
                for comparison in comparisons:
                    grouping.append({
                        'id': 'https://localhost:8888/app/xapi/criterion/'+comparison.criterion_uuid,
                        'objectType': 'Activity'
                    })
                self.assertEqual(statements[index]['context'], {
                    'contextActivities': {
                        'grouping': grouping,
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparisons[0].answer1_uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+comparisons[0].answer2_uuid,
                            'objectType': 'Activity'
                        }]
                    }
                })
                index+=1

                if completed and not is_comparison_example:
                    for answer in [self.answer1, self.answer2]:
                        for score in answer.scores:
                            comparison = next(comparison for comparison in comparisons \
                                if comparison.criterion_id == score.criterion_id)

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
                                    'http://xapi.ubc.ca/extension/score-details': {
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
                                        'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                        'objectType': 'Activity'
                                    },{
                                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/comparison?pair='+answer_uuids[0]+','+answer_uuids[1],
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
                        comparisons=comparisons,
                        is_comparison_example=is_comparison_example
                    )

                    tracking_statements = self.get_and_clear_statement_log()
                    self.assertEqual(len(statements), len(tracking_statements))

                    index = 0
                    for comparison in comparisons:
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
                                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/comparison?pair='+answer_uuids[0]+','+answer_uuids[1],
                                    'objectType': 'Activity'
                                },{
                                    'id': 'https://localhost:8888/app/xapi/criterion/'+comparison.criterion_uuid,
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
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparisons[0].answer1_uuid,
                                'objectType': 'Activity'
                            },{
                                'id': 'https://localhost:8888/app/xapi/answer/'+comparisons[0].answer2_uuid,
                                'objectType': 'Activity'
                            }]
                        }
                    })
                    index+=1

                    if completed and not is_comparison_example:
                        for answer in [self.answer1, self.answer2]:
                            for score in answer.scores:
                                comparison = next(comparison for comparison in comparisons \
                                    if comparison.criterion_id == score.criterion_id)

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
                                            'id': 'https://localhost:8888/app/xapi/comparison/'+comparison.uuid,
                                            'objectType': 'Activity'
                                        },{
                                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/comparison?pair='+answer_uuids[0]+','+answer_uuids[1],
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