# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime

from compair import db
from data.fixtures import AnswerFactory, DefaultFixture
from data.fixtures.test_data import TestFixture
from compair.models import Answer
from compair.tests.test_compair import ComPAIRAPITestCase

class ComparionExampleAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(ComparionExampleAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=2, with_draft_student=True)
        self.fixtures.add_comparison_example(self.fixtures.assignment, self.fixtures.instructor)
        self.fixtures.add_comparison_example(self.fixtures.assignment, self.fixtures.ta)
        self.base_url = self._build_url(self.fixtures.course.uuid, self.fixtures.assignment.uuid)

    def _build_url(self, course_uuid, assignment_uuid, tail=""):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/comparisons/examples' + tail
        return url

    def test_get_all_comparison_examples(self):
        # Test login required
        rv = self.client.get(self.base_url)
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        for student in [self.fixtures.unauthorized_student, self.fixtures.students[0]]:
            for user_context in [ \
                    self.login(student.username), \
                    self.impersonate(DefaultFixture.ROOT_USER, student)]:
                with user_context:
                    rv = self.client.get(self.base_url)
                    self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test non-existent entry
            rv = self.client.get(self._build_url(self.fixtures.course.uuid, "4903409"))
            self.assert404(rv)
            rv = self.client.get(self._build_url("4903409", self.fixtures.assignment.uuid))
            self.assert404(rv)

            rv = self.client.get(self.base_url)
            self.assert200(rv)
            results = rv.json['objects']
            self.assertEqual(len(results), 2)
            comparison_examples = self.fixtures.assignment.comparison_examples
            for index, comparison_example in enumerate(comparison_examples):
                self.assertEqual(results[index]['id'], comparison_example.uuid)
                self.assertEqual(results[index]['answer1_id'], comparison_example.answer1_uuid)
                self.assertEqual(results[index]['answer2_id'], comparison_example.answer2_uuid)

        # ta
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            results = rv.json['objects']
            self.assertEqual(len(results), 2)
            comparison_examples = self.fixtures.assignment.comparison_examples
            for index, comparison_example in enumerate(comparison_examples):
                self.assertEqual(results[index]['id'], comparison_example.uuid)
                self.assertEqual(results[index]['answer1_id'], comparison_example.answer1_uuid)
                self.assertEqual(results[index]['answer2_id'], comparison_example.answer2_uuid)

    def test_create_comparison_example(self):
        self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.instructor)
        self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.ta)

        expected_comparison_example = {
            'answer1_id': self.fixtures.answers[-2].uuid,
            'answer2_id': self.fixtures.answers[-1].uuid
        }

        # test login required
        rv = self.client.post(
            self.base_url,
            data=json.dumps(expected_comparison_example),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized users
        student = self.fixtures.unauthorized_student
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(DefaultFixture.ROOT_USER, student)]:
            with user_context:
                rv = self.client.post(
                    self.base_url,
                    data=json.dumps(expected_comparison_example),
                    content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert403(rv)

        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(
                    self.base_url,
                    data=json.dumps(expected_comparison_example),
                    content_type='application/json')
                self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test non-existent entry
            rv = self.client.post(
                self._build_url(self.fixtures.course.uuid, "4903409"),
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert404(rv)

            rv = self.client.post(
                self._build_url("4903409", self.fixtures.assignment.uuid),
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert404(rv)

            # test invalid format - answer1_id
            invalid_comparison_example = expected_comparison_example.copy()
            invalid_comparison_example['answer1_id'] = None
            rv = self.client.post(
                self.base_url,
                data=json.dumps(invalid_comparison_example),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer1_id not exists
            invalid_comparison_example = expected_comparison_example.copy()
            invalid_comparison_example['answer1_id'] = "999"
            rv = self.client.post(
                self.base_url,
                data=json.dumps(invalid_comparison_example),
                content_type='application/json')
            self.assert404(rv)

            # test invalid format - answer2_id
            invalid_comparison_example = expected_comparison_example.copy()
            invalid_comparison_example['answer2_id'] = None
            rv = self.client.post(
                self.base_url,
                data=json.dumps(invalid_comparison_example),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer2_id not exists
            invalid_comparison_example = expected_comparison_example.copy()
            invalid_comparison_example['answer2_id'] = "999"
            rv = self.client.post(
                self.base_url,
                data=json.dumps(invalid_comparison_example),
                content_type='application/json')
            self.assert404(rv)

            # test create successful
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected_comparison_example['answer1_id'], rv.json['answer1_id'])
            self.assertEqual(expected_comparison_example['answer2_id'], rv.json['answer2_id'])

        # ta
        with self.login(self.fixtures.ta.username):
            # test create successful
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected_comparison_example['answer1_id'], rv.json['answer1_id'])
            self.assertEqual(expected_comparison_example['answer2_id'], rv.json['answer2_id'])

    def test_edit_comparison_example(self):
        comparison_example = self.fixtures.comparison_examples[0]
        self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.ta)
        new_answer = self.fixtures.answers[-1]

        expected = {
            'id': comparison_example.uuid,
            'answer1_id': new_answer.uuid,
            'answer2_id': comparison_example.answer2_uuid,
        }

        # test login required
        rv = self.client.post(
            self.base_url + '/' + comparison_example.uuid,
            data=json.dumps(expected),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        for student in [self.fixtures.unauthorized_student, self.fixtures.students[0]]:
            for user_context in [ \
                    self.login(student.username), \
                    self.impersonate(DefaultFixture.ROOT_USER, student)]:
                with user_context:
                    rv = self.client.post(
                        self.base_url + '/' + comparison_example.uuid,
                        data=json.dumps(expected),
                        content_type='application/json')
                    self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post(
                self._build_url("999", self.fixtures.assignment.uuid, '/' + comparison_example.uuid),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.fixtures.course.uuid, "999", '/' + comparison_example.uuid),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid comparison_example id
            rv = self.client.post(
                self.base_url + '/999',
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid format - answer1_id
            invalid = expected.copy()
            invalid['answer1_id'] = None
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer1_id not exists
            invalid = expected.copy()
            invalid['answer1_id'] = "999"
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert404(rv)

            # test invalid format - answer2_id
            invalid = expected.copy()
            invalid['answer2_id'] = None
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer2_id not exists
            invalid = expected.copy()
            invalid['answer2_id'] = "999"
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert404(rv)

            # test edit successful
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected['id'], rv.json['id'])
            self.assertEqual(expected['answer1_id'], rv.json['answer1_id'])
            self.assertEqual(expected['answer2_id'], rv.json['answer2_id'])

        # ta
        with self.login(self.fixtures.ta.username):
            # test edit successful
            rv = self.client.post(
                self.base_url + '/' + comparison_example.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected['id'], rv.json['id'])
            self.assertEqual(expected['answer1_id'], rv.json['answer1_id'])
            self.assertEqual(expected['answer2_id'], rv.json['answer2_id'])


    def test_delete_comparison_example(self):
        comparison_example = self.fixtures.comparison_examples[0]
        comparison_example2 = self.fixtures.comparison_examples[1]

        # test login required
        rv = self.client.delete(self.base_url + '/' + comparison_example.uuid)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(self.base_url + '/' + comparison_example.uuid)
            self.assert403(rv)

        for student in [self.fixtures.unauthorized_student, self.fixtures.students[0]]:
            for user_context in [ \
                    self.login(student.username), \
                    self.impersonate(DefaultFixture.ROOT_USER, student)]:
                with user_context:
                    rv = self.client.delete(self.base_url + '/' + comparison_example.uuid)
                    self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
             # test invalid assignment id
            rv = self.client.delete(self._build_url(self.fixtures.course.uuid, "4903409") + '/' + comparison_example.uuid)
            self.assert404(rv)

             # test invalid course id
            rv = self.client.delete(self._build_url("4903409", self.fixtures.assignment.uuid) + '/' + comparison_example.uuid)
            self.assert404(rv)

            # test invalid comparison example id
            rv = self.client.delete(self.base_url + '/999')
            self.assert404(rv)

            # test deletion by instructor
            rv = self.client.delete(self.base_url + '/' + comparison_example.uuid)
            self.assert200(rv)
            self.assertEqual(comparison_example.uuid, rv.json['id'])

        # test deletion by ta
        with self.login(self.fixtures.instructor.username):
            rv = self.client.delete(self.base_url + '/' + comparison_example2.uuid)
            self.assert200(rv)
            self.assertEqual(comparison_example2.uuid, rv.json['id'])