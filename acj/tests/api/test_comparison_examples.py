import json
import datetime

from acj import db
from data.fixtures import AnswerFactory
from data.fixtures.test_data import TestFixture
from acj.models import Answer
from acj.tests.test_acj import ACJAPITestCase

class ComparionExampleAPITests(ACJAPITestCase):
    def setUp(self):
        super(ComparionExampleAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=2, with_draft_student=True)
        self.fixtures.add_comparison_example(self.fixtures.assignment, self.fixtures.instructor)
        self.fixtures.add_comparison_example(self.fixtures.assignment, self.fixtures.ta)
        self.base_url = self._build_url(self.fixtures.course.id, self.fixtures.assignment.id)

    def _build_url(self, course_id, assignment_id, tail=""):
        url = '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/comparisons/examples' + tail
        return url

    def test_get_all_comparison_examples(self):
        # Test login required
        rv = self.client.get(self.base_url)
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test non-existent entry
            rv = self.client.get(self._build_url(self.fixtures.course.id, 4903409))
            self.assert404(rv)
            rv = self.client.get(self._build_url(4903409, self.fixtures.assignment.id))
            self.assert404(rv)

            rv = self.client.get(self.base_url)
            self.assert200(rv)
            results = rv.json['objects']
            self.assertEqual(len(results), 2)
            comparison_examples = self.fixtures.assignment.comparison_examples
            for index, comparison_example in enumerate(comparison_examples):
                self.assertEqual(results[index]['id'], comparison_example.id)
                self.assertEqual(results[index]['answer1_id'], comparison_example.answer1_id)
                self.assertEqual(results[index]['answer2_id'], comparison_example.answer2_id)

        # ta
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            results = rv.json['objects']
            self.assertEqual(len(results), 2)
            comparison_examples = self.fixtures.assignment.comparison_examples
            for index, comparison_example in enumerate(comparison_examples):
                self.assertEqual(results[index]['id'], comparison_example.id)
                self.assertEqual(results[index]['answer1_id'], comparison_example.answer1_id)
                self.assertEqual(results[index]['answer2_id'], comparison_example.answer2_id)

    def test_create_comparison_example(self):
        self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.instructor)
        self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.ta)

        expected_comparison_example = {
            'answer1_id': self.fixtures.answers[-2].id,
            'answer2_id': self.fixtures.answers[-1].id
        }

        # test login required
        rv = self.client.post(
            self.base_url,
            data=json.dumps(expected_comparison_example),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
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

        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test non-existent entry
            rv = self.client.post(
                self._build_url(self.fixtures.course.id, 4903409),
                data=json.dumps(expected_comparison_example),
                content_type='application/json')
            self.assert404(rv)

            rv = self.client.post(
                self._build_url(4903409, self.fixtures.assignment.id),
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
            invalid_comparison_example['answer1_id'] = 999
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
            invalid_comparison_example['answer2_id'] = 999
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
            'id': comparison_example.id,
            'answer1_id': new_answer.id,
            'answer2_id': comparison_example.answer2_id,
        }

        # test login required
        rv = self.client.post(
            self.base_url + '/' + str(comparison_example.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        # instructor
        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post(
                self._build_url(999, self.fixtures.assignment.id, '/' + str(comparison_example.id)),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.fixtures.course.id, 999, '/' + str(comparison_example.id)),
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
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer1_id not exists
            invalid = expected.copy()
            invalid['answer1_id'] = 999
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert404(rv)

            # test invalid format - answer2_id
            invalid = expected.copy()
            invalid['answer2_id'] = None
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert400(rv)

            # test invalid format - answer2_id not exists
            invalid = expected.copy()
            invalid['answer2_id'] = 999
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
                data=json.dumps(invalid),
                content_type='application/json')
            self.assert404(rv)

            # test edit successful
            rv = self.client.post(
                self.base_url + '/' + str(comparison_example.id),
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
                self.base_url + '/' + str(comparison_example.id),
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
        rv = self.client.delete(self.base_url + '/' + str(comparison_example.id))
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(self.base_url + '/' + str(comparison_example.id))
            self.assert403(rv)

        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.delete(self.base_url + '/' + str(comparison_example.id))
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            rv = self.client.delete(self.base_url + '/' + str(comparison_example.id))
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
             # test invalid assignment id
            rv = self.client.delete(self._build_url(self.fixtures.course.id, 4903409) + '/' + str(comparison_example.id))
            self.assert404(rv)

             # test invalid course id
            rv = self.client.delete(self._build_url(4903409, self.fixtures.assignment.id) + '/' + str(comparison_example.id))
            self.assert404(rv)

            # test invalid comparison example id
            rv = self.client.delete(self.base_url + '/999')
            self.assert404(rv)

            # test deletion by instructor
            rv = self.client.delete(self.base_url + '/' + str(comparison_example.id))
            self.assert200(rv)
            self.assertEqual(comparison_example.id, rv.json['id'])

        # test deletion by ta
        with self.login(self.fixtures.instructor.username):
            rv = self.client.delete(self.base_url + '/' + str(comparison_example2.id))
            self.assert200(rv)
            self.assertEqual(comparison_example2.id, rv.json['id'])