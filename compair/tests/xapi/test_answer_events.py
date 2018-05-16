# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from data.fixtures.test_data import SimpleAnswersTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_answer_modified, \
    on_answer_delete

class AnswerXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = SimpleAnswersTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]
        self.answer = self.data.create_answer(self.assignment, self.user)

    def test_on_answer_modified(self):
        for draft in [True, False]:
            self.answer.draft = draft
            db.session.commit()

            # test without tracking
            on_answer_modified.send(
                current_app._get_current_object(),
                event_name=on_answer_modified.name,
                user=self.user,
                assignment=self.assignment,
                answer=self.answer
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 2)

            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            if draft:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://xapi.learninganalytics.ubc.ca/verb/draft',
                    'display': {'en-US': 'drafted'}
                })
            else:
                self.assertEqual(statements[0]['verb'], {
                    'id': 'http://activitystrea.ms/schema/1.0/submit',
                    'display': {'en-US': 'submitted'}
                })
            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                'definition': {'type': 'http://id.tincanapi.com/activitytype/solution', 'name': {'en-US': 'Assignment answer'}},
                'objectType': 'Activity'
            })
            if draft:
                self.assertEqual(statements[0]['result'], {
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
                    },
                    'response': self.answer.content
                })
            else:
                self.assertEqual(statements[0]['result'], {
                    'extensions': {
                        'http://xapi.learninganalytics.ubc.ca/extension/character-count': len(self.answer.content),
                        'http://xapi.learninganalytics.ubc.ca/extension/word-count': len(self.answer.content.split(" "))
                    },
                    'response': self.answer.content,
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
                    },],
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
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
                'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                'definition': {
                    'type': 'http://adlnet.gov/expapi/activities/question',
                    'name': {'en-US': self.assignment.name },
                    'description': {'en-US': self.assignment.description}
                },
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
                    },],
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                        'objectType': 'Activity'
                    }]
                }
            })

            # test with tracking
            tracking = self.generate_tracking(with_duration=True)
            tracking_json = json.dumps({ 'tracking':  tracking })
            with self.app.test_request_context(content_type='application/json', method='POST',
                    content_length=len(tracking_json), data=tracking_json):
                on_answer_modified.send(
                    current_app._get_current_object(),
                    event_name=on_answer_modified.name,
                    user=self.user,
                    assignment=self.assignment,
                    answer=self.answer
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
                        },],
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
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
                        },],
                        'parent': [{
                            'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid,
                            'objectType': 'Activity'
                        }]
                    }
                })
                self.assertEqual(tracking_statements[1]['result'], {
                    'completion': not draft,
                    'duration': tracking.get('duration'),
                    'success': True
                })


    def test_on_answer_delete(self):
        for draft in [True, False]:
            self.answer.draft = draft
            db.session.commit()

            on_answer_delete.send(
                current_app._get_current_object(),
                event_name=on_answer_delete.name,
                user=self.user,
                answer=self.answer
            )

            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)

            self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
            self.assertEqual(statements[0]['verb'], {
                'id': 'http://activitystrea.ms/schema/1.0/delete',
                'display': {'en-US': 'deleted'}
            })
            self.assertEqual(statements[0]['object'], {
                'id': 'https://localhost:8888/app/xapi/answer/'+self.answer.uuid,
                'definition': {'type': 'http://id.tincanapi.com/activitytype/solution', 'name': {'en-US': 'Assignment answer'}},
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
                    },],
                    'parent': [{
                        'id': 'https://localhost:8888/app/xapi/assignment/'+self.assignment.uuid+'/question',
                        'objectType': 'Activity'
                    }]
                }
            })