import datetime
import json

from data.fixtures.test_data import SimpleAssignmentTestData, ComparisonTestData, TestFixture
from acj.models import Assignment, Comparison, PairingAlgorithm
from acj.tests.test_acj import ACJAPITestCase
from acj.core import db


class AssignmentAPITests(ACJAPITestCase):
    def setUp(self):
        super(AssignmentAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.url = '/api/courses/' + str(self.data.get_course().id) + '/assignments'

    def test_get_single_assignment(self):
        assignment_expected = self.data.get_assignments()[0]
        assignment_api_url = self.url + '/' + str(assignment_expected.id)
        # Test login required
        rv = self.client.get(assignment_api_url)
        self.assert401(rv)
        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(assignment_api_url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(assignment_api_url)
            self.assert403(rv)

        # Test non-existent assignment
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self.url + '/939023')
            self.assert404(rv)
            # Test get actual assignment
            rv = self.client.get(assignment_api_url)
            self.assert200(rv)
            self._verify_assignment(assignment_expected, rv.json)

    def test_get_all_assignments(self):
        # Test login required
        rv = self.client.get(self.url)
        self.assert401(rv)
        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(self.url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(self.url)
            self.assert403(rv)
            # Test non-existent course
            rv = self.client.get('/api/courses/390484/assignments')
            self.assert404(rv)

        # Test receives all assignments
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self.url)
            for i, expected in enumerate(reversed(self.data.get_assignments())):
                actual = rv.json['objects'][i]
                self._verify_assignment(expected, actual)

    def test_create_assignment(self):
        now = datetime.datetime.utcnow()
        assignment_expected = {
            'name': 'this is a new assignment\'s name',
            'description': 'this is the new assignment\'s description.',
            'answer_start': now.isoformat() + 'Z',
            'answer_end': (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            'number_of_comparisons': 3,
            'students_can_reply': False,
            'enable_self_evaluation': False,
            'criteria': [
                { 'id': self.data.get_default_criterion().id }
            ],
            'pairing_algorithm': PairingAlgorithm.random.value
        }
        # Test login required
        rv = self.client.post(
            self.url,
            data=json.dumps(assignment_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):  # student post assignments not implemented
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # Test bad format
            rv = self.client.post(
                self.url,
                data=json.dumps({'name': 'blah'}),
                content_type='application/json')
            self.assert400(rv)
            # Test zero criteria
            bad_criteria = assignment_expected.copy()
            bad_criteria['criteria'] = []
            rv = self.client.post(
                self.url,
                data=json.dumps(bad_criteria),
                content_type='application/json')
            self.assert403(rv)
            # Test actual creation
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                assignment_expected['name'], rv.json['name'],
                "assignment create did not return the same name!")
            self.assertEqual(
                assignment_expected['description'], rv.json['description'],
                "assignment create did not return the same description!")
            self.assertEqual(assignment_expected['pairing_algorithm'], rv.json['pairing_algorithm'])
            # Test getting the assignment again
            rv = self.client.get(self.url + '/' + str(rv.json['id']))
            self.assert200(rv)
            self.assertEqual(
                assignment_expected['name'], rv.json['name'],
                "assignment create did not save name properly!")
            self.assertEqual(
                assignment_expected['description'], rv.json['description'],
                "assignment create did not save description properly!")
            self.assertEqual(assignment_expected['pairing_algorithm'], rv.json['pairing_algorithm'])

    def test_edit_assignment(self):
        assignment = self.data.get_assignments()[0]
        url = self.url + '/' + str(assignment.id)
        expected = {
            'id': assignment.id,
            'name': 'This is the new name.',
            'description': 'new_description',
            'answer_start': assignment.answer_start.isoformat() + 'Z',
            'answer_end': assignment.answer_end.isoformat() + 'Z',
            'number_of_comparisons': assignment.number_of_comparisons,
            'students_can_reply': assignment.students_can_reply,
            'enable_self_evaluation': assignment.enable_self_evaluation,
            'criteria': [
                { 'id': self.data.get_default_criterion().id }
            ],
            'pairing_algorithm': PairingAlgorithm.adaptive.value
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)


        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/assignments/' + str(assignment.id)
            rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self.url + '/999'
            rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # Test zero criteria
            bad_criteria = expected.copy()
            bad_criteria['criteria'] = []
            rv = self.client.post(url, data=json.dumps(bad_criteria), content_type='application/json')
            self.assert403(rv)

            # test edit by author
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

            # test edit by author add & remove criteria
            new_criterion = self.data.create_criterion(self.data.get_authorized_instructor())
            add_criteria = expected.copy()
            add_criteria['criteria'] = [{ 'id': new_criterion.id }]
            rv = self.client.post(url, data=json.dumps(add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

        with self.login(self.data.get_authorized_ta().username):
            # test edit by user who can manage posts (TA)
            ta_expected = {
                'id': assignment.id,
                'name': 'Another name',
                'description': 'new_description',
                'answer_start': assignment.answer_start.isoformat() + 'Z',
                'answer_end': assignment.answer_end.isoformat() + 'Z',
                'number_of_comparisons': assignment.number_of_comparisons,
                'students_can_reply': assignment.students_can_reply,
                'enable_self_evaluation': assignment.enable_self_evaluation,
                'criteria': [
                    { 'id': self.data.get_default_criterion().id }
                ],
                'pairing_algorithm': PairingAlgorithm.adaptive.value
            }
            rv = self.client.post(url, data=json.dumps(ta_expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(ta_expected['name'], rv.json['name'])
            self.assertEqual(ta_expected['description'], rv.json['description'])

            # test edit by TA add & remove criteria
            ta_new_criterion = self.data.create_criterion(self.data.get_authorized_ta())
            ta_add_criteria = ta_expected.copy()
            ta_add_criteria['criteria'] = [{ 'id': ta_new_criterion.id }]
            rv = self.client.post(url, data=json.dumps(ta_add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

    def test_delete_assignment(self):
        # Test deleting the assignment
        assignment_id = Assignment.query.first().id
        expected_ret = {'id': assignment_id}
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.delete(self.url + '/' + str(assignment_id))
            self.assert403(rv)
            self.assertEqual(
                '<p>' + self.data.get_authorized_student().username + ' does not have delete access to assignment 1</p>',
                rv.json['message'])

        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(self.url + '/' + str(assignment_id))
            self.assert200(rv)
            self.assertEqual(expected_ret['id'], rv.json['id'], "assignment " + str(rv.json['id']) + " deleted successfully")

    def _verify_assignment(self, expected, actual):
        self.assertEqual(expected.name, actual['name'])
        self.assertEqual(expected.description, actual['description'])
        self.assertEqual(expected.user_id, actual['user_id'])
        self.assertEqual(expected.pairing_algorithm.value, actual['pairing_algorithm'])

class AssignmentStatusComparisonsAPITests(ACJAPITestCase):
    def setUp(self):
        super(AssignmentStatusComparisonsAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.url = '/api/courses/' + str(self.data.get_course().id) + '/assignments'
        self.assignment = self.data.get_assignments()[0]

    def _submit_all_possible_comparisons_for_user(self, user_id):
        submit_count = 0

        for comparison_example in self.data.comparisons_examples:
            if comparison_example.assignment_id == self.assignment.id:
                comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id)
                self.assertEqual(comparisons[0].answer1_id, comparison_example.answer1_id)
                self.assertEqual(comparisons[0].answer2_id, comparison_example.answer2_id)
                for comparison in comparisons:
                    comparison.completed = True
                    comparison.winner_id = min([comparisons[0].answer1_id, comparisons[0].answer2_id])
                    db.session.add(comparison)
                submit_count += 1
                db.session.commit()

        # self.login(username)
        # calculate number of comparisons to do before user has compared all the pairs it can
        num_eligible_answers = 0  # need to minus one to exclude the logged in user's own answer
        for answer in self.data.get_student_answers():
            if answer.assignment_id == self.assignment.id and answer.user_id != user_id:
                num_eligible_answers += 1
        # n - 1 possible pairs before all answers have been compared
        num_possible_comparisons = num_eligible_answers - 1
        for i in range(num_possible_comparisons):
            comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id)
            for comparison in comparisons:
                comparison.completed = True
                comparison.winner_id = min([comparisons[0].answer1_id, comparisons[0].answer2_id])
                db.session.add(comparison)
            submit_count += 1
            db.session.commit()

            Comparison.calculate_scores(self.assignment.id)
        return submit_count

    def test_get_all_status(self):
        url = self.url + '/status'
        assignments = self.data.get_assignments()

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid input
        with self.login(self.data.get_authorized_student().username):
            # test invalid course id
            invalid_url = '/api/courses/999/assignments/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)

            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 2)
                elif assignments[1].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 2)
                else:
                    self.assertFalse(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

        with self.login(self.data.get_authorized_student().username):
            # test authorized student - when haven't compared
            rv = self.client.get(url)
            self.assert200(rv)
            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 1)
                elif assignments[1].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 1)
                else:
                    self.assertFalse(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

            compare_count_result = self._submit_all_possible_comparisons_for_user(self.data.get_authorized_student().id)

            # test authorized student - when have compared all
            rv = self.client.get(url)
            self.assert200(rv)
            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertFalse(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], compare_count_result)
                    self.assertEqual(status['comparisons']['left'],
                        assignment.total_comparisons_required - compare_count_result)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 1)
                elif assignments[1].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 1)
                else:
                    self.assertFalse(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

            # test self evaluation enabled
            for assignment in assignments:
                assignment.enable_self_evauluation = True
            db.session.commit()

    def test_get_status(self):
        url = self.url + '/' + str(self.assignment.id) + '/status'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_student().username):
            invalid_url = '/api/courses/999/assignments/'+str(self.assignment.id)+'/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = '/api/courses/'+str(self.data.get_course().id)+'/assignments/999/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.assignment.total_comparisons_required)
            self.assertTrue(status['comparisons']['available'])
            self.assertTrue(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 2)

        with self.login(self.data.get_authorized_student().username):
            # test authorized student - when haven't compared
            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.assignment.total_comparisons_required)
            self.assertTrue(status['comparisons']['available'])
            self.assertTrue(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 1)

            compare_count_result = self._submit_all_possible_comparisons_for_user(self.data.get_authorized_student().id)
            # test authorized student - when have compared all
            self.login(self.data.get_authorized_student().username)
            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertEqual(status['comparisons']['count'], compare_count_result)
            self.assertEqual(status['comparisons']['left'],
                self.assignment.total_comparisons_required - compare_count_result)
            self.assertFalse(status['comparisons']['available'])
            self.assertTrue(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 1)

class AssignmentStatusAnswersAPITests(ACJAPITestCase):
    def setUp(self):
        super(AssignmentStatusAnswersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_assignments=2, num_groups=2)
        self.url = '/api/courses/' + str(self.fixtures.course.id) + '/assignments'

    def test_get_all_status(self):
        url = self.url + '/status'
        assignments = self.fixtures.assignments

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid input
        with self.login(self.fixtures.students[0].username):
            # test invalid course id
            invalid_url = '/api/courses/999/assignments/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

        with self.login(self.fixtures.instructor.username):
            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)

            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)
                else:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

            # test authorized instructor - multiple answers
            self.fixtures.add_answer(assignments[0], self.fixtures.instructor)
            self.fixtures.add_answer(assignments[0], self.fixtures.instructor)
            self.fixtures.add_answer(assignments[0], self.fixtures.instructor)

            rv = self.client.get(url)
            self.assert200(rv)

            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 3)
                else:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

        self.fixtures.add_students(1)
        with self.login(self.fixtures.students[-1].username):
            # test authorized student - no answers
            rv = self.client.get(url)
            self.assert200(rv)
            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)
                else:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

            # test authorized student - answered
            self.fixtures.add_answer(assignments[0], self.fixtures.students[-1])

            rv = self.client.get(url)
            self.assert200(rv)
            for assignment in assignments:
                self.assertTrue(str(assignment.id) in rv.json['statuses'])
                status = rv.json['statuses'][str(assignment.id)]
                if assignments[0].id == assignment.id:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertTrue(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 1)
                else:
                    self.assertTrue(status['comparisons']['available'])
                    self.assertEqual(status['comparisons']['count'], 0)
                    self.assertEqual(status['comparisons']['left'], assignment.total_comparisons_required)
                    self.assertFalse(status['answers']['answered'])
                    self.assertEqual(status['answers']['count'], 0)

    def test_get_status(self):
        url = self.url + '/' + str(self.fixtures.assignment.id) + '/status'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            invalid_url = '/api/courses/999/assignments/'+str(self.fixtures.assignment.id)+'/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = '/api/courses/'+str(self.fixtures.course.id)+'/assignments/999/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

        with self.login(self.fixtures.instructor.username):
            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['comparisons']['available'])
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.fixtures.assignment.total_comparisons_required)
            self.assertFalse(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 0)

            # test authorized instructor - multiple answers
            self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.instructor)
            self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.instructor)
            self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.instructor)

            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['comparisons']['available'])
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.fixtures.assignment.total_comparisons_required)
            self.assertTrue(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 3)

        self.fixtures.add_students(1)
        with self.login(self.fixtures.students[-1].username):
            # test authorized student - no answers
            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['comparisons']['available'])
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.fixtures.assignment.total_comparisons_required)
            self.assertFalse(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 0)

            # test authorized student - answered
            self.fixtures.add_answer(self.fixtures.assignment, self.fixtures.students[-1])

            rv = self.client.get(url)
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['comparisons']['available'])
            self.assertEqual(status['comparisons']['count'], 0)
            self.assertEqual(status['comparisons']['left'], self.fixtures.assignment.total_comparisons_required)
            self.assertTrue(status['answers']['answered'])
            self.assertEqual(status['answers']['count'], 1)