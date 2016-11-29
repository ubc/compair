import json

from data.fixtures.test_data import AnswerCommentsTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app
from compair.models import AnswerCommentType

from compair.xapi.capture_events import on_answer_comment_create, \
    on_answer_comment_modified, on_answer_comment_delete

class AnswerCommentXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = AnswerCommentsTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]
        self.answer = self.data.create_answer(self.assignment, self.user)

        self.self_evaluation_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.self_evaluation)
        self.evaluation_comment  = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.evaluation)
        self.public_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.public)
        self.private_comment = self.data.create_answer_comment(
            self.user, self.answer, comment_type=AnswerCommentType.private)

    def test_on_answer_comment_create(self):
        # test self_evaluation_comment
        on_answer_comment_create.send(
            current_app._get_current_object(),
            event_name=on_answer_comment_create.name,
            user=self.user,
            answer_comment=self.self_evaluation_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 0)

        # test evaluation_comment
        on_answer_comment_create.send(
            current_app._get_current_object(),
            event_name=on_answer_comment_create.name,
            user=self.user,
            answer_comment=self.evaluation_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 0)

        # test public_comment/private_comment
        for comment in [self.public_comment, self.private_comment]:
            on_answer_comment_create.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_create.name,
                user=self.user,
                answer_comment=comment
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            self.assertEqual(statements[0]['verb'], {
                'id': 'http://adlnet.gov/expapi/verbs/commented',
                'display': {'en-US': 'commented'}
            })
            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/comment/'+comment.uuid,
                'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment answer comment'}},
                'objectType': 'Activity'
            })
            self.assertEqual(statements[0]['result'], {
                'extensions': {
                    'http://xapi.ubc.ca/extension/character-count': len(comment.content),
                    'http://xapi.ubc.ca/extension/word-count': len(comment.content.split(" "))
                },
                'response': comment.content
            })
            self.assertEqual(statements[0]['context'], {
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
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })

    def test_on_answer_comment_modified(self):
        for draft in [True, False]:
            self.self_evaluation_comment.draft = draft
            db.session.commit()

            # test self_evaluation_comment without tracking
            on_answer_comment_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_modified.name,
                user=self.user,
                answer_comment=self.self_evaluation_comment
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 2)
            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))

            if draft:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://xapi.ubc.ca/verb/draft',
                    'display': {'en-US': 'drafted'}
                })
            else:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                })

            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/comment/'+self.self_evaluation_comment.uuid,
                'definition': {'type': 'http://activitystrea.ms/schema/1.0/review', 'name': {'en-US': 'Assignment self-evaluation review'}},
                'objectType': 'Activity'
            })
            if draft:
                self.assertEqual(statements[0]['result'], {
                    'extensions': {
                        'http://xapi.ubc.ca/extension/character-count': len(self.self_evaluation_comment.content),
                        'http://xapi.ubc.ca/extension/word-count': len(self.self_evaluation_comment.content.split(" "))
                    },
                    'response': self.self_evaluation_comment.content
                })
            else:
                self.assertEqual(statements[0]['result'], {
                    'extensions': {
                        'http://xapi.ubc.ca/extension/character-count': len(self.self_evaluation_comment.content),
                        'http://xapi.ubc.ca/extension/word-count': len(self.self_evaluation_comment.content.split(" "))
                    },
                    'response': self.self_evaluation_comment.content,
                    'success': True
                })

            self.assertEqual(statements[0]['context'], {
                'contextActivities': {
                    'grouping': [{
                        'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                        'objectType': 'Activity'
                    },{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                        'objectType': 'Activity'
                    },{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }],
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/self-evaluation',
                        'objectType': 'Activity'
                    }]
                }
            })

            self.assertEqual(statements[1]['actor'], self.get_compair_actor(self.user))
            if draft:
                self.assertEqual(statements[1]['verb'], {
                    'id': 'http://adlnet.gov/expapi/verbs/suspended',
                    'display': {'en-US': 'suspended'}
                })
            else:
                self.assertEqual(statements[1]['verb'], {
                    'id': 'http://adlnet.gov/expapi/verbs/completed',
                    'display': {'en-US': 'completed'}
                })

            self.assertEqual(statements[1]['object'], {
                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/self-evaluation',
                'definition': {'type': 'http://adlnet.gov/expapi/activities/question', 'name': {'en-US': 'Assignment self-evaluation'}},
                'objectType': 'Activity'
            })
            self.assertEqual(statements[1]['result'], {
                'completion': not draft,
                'success': True
            })
            self.assertEqual(statements[1]['context'], {
                'contextActivities': {
                    'grouping': [{
                        'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                        'objectType': 'Activity'
                    }],
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                        'objectType': 'Activity'
                    },{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })

            # test self_evaluation_comment with tracking
            tracking = self.generate_tracking(with_duration=True)
            tracking_json = json.dumps({ 'tracking':  tracking })
            with self.app.test_request_context(content_type='application/json', method='POST',
                    content_length=len(tracking_json), data=tracking_json):
                on_answer_comment_modified.send(
                    current_app._get_current_object(),
                    event_name=on_answer_comment_modified.name,
                    user=self.user,
                    answer_comment=self.self_evaluation_comment
                )

                tracking_statements = self.get_and_clear_statement_log()
                self.assertEqual(len(statements), 2)
                self.assertEqual(statements[0]['actor'], tracking_statements[0]['actor'])
                self.assertEqual(statements[0]['verb'], tracking_statements[0]['verb'])
                self.assertEqual(statements[0]['object'], tracking_statements[0]['object'])
                self.assertEqual(statements[0]['result'], tracking_statements[0]['result'])
                self.assertEqual(tracking_statements[0]['context'], {
                    'registration': tracking.get('registration'),
                    'contextActivities': {
                        'grouping': [{
                            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                            'objectType': 'Activity'
                        }],
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/self-evaluation',
                            'objectType': 'Activity'
                        }]
                    }
                })
                self.assertEqual(statements[1]['actor'], tracking_statements[1]['actor'])
                self.assertEqual(statements[1]['verb'], tracking_statements[1]['verb'])
                self.assertEqual(statements[1]['object'], tracking_statements[1]['object'])
                self.assertEqual(tracking_statements[1]['context'], {
                    'registration': tracking.get('registration'),
                    'contextActivities': {
                        'grouping': [{
                            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                            'objectType': 'Activity'
                        }],
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        },{
                            'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                            'objectType': 'Activity'
                        }]
                    }
                })
                self.assertEqual(tracking_statements[1]['result'], {
                    'completion': not draft,
                    'duration': tracking.get('duration'),
                    'success': True
                })

        for draft in [True, False]:
            self.evaluation_comment.draft = draft
            db.session.commit()

            # test evaluation_comment
            on_answer_comment_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_modified.name,
                user=self.user,
                answer_comment=self.evaluation_comment
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)

            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            if draft:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://xapi.ubc.ca/verb/draft',
                    'display': {'en-US': 'drafted'}
                })
            else:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://adlnet.gov/expapi/verbs/commented',
                    'display': {'en-US': 'commented'}
                })

            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/comment/'+self.evaluation_comment.uuid,
                'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment answer evaluation comment'}},
                'objectType': 'Activity'
            })
            self.assertEqual(statements[0]['result'], {
                'extensions': {
                    'http://xapi.ubc.ca/extension/character-count': len(self.evaluation_comment.content),
                    'http://xapi.ubc.ca/extension/word-count': len(self.evaluation_comment.content.split(" "))
                },
                'response': self.evaluation_comment.content
            })
            self.assertEqual(statements[0]['context'], {
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
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })

            # test evaluation_comment with tracking
            tracking = self.generate_tracking(with_duration=True)
            tracking_json = json.dumps({ 'tracking':  tracking })
            with self.app.test_request_context(content_type='application/json', method='POST',
                    content_length=len(tracking_json), data=tracking_json):
                on_answer_comment_modified.send(
                    current_app._get_current_object(),
                    event_name=on_answer_comment_modified.name,
                    user=self.user,
                    answer_comment=self.evaluation_comment
                )

                tracking_statements = self.get_and_clear_statement_log()
                self.assertEqual(len(statements), 1)
                self.assertEqual(statements[0]['actor'], tracking_statements[0]['actor'])
                self.assertEqual(statements[0]['verb'], tracking_statements[0]['verb'])
                self.assertEqual(statements[0]['object'], tracking_statements[0]['object'])
                self.assertEqual(statements[0]['result'], tracking_statements[0]['result'])
                self.assertEqual(tracking_statements[0]['context'], {
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
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                            'objectType': 'Activity'
                        }]
                    }
                })

        for comment in [self.public_comment, self.private_comment]:
            on_answer_comment_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_modified.name,
                user=self.user,
                answer_comment=comment
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            self.assertEqual(statements[0]['verb'], {
                'id': 'http://activitystrea.ms/schema/1.0/update',
                'display': {'en-US': 'updated'}
            })
            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/comment/'+comment.uuid,
                'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment answer comment'}},
                'objectType': 'Activity'
            })
            self.assertEqual(statements[0]['result'], {
                'extensions': {
                    'http://xapi.ubc.ca/extension/character-count': len(comment.content),
                    'http://xapi.ubc.ca/extension/word-count': len(comment.content.split(" "))
                },
                'response': comment.content
            })
            self.assertEqual(statements[0]['context'], {
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
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })

    def test_on_answer_comment_delete(self):
        # test self_evaluation_comment
        on_answer_comment_delete.send(
            current_app._get_current_object(),
            event_name=on_answer_comment_delete.name,
            user=self.user,
            answer_comment=self.self_evaluation_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/delete',
            'display': {'en-US': 'deleted'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/answer/comment/'+self.self_evaluation_comment.uuid,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/review', 'name': {'en-US': 'Assignment self-evaluation review'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
            'contextActivities': {
                'grouping': [{
                    'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
                    'objectType': 'Activity'
                },{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                    'objectType': 'Activity'
                },{
                    'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                    'objectType': 'Activity'
                }],
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/self-evaluation',
                    'objectType': 'Activity'
                }]
            }
        })

        # test evaluation_comment
        on_answer_comment_delete.send(
            current_app._get_current_object(),
            event_name=on_answer_comment_delete.name,
            user=self.user,
            answer_comment=self.evaluation_comment
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/delete',
            'display': {'en-US': 'deleted'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/answer/comment/'+self.evaluation_comment.uuid,
            'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment answer evaluation comment'}},
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertEqual(statements[0]['context'], {
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
                'parent': [{
                    'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                    'objectType': 'Activity'
                }]
            }
        })


        # test public_comment/private_comment
        for comment in [self.public_comment, self.private_comment]:
            on_answer_comment_delete.send(
                current_app._get_current_object(),
                event_name=on_answer_comment_delete.name,
                user=self.user,
                answer_comment=comment
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            self.assertEqual(statements[0]['verb'], {
                'id': 'http://activitystrea.ms/schema/1.0/delete',
                'display': {'en-US': 'deleted'}
            })
            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/comment/'+comment.uuid,
                'definition': {'type': 'http://activitystrea.ms/schema/1.0/comment', 'name': {'en-US': 'Assignment answer comment'}},
                'objectType': 'Activity'
            })
            self.assertNotIn('result', statements[0])
            self.assertEqual(statements[0]['context'], {
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
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })