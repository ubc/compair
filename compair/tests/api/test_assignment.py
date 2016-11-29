import datetime
import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, ComparisonTestData, \
    TestFixture, LTITestData
from data.factories import AssignmentFactory
from compair.models import Assignment, Comparison, PairingAlgorithm, \
    CourseGrade, AssignmentGrade, SystemRole, CourseRole, LTIOutcome
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db


class AssignmentAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.url = '/api/courses/' + self.data.get_course().uuid + '/assignments'

    def test_get_single_assignment(self):
        assignment_expected = self.data.get_assignments()[0]
        assignment_api_url = self.url + '/' + assignment_expected.uuid
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
        criterion2 = self.data.create_criterion(self.data.get_authorized_instructor())
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
                { 'id': self.data.get_default_criterion().uuid },
                { 'id': criterion2.uuid }
            ],
            'pairing_algorithm': PairingAlgorithm.random.value,
            'rank_display_limit': 20,
            'answer_grade_weight': 1,
            'comparison_grade_weight': 1,
            'self_evaluation_grade_weight': 1
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
            self.assert400(rv)
            # Test invalid criteria
            bad_criteria = assignment_expected.copy()
            bad_criteria['criteria'] = [{'id': '999'}, {'id': '9999'}]
            rv = self.client.post(
                self.url,
                data=json.dumps(bad_criteria),
                content_type='application/json')
            self.assert400(rv)

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
            self.assertEqual(assignment_expected['rank_display_limit'], rv.json['rank_display_limit'])
            self.assertEqual(len(rv.json['criteria']), 2)
            self.assertIn(rv.json['criteria'][0]['id'], [self.data.get_default_criterion().uuid, criterion2.uuid])
            self.assertIn(rv.json['criteria'][1]['id'], [self.data.get_default_criterion().uuid, criterion2.uuid])

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
            self.assertEqual(assignment_expected['rank_display_limit'], rv.json['rank_display_limit'])
            self.assertEqual(len(rv.json['criteria']), 2)
            self.assertIn(rv.json['criteria'][0]['id'], [self.data.get_default_criterion().uuid, criterion2.uuid])
            self.assertIn(rv.json['criteria'][1]['id'], [self.data.get_default_criterion().uuid, criterion2.uuid])

    def test_edit_assignment(self):
        assignment = self.data.get_assignments()[0]
        url = self.url + '/' + assignment.uuid
        expected = {
            'id': assignment.uuid,
            'name': 'This is the new name.',
            'description': 'new_description',
            'answer_start': assignment.answer_start.isoformat() + 'Z',
            'answer_end': assignment.answer_end.isoformat() + 'Z',
            'number_of_comparisons': assignment.number_of_comparisons,
            'students_can_reply': assignment.students_can_reply,
            'enable_self_evaluation': assignment.enable_self_evaluation,
            'criteria': [
                { 'id': self.data.get_default_criterion().uuid }
            ],
            'pairing_algorithm': PairingAlgorithm.adaptive.value,
            'rank_display_limit': 10,
            'answer_grade_weight': 2,
            'comparison_grade_weight': 2,
            'self_evaluation_grade_weight': 2
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
            invalid_url = '/api/courses/999/assignments/' + assignment.uuid
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

            # test change rank limit
            change_rank_limit = expected.copy()
            change_rank_limit['rank_display_limit'] = None
            rv = self.client.post(url, data=json.dumps(change_rank_limit), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

            change_rank_limit = expected.copy()
            change_rank_limit['rank_display_limit'] = 100
            rv = self.client.post(url, data=json.dumps(change_rank_limit), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

            # test edit by author add & remove criteria
            new_criterion = self.data.create_criterion(self.data.get_authorized_instructor())
            add_criteria = expected.copy()
            add_criteria['criteria'] = [{ 'id': new_criterion.uuid }]
            rv = self.client.post(url, data=json.dumps(add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

        with self.login(self.data.get_authorized_ta().username):
            # test edit by user who can manage posts (TA)
            ta_expected = {
                'id': assignment.uuid,
                'name': 'Another name',
                'description': 'new_description',
                'answer_start': assignment.answer_start.isoformat() + 'Z',
                'answer_end': assignment.answer_end.isoformat() + 'Z',
                'number_of_comparisons': assignment.number_of_comparisons,
                'students_can_reply': assignment.students_can_reply,
                'enable_self_evaluation': assignment.enable_self_evaluation,
                'criteria': [
                    { 'id': self.data.get_default_criterion().uuid }
                ],
                'pairing_algorithm': PairingAlgorithm.random.value,
                'rank_display_limit': 20,
                'answer_grade_weight': 2,
                'comparison_grade_weight': 2,
                'self_evaluation_grade_weight': 2
            }
            rv = self.client.post(url, data=json.dumps(ta_expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(ta_expected['name'], rv.json['name'])
            self.assertEqual(ta_expected['description'], rv.json['description'])
            self.assertEqual(ta_expected['pairing_algorithm'], rv.json['pairing_algorithm'])
            self.assertEqual(ta_expected['rank_display_limit'], rv.json['rank_display_limit'])

            # test edit by TA add & remove criteria
            ta_new_criterion = self.data.create_criterion(self.data.get_authorized_ta())
            ta_add_criteria = ta_expected.copy()
            ta_add_criteria['criteria'] = [{ 'id': ta_new_criterion.uuid }]
            rv = self.client.post(url, data=json.dumps(ta_add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

    def test_delete_assignment(self):
        # Test deleting the assignment
        assignment = Assignment.query.first()
        expected_ret = {'id': assignment.uuid}
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.delete(self.url + '/' + assignment.uuid)
            self.assert403(rv)
            self.assertEqual(
                '<p>' + self.data.get_authorized_student().username + ' does not have delete access to assignment '+assignment.uuid+'</p>',
                rv.json['message'])

        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(self.url + '/' + assignment.uuid)
            self.assert200(rv)
            self.assertEqual(expected_ret['id'], rv.json['id'], "assignment " + str(rv.json['id']) + " deleted successfully")

    def _verify_assignment(self, expected, actual):
        self.assertEqual(expected.name, actual['name'])
        self.assertEqual(expected.description, actual['description'])
        self.assertEqual(expected.user_uuid, actual['user_id'])
        self.assertEqual(expected.pairing_algorithm.value, actual['pairing_algorithm'])
        self.assertEqual(expected.rank_display_limit, actual['rank_display_limit'])



class AssignmentEditComparedAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentEditComparedAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.url = '/api/courses/' + self.data.get_course().uuid + '/assignments'
        self.assignment = self.data.get_assignments()[0]

    def _submit_all_possible_comparisons_for_user(self, user_id):
        submit_count = 0

        for comparison_example in self.data.comparisons_examples:
            if comparison_example.assignment_id == self.assignment.id:
                comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
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
            comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
            for comparison in comparisons:
                comparison.completed = True
                comparison.winner_id = min([comparisons[0].answer1_id, comparisons[0].answer2_id])
                db.session.add(comparison)
            submit_count += 1
            db.session.commit()

            Comparison.calculate_scores(self.assignment.id)
        return submit_count

    def test_edit_compared_assignment(self):
        url = self.url + '/' + self.assignment.uuid
        expected = {
            'id': self.assignment.uuid,
            'name': 'This is the new name.',
            'description': 'new_description',
            'answer_start': self.assignment.answer_start.isoformat() + 'Z',
            'answer_end': self.assignment.answer_end.isoformat() + 'Z',
            'number_of_comparisons': self.assignment.number_of_comparisons,
            'students_can_reply': self.assignment.students_can_reply,
            'enable_self_evaluation': self.assignment.enable_self_evaluation,
            'criteria': [
                { 'id': self.data.get_default_criterion().uuid }
            ],
            'pairing_algorithm': self.assignment.pairing_algorithm.value,
            'rank_display_limit': 10
        }
        compare_count_result = self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)

        # test edit compared assignment
        with self.login(self.data.get_authorized_instructor().username):
            # test cannot change pairing_algorithm
            chaged_pairing = expected.copy()
            chaged_pairing['pairing_algorithm'] = PairingAlgorithm.adaptive.value
            rv = self.client.post(url, data=json.dumps(chaged_pairing), content_type='application/json')
            self.assert403(rv)
            self.assertEqual(rv.json['error'],
                'The pair selection algorithm cannot be changed in the assignment ' + \
                'because it has already been used in an evaluation.')

            # test cannot change criteria
            change_criteria = expected.copy()
            change_criteria['criteria'] = [
                { 'id': self.data.create_criterion(self.data.get_authorized_instructor()).uuid }
            ]
            rv = self.client.post(url, data=json.dumps(change_criteria), content_type='application/json')
            self.assert403(rv)
            self.assertEqual(rv.json['error'],
                'The criteria cannot be changed in the assignment ' + \
                'because they have already been used in an evaluation.')

            # can otherwise edit compared assignments
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected['name'], rv.json['name'])
            self.assertEqual(expected['description'], rv.json['description'])
            self.assertEqual(expected['pairing_algorithm'], rv.json['pairing_algorithm'])
            self.assertEqual(expected['rank_display_limit'], rv.json['rank_display_limit'])

class AssignmentStatusComparisonsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentStatusComparisonsAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.url = '/api/courses/' + self.data.get_course().uuid + '/assignments'
        self.assignment = self.data.get_assignments()[0]

    def _submit_all_possible_comparisons_for_user(self, user_id):
        submit_count = 0

        for comparison_example in self.data.comparisons_examples:
            if comparison_example.assignment_id == self.assignment.id:
                comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
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
            comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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

        with self.login(self.data.get_authorized_student().username):
            # test authorized student - when haven't compared
            rv = self.client.get(url)
            self.assert200(rv)
            for assignment in assignments:
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
        url = self.url + '/' + self.assignment.uuid + '/status'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_student().username):
            invalid_url = '/api/courses/999/assignments/'+self.assignment.uuid+'/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = '/api/courses/'+self.data.get_course().uuid+'/assignments/999/status'
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
            self.assertEqual(status['answers']['count'], 1)

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

class AssignmentStatusAnswersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentStatusAnswersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_assignments=2, num_groups=2)
        self.url = '/api/courses/' + self.fixtures.course.uuid + '/assignments'

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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
                self.assertTrue(assignment.uuid in rv.json['statuses'])
                status = rv.json['statuses'][assignment.uuid]
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
        url = self.url + '/' + self.fixtures.assignment.uuid + '/status'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            invalid_url = '/api/courses/999/assignments/'+self.fixtures.assignment.uuid+'/status'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = '/api/courses/'+self.fixtures.course.uuid+'/assignments/999/status'
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



class AssignmentCourseGradeUpdateAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentCourseGradeUpdateAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_assignments=2, num_groups=2)
        self.url = '/api/courses/' + self.fixtures.course.uuid + '/assignments'
        self.lti_data = LTITestData()

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_create(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        url = self.url

        course_grades = {
            course_grade.user_id: course_grade.grade \
                for course_grade in CourseGrade.get_course_grades(self.fixtures.course)
        }

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
                { 'id': self.fixtures.default_criterion.uuid }
            ],
            'pairing_algorithm': PairingAlgorithm.random.value,
            'rank_display_limit': 20,
            'answer_grade_weight': 1,
            'comparison_grade_weight': 1,
            'self_evaluation_grade_weight': 1
        }

        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert200(rv)

            new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)
            self.assertEqual(len(course_grades.items()), len(new_course_grades))

            # adding an assignment should lower all grades for course
            for new_course_grade in new_course_grades:
                grade = course_grades.get(new_course_grade.user_id)
                self.assertIsNotNone(grade)
                self.assertLess(new_course_grade.grade, grade)

        # test lti grade post
        lti_consumer = self.lti_data.lti_consumer
        student = self.fixtures.students[0]
        lti_user_resource_link = self.lti_data.setup_student_user_resource_links(
            student, self.fixtures.course)

        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert200(rv)

            new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)
            student_grade_id = next((new_course_grade.id \
                for new_course_grade in new_course_grades  \
                if new_course_grade.user_id == student.id)
            )

            mocked_update_assignment_grades_run.assert_not_called()

            mocked_update_course_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link.lis_result_sourcedid, student_grade_id)]
            )
            mocked_update_course_grades_run.reset_mock()

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_edit(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        assignment = self.fixtures.assignment
        url = self.url + '/' + assignment.uuid

        expected = {
            'id': assignment.uuid,
            'name': 'This is the new name.',
            'description': 'new_description',
            'answer_start': assignment.answer_start.isoformat() + 'Z',
            'answer_end': assignment.answer_end.isoformat() + 'Z',
            'number_of_comparisons': assignment.number_of_comparisons,
            'students_can_reply': assignment.students_can_reply,
            'enable_self_evaluation': assignment.enable_self_evaluation,
            'criteria': [
                { 'id': self.fixtures.default_criterion.uuid }
            ],
            'pairing_algorithm': PairingAlgorithm.adaptive.value,
            'rank_display_limit': 10,
            'answer_grade_weight': assignment.answer_grade_weight,
            'comparison_grade_weight': assignment.answer_grade_weight,
            'self_evaluation_grade_weight': assignment.self_evaluation_grade_weight,
        }

        course_grades = {
            course_grade.user_id: course_grade.grade \
                for course_grade in CourseGrade.get_course_grades(self.fixtures.course)
        }

        assignment_grades = {
            assignment_grade.user_id: assignment_grade.grade \
                for assignment_grade in AssignmentGrade.get_assignment_grades(assignment)
        }

        lti_consumer = self.lti_data.lti_consumer
        student = self.fixtures.students[0]
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            student, self.fixtures.course, self.fixtures.assignment)

        with self.login(self.fixtures.instructor.username):
            # grades shouldn't change if weight don't change
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)

            new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)
            self.assertEqual(len(course_grades.items()), len(new_course_grades))
            for new_course_grade in new_course_grades:
                grade = course_grades.get(new_course_grade.user_id)
                self.assertIsNotNone(grade)
                self.assertAlmostEqual(new_course_grade.grade, grade)

            new_assignment_grades = AssignmentGrade.get_assignment_grades(assignment)
            self.assertEqual(len(assignment_grades.items()), len(new_assignment_grades))
            for new_assignment_grade in new_assignment_grades:
                grade = assignment_grades.get(new_assignment_grade.user_id)
                self.assertIsNotNone(grade)
                self.assertAlmostEqual(new_assignment_grade.grade, grade)

            mocked_update_assignment_grades_run.assert_not_called()
            mocked_update_course_grades_run.assert_not_called()

            # grades should change if weights change
            for weight in ['answer_grade_weight', 'comparison_grade_weight', 'self_evaluation_grade_weight']:
                modified_expected = expected.copy()
                modified_expected[weight] += 1
                if weight == 'self_evaluation_grade_weight':
                    modified_expected['enable_self_evaluation'] = True

                rv = self.client.post(url, data=json.dumps(modified_expected), content_type='application/json')
                self.assert200(rv)

                new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)
                self.assertEqual(len(course_grades.items()), len(new_course_grades))
                for new_course_grade in new_course_grades:
                    grade = course_grades.get(new_course_grade.user_id)
                    self.assertIsNotNone(grade)
                    self.assertNotEqual(new_course_grade.grade, grade)

                new_assignment_grades = AssignmentGrade.get_assignment_grades(assignment)
                self.assertEqual(len(assignment_grades.items()), len(new_assignment_grades))
                for new_assignment_grade in new_assignment_grades:
                    grade = assignment_grades.get(new_assignment_grade.user_id)
                    self.assertIsNotNone(grade)
                    self.assertNotEqual(new_assignment_grade.grade, grade)

                student_assignment_grade_id = next((new_assignment_grade.id \
                    for new_assignment_grade in new_assignment_grades  \
                    if new_assignment_grade.user_id == student.id)
                )
                mocked_update_assignment_grades_run.assert_called_once_with(
                    lti_consumer.id,
                    [(lti_user_resource_link2.lis_result_sourcedid, student_assignment_grade_id)]
                )
                mocked_update_assignment_grades_run.reset_mock()

                student_course_grade_id = next((new_course_grade.id \
                    for new_course_grade in new_course_grades  \
                    if new_course_grade.user_id == student.id)
                )
                mocked_update_course_grades_run.assert_called_once_with(
                    lti_consumer.id,
                    [(lti_user_resource_link1.lis_result_sourcedid, student_course_grade_id)]
                )
                mocked_update_course_grades_run.reset_mock()


    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_delete(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        # add dumby Assignment
        self.fixtures.add_assignments(num_assignments=1)
        db.session.commit()
        assignment = self.fixtures.assignments.pop()
        url = self.url + '/' + assignment.uuid
        self.fixtures.course.calculate_grades()

        course_grades = {
            course_grade.user_id: course_grade.grade \
                for course_grade in CourseGrade.get_course_grades(self.fixtures.course)
        }

        lti_consumer = self.lti_data.lti_consumer
        student = self.fixtures.students[0]
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            student, self.fixtures.course, self.fixtures.assignment)

        with self.login(self.fixtures.instructor.username):
            rv = self.client.delete(url)
            self.assert200(rv)

            new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)

            self.assertEqual(len(course_grades.items()), len(new_course_grades))
            # removing an assignment raise all grades for course (since no students completed any of it)
            for new_course_grade in new_course_grades:
                grade = course_grades.get(new_course_grade.user_id)
                self.assertIsNotNone(grade)
                self.assertGreater(new_course_grade.grade, grade)

            mocked_update_assignment_grades_run.assert_not_called()

            student_course_grade_id = next((new_course_grade.id \
                for new_course_grade in new_course_grades  \
                if new_course_grade.user_id == student.id)
            )
            mocked_update_course_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link1.lis_result_sourcedid, student_course_grade_id)]
            )
            mocked_update_course_grades_run.reset_mock()

            # there shouldn't been any more course grades after removing all assignments
            for assignment in self.fixtures.course.assignments:
                if assignment.active:
                    url = self.url + '/' + assignment.uuid
                    rv = self.client.delete(url)
                    self.assert200(rv)

            new_course_grades = CourseGrade.get_course_grades(self.fixtures.course)
            self.assertEqual(0, len(new_course_grades))