# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
import mock

from compair import db
from data.factories import AnswerCommentFactory
from data.fixtures import DefaultFixture
from data.fixtures.test_data import TestFixture, LTITestData
from compair.models import PairingAlgorithm, AnswerCommentType
from compair.tests.test_compair import ComPAIRAPITestCase

class GradebookAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(GradebookAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=10, num_groups=5,
            num_group_assignments=1, with_comparisons=True)

        self.assignment = self.fixtures.assignment
        self.group_assignment = self.fixtures.assignments[1]

        self.base_url = self._build_url(self.fixtures.course.uuid, self.fixtures.assignment.uuid)

    def _build_url(self, course_uuid, assignment_uuid):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/gradebook'
        return url

    def test_get_gradebook(self):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            # Test login required
            rv = self.client.get(self.base_url, data=json.dumps({}))
            self.assert401(rv)

            with self.login(self.fixtures.unauthorized_instructor.username):
                rv = self.client.get(self.base_url, data=json.dumps({}))
                self.assert403(rv)

            for student in [self.fixtures.students[0], self.fixtures.unauthorized_student]:
                for user_context in [ \
                        self.login(student.username), \
                        self.impersonate(DefaultFixture.ROOT_USER, student)]:
                    with user_context:
                        rv = self.client.get(self.base_url, data=json.dumps({}))
                        self.assert403(rv)

            # authorized instructor
            with self.login(self.fixtures.instructor.username):
                # test invalid course id
                rv = self.client.get('/api/courses/999/assignments/'+assignment.uuid+'/gradebook', data=json.dumps({}), content_type='application/json')
                self.assert404(rv)

                # test invalid assignment id
                rv = self.client.get('/api/courses/'+self.fixtures.course.uuid+'/assignments/999/gradebook', data=json.dumps({}), content_type='application/json')
                self.assert404(rv)

                # get gradebook (with scores, no self eval)
                assignment.enable_self_evaluation = False
                assignment.pairing_algorithm = PairingAlgorithm.adaptive_min_delta
                db.session.commit()

                rv = self.client.get(self.base_url, data=json.dumps({}), content_type='application/json')
                self.assert200(rv)

                self.assertEqual(len(rv.json['gradebook']), len(self.fixtures.students))
                self.assertEqual(rv.json['total_comparisons_required'], assignment.total_comparisons_required)
                self.assertTrue(rv.json['include_scores'])
                self.assertFalse(rv.json['include_self_evaluation'])

                for gradebook in rv.json['gradebook']:
                    self.assertIn('user', gradebook)

                    student = next(student for student in self.fixtures.students if student.uuid == gradebook['user']['id'])
                    self.assertIsNotNone(student)

                    if not assignment.enable_group_answers:
                        answer = next(a for a in student.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                    else:
                        group = student.get_course_group(self.fixtures.course.id)
                        answer = next(a for a in group.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                    self.assertEqual(gradebook['num_answers'], 1 if answer else 0)

                    comparisons = [c for c in student.comparisons if c.assignment_id == assignment.id and c.completed]
                    self.assertEqual(gradebook['num_comparisons'], len(comparisons))

                    assignment_grade = next(ag for ag in student.assignment_grades if ag.assignment_id == assignment.id)
                    self.assertEqual(gradebook['grade'], assignment_grade.grade * 100)

                    if answer and answer.file:
                        self.assertEqual(gradebook['file']['id'], answer.file_id)
                    else:
                        self.assertIsNone(gradebook['file'])

                    if answer == None:
                        self.assertEqual(gradebook['score'], 'No Answer')
                    elif answer.score:
                        self.assertEqual(gradebook['score'], round(answer.score.normalized_score, 3))
                    else:
                        self.assertEqual(gradebook['score'], 'Not Evaluated')

                    self.assertNotIn('num_self_evaluation', gradebook)

                # get gradebook (with self eval, no scores)
                assignment.enable_self_evaluation = True
                assignment.pairing_algorithm = PairingAlgorithm.random
                first_student = self.fixtures.students[0]

                if not assignment.enable_group_answers:
                    answer = next(a for a in first_student.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                else:
                    group = first_student.get_course_group(self.fixtures.course.id)
                    answer = next(a for a in group.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                AnswerCommentFactory(
                    user=first_student,
                    answer=answer,
                    comment_type=AnswerCommentType.self_evaluation,
                )
                db.session.commit()

                rv = self.client.get(self.base_url, data=json.dumps({}), content_type='application/json')
                self.assert200(rv)

                self.assertEqual(len(rv.json['gradebook']), len(self.fixtures.students))
                self.assertEqual(rv.json['total_comparisons_required'], assignment.total_comparisons_required)
                self.assertFalse(rv.json['include_scores'])
                self.assertTrue(rv.json['include_self_evaluation'])

                for gradebook in rv.json['gradebook']:
                    self.assertIn('user', gradebook)

                    student = next(student for student in self.fixtures.students if student.uuid == gradebook['user']['id'])
                    self.assertIsNotNone(student)

                    if not assignment.enable_group_answers:
                        answer = next(a for a in student.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                    else:
                        group = student.get_course_group(self.fixtures.course.id)
                        answer = next(a for a in group.answers if a.assignment_id == assignment.id and a.active and not a.draft)
                    self.assertEqual(gradebook['num_answers'], 1 if answer else 0)

                    comparisons = [c for c in student.comparisons if c.assignment_id == assignment.id and c.completed]
                    self.assertEqual(gradebook['num_comparisons'], len(comparisons))

                    assignment_grade = next(ag for ag in student.assignment_grades if ag.assignment_id == assignment.id)
                    self.assertEqual(gradebook['grade'], assignment_grade.grade * 100)

                    if answer and answer.file:
                        self.assertEqual(gradebook['file']['id'], answer.file_id)
                    else:
                        self.assertIsNone(gradebook['file'])

                    self.assertNotIn('score', gradebook)

                    self_eval = next((
                        ac for ac in answer.comments if ac.user_id == student.id and \
                        ac.active and not ac.draft and ac.comment_type == AnswerCommentType.self_evaluation
                    ), None)
                    self.assertEqual(gradebook['num_self_evaluation'], 1 if self_eval else 0)
