import json
import copy
import operator

from data.fixtures.test_data import ComparisonTestData
from acj.models import Answer, Comparison
from acj.tests.test_acj import ACJAPITestCase
from acj.core import db

import mock

class ComparisonAPITests(ACJAPITestCase):
    def setUp(self):
        super(ComparisonAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.course = self.data.get_course()
        self.assignment = self.data.get_assignments()[0]
        self.base_url = self._build_url(self.course.id, self.assignment.id)

    def _build_url(self, course_id, assignment_id, tail=""):
        url = \
            '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/comparisons' + \
            tail
        return url

    def _build_comparison_submit(self, winner_id):
        submit = {
            'comparisons': [
                {
                    'criteria_id': self.assignment.assignment_criteria[0].criteria_id,
                    'winner_id': winner_id
                }
            ]
        }
        return submit

    def test_get_answer_pair_access_control(self):
        # test login required
        rv = self.client.get(self.base_url)
        self.assert401(rv)
        # test deny access to unenroled users
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        # enroled user from this point on
        with self.login(self.data.get_authorized_student().username):
            # test non-existent course
            rv = self.client.get(self._build_url(9993929, self.assignment.id))
            self.assert404(rv)
            # test non-existent assignment
            rv = self.client.get(self._build_url(self.course.id, 23902390))
            self.assert404(rv)
            # no comparisons has been entered yet, assignment is not in comparing period
            rv = self.client.get(self._build_url(
                self.course.id, self.data.get_assignment_in_answer_period().id))
            self.assert403(rv)

    def test_get_answer_pair_basic(self):
        with self.login(self.data.get_authorized_student().username):
            # no comparisons has been entered yet
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answer_pair = rv.json
            actual_answer1 = actual_answer_pair['objects'][0]['answer1']
            actual_answer2 = actual_answer_pair['objects'][0]['answer2']
            expected_answer_ids = [answer.id for answer in self.data.get_student_answers()]
            # make sure that we actually got answers for the assignment we're targetting
            self.assertIn(actual_answer1['id'], expected_answer_ids)
            self.assertIn(actual_answer2['id'], expected_answer_ids)

    def test_get_answer_pair_answer_exclusions_for_answers_with_no_scores(self):
        """
        The user doing comparisons should not see their own answer in a comparison.
        Instructor and TA answers should not show up.
        Answers cannot be paired with itself.
        For answers that don't have a score yet, which means they're randomly matched up.
        """
        with self.login(self.data.get_authorized_student().username):
            excluded_student_answer = Answer.query.filter(
                Answer.user_id == self.data.get_authorized_student().id,
                Answer.assignment_id == self.assignment.id).first()
            self.assertTrue(excluded_student_answer, "Missing authorized student's answer.")
            excluded_instructor_answer = Answer.query.filter(
                Answer.user_id == self.data.get_authorized_instructor().id,
                Answer.assignment_id == self.assignment.id).first()
            self.assertTrue(excluded_instructor_answer, "Missing instructor answer")
            excluded_ta_answer = Answer.query.filter(
                Answer.user_id == self.data.get_authorized_ta().id,
                Answer.assignment_id == self.assignment.id).first()
            self.assertTrue(excluded_ta_answer, "Missing TA answer")
            # no comparisons has been entered yet, this tests the randomized pairing when no answers has
            # scores, since it's randomized though, we'll have to run it lots of times to be sure
            for i in range(50):
                rv = self.client.get(self.base_url)
                self.assert200(rv)
                actual_answer_pair = rv.json
                actual_answer1 = actual_answer_pair['objects'][0]['answer1']
                actual_answer2 = actual_answer_pair['objects'][0]['answer2']
                # exclude student's own answer
                self.assertNotEqual(actual_answer1['id'], excluded_student_answer.id)
                self.assertNotEqual(actual_answer2['id'], excluded_student_answer.id)
                # exclude instructor answer
                self.assertNotEqual(actual_answer1['id'], excluded_instructor_answer.id)
                self.assertNotEqual(actual_answer2['id'], excluded_instructor_answer.id)
                # exclude ta answer
                self.assertNotEqual(actual_answer1['id'], excluded_ta_answer.id)
                self.assertNotEqual(actual_answer2['id'], excluded_ta_answer.id)

        # need a user with no answers submitted, otherwise pairs with the same answers
        # won't be generated since we have too few answers
        with self.login(self.data.get_authorized_student_with_no_answers().username):
            for i in range(50):
                rv = self.client.get(self.base_url)
                self.assert200(rv)
                # answer cannot be paired with itself
                self.assertNotEqual(rv.json['objects'][0]['answer1_id'], rv.json['objects'][0]['answer2_id'])

    def test_submit_comparison_access_control(self):
        # test login required
        rv = self.client.post(
            self.base_url,
            data=json.dumps({}),
            content_type='application/json')
        self.assert401(rv)

        # establish expected data by first getting an answer pair
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            # expected_answer_pair = rv.json
            comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'])

        # test deny access to unenroled users
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert403(rv)

        # test deny access to non-students
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert403(rv)

        # authorized user from this point
        with self.login(self.data.get_authorized_student().username):
            # test non-existent course
            rv = self.client.post(
                self._build_url(9999999, self.assignment.id),
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert404(rv)
            # test non-existent assignment
            rv = self.client.post(
                self._build_url(self.course.id, 9999999),
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert404(rv)
            # test reject missing criteria
            faulty_comparisons = copy.deepcopy(comparison_submit)
            faulty_comparisons['comparisons'] = []
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)
            # test reject missing course criteria id
            faulty_comparisons = copy.deepcopy(comparison_submit)
            del faulty_comparisons['comparisons'][0]['criteria_id']
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)
            # test reject missing winner
            faulty_comparisons = copy.deepcopy(comparison_submit)
            del faulty_comparisons['comparisons'][0]['winner_id']
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)
            # test invalid criteria id
            faulty_comparisons = copy.deepcopy(comparison_submit)
            faulty_comparisons['comparisons'][0]['criteria_id'] = 3930230
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)
            # test invalid winner id
            faulty_comparisons = copy.deepcopy(comparison_submit)
            faulty_comparisons['comparisons'][0]['winner_id'] = 2382301
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)

    def test_submit_comparison_basic(self):
        with self.login(self.data.get_authorized_student().username):
            # calculate number of comparisons to do before user has compared all the pairs it can
            num_eligible_answers = -1  # need to minus one to exclude the logged in user's own answer
            for answer in self.data.get_student_answers():
                if answer.assignment.id == self.assignment.id:
                    num_eligible_answers += 1
            # n - 1 possible pairs before all answers have been compared
            num_possible_comparisons = num_eligible_answers - 1
            winner_ids = []
            for i in range(num_possible_comparisons):
                # establish expected data by first getting an answer pair
                rv = self.client.get(self.base_url)
                self.assert200(rv)
                expected_answer_pair = rv.json
                comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'])
                winner_ids.append(rv.json['objects'][0]['winner_id'])
                # test normal post
                rv = self.client.post(
                    self.base_url,
                    data=json.dumps(comparison_submit),
                    content_type='application/json')
                self.assert200(rv)
                actual_comparisons = rv.json['objects']
                self._validate_comparison_submit(comparison_submit, actual_comparisons, expected_answer_pair)
                # Resubmit of same comparison should fail
                rv = self.client.post(
                    self.base_url,
                    data=json.dumps(comparison_submit),
                    content_type='application/json')
                self.assert400(rv)
            # all answers has been compared by the user, errors out when trying to get another pair
            rv = self.client.get(self.base_url)
            self.assert400(rv)

    def _validate_comparison_submit(self, comparison_submit, actual_comparisons, expected_answer_pair):
        self.assertEqual(
            len(actual_comparisons), len(comparison_submit['comparisons']),
            "The number of comparisons saved does not match the number sent")
        for actual_comparison in actual_comparisons:
            self.assertEqual(
                expected_answer_pair['objects'][0]['answer1_id'],
                actual_comparison['answer1_id'],
                "Expected and actual comparison answer1 id did not match")
            self.assertEqual(
                expected_answer_pair['objects'][0]['answer2_id'],
                actual_comparison['answer2_id'],
                "Expected and actual comparison answer2 id did not match")
            found_comparison = False
            for expected_comparison in comparison_submit['comparisons']:
                if expected_comparison['criteria_id'] != \
                        actual_comparison['criteria_id']:
                    continue
                self.assertEqual(
                    expected_comparison['winner_id'],
                    actual_comparison['winner_id'],
                    "Expected and actual winner answer id did not match.")
                found_comparison = True
            self.assertTrue(
                found_comparison,
                "Actual comparison received contains a comparison that was not sent.")

    def test_get_answer_pair_answer_exclusion_with_scored_answers(self):
        """
        The user doing comparisons should not see their own answer in a comparison.
        Instructor and TA answers should not show up.
        Answers cannot be paired with itself.
        Scored answer pairing means answers should be matched up to similar scores.
        """
        # Make sure all answers are compared first
        self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)
        self._submit_all_possible_comparisons_for_user(
            self.data.get_secondary_authorized_student().id)

        with self.login(self.data.get_authorized_student_with_no_answers().username):
            excluded_instructor_answer = Answer.query.filter(
                Answer.user_id == self.data.get_authorized_instructor().id,
                Answer.assignment_id == self.assignment.id).first()
            self.assertTrue(excluded_instructor_answer, "Missing instructor answer")
            excluded_ta_answer = Answer.query.filter(
                Answer.user_id == self.data.get_authorized_ta().id,
                Answer.assignment_id == self.assignment.id).first()
            self.assertTrue(excluded_ta_answer, "Missing TA answer")
            # no comparisons has been entered yet, this tests the randomized pairing when no answers has
            # scores, since it's randomized though, we'll have to run it lots of times to be sure
            for i in range(50):
                rv = self.client.get(self.base_url)
                self.assert200(rv)
                actual_answer_pair = rv.json
                actual_answer1 = actual_answer_pair['objects'][0]['answer1']
                actual_answer2 = actual_answer_pair['objects'][0]['answer2']
                # exclude instructor answer
                self.assertNotEqual(actual_answer1['id'], excluded_instructor_answer.id)
                self.assertNotEqual(actual_answer2['id'], excluded_instructor_answer.id)
                # exclude ta answer
                self.assertNotEqual(actual_answer1['id'], excluded_ta_answer.id)
                self.assertNotEqual(actual_answer2['id'], excluded_ta_answer.id)
                # answer cannot be paired with itself
                self.assertNotEqual(actual_answer1['id'], actual_answer2['id'])

    def _submit_all_possible_comparisons_for_user(self, user_id):
        # self.login(username)
        # calculate number of comparisons to do before user has compared all the pairs it can
        num_eligible_answers = 0  # need to minus one to exclude the logged in user's own answer
        for answer in self.data.get_student_answers():
            if answer.assignment_id == self.assignment.id and answer.user_id != user_id:
                num_eligible_answers += 1
        # n - 1 possible pairs before all answers have been compared
        num_possible_comparisons = num_eligible_answers - 1
        winner_ids = []
        loser_ids = []
        for i in range(num_possible_comparisons):
            comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id)
            answer1_id = comparisons[0].answer1_id
            answer2_id = comparisons[0].answer2_id
            min_id = min([answer1_id, answer2_id])
            max_id = max([answer1_id, answer2_id])
            winner_ids.append(min_id)
            loser_ids.append(max_id)
            for comparison in comparisons:
                comparison.completed = True
                comparison.winner_id = min_id
                db.session.add(comparison)
            db.session.commit()

            Comparison.calculate_scores(self.assignment.id)
        # test normal post
        # rv = self.client.post(self.base_url, data=json.dumps(comparison_submit),
        # 					  content_type='application/json')
        # self.assert200(rv)
        # self.logout()

        return {'winners': winner_ids, 'losers': loser_ids}

    @mock.patch('random.shuffle')
    def test_score_calculation(self, mock_shuffle):
        """
        This is just a rough check on whether score calculations are correct. Answers
        that has more wins should have the highest scores.
        """
        # Make sure all answers are compared first
        comparisons_auth = self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)
        comparisons_secondary = self._submit_all_possible_comparisons_for_user(
            self.data.get_secondary_authorized_student().id)

        loser_ids = comparisons_auth['losers']
        loser_ids.extend(comparisons_secondary['losers'])
        winner_ids = comparisons_auth['winners']
        winner_ids.extend(comparisons_secondary['winners'])

        # Count the number of wins each answer has had
        num_wins_by_id = {}
        for loser_id in loser_ids:
            num_wins_by_id[loser_id] = num_wins_by_id.setdefault(loser_id, 0)
        for winner_id in winner_ids:
            num_wins = num_wins_by_id.setdefault(winner_id, 0)
            num_wins_by_id[winner_id] = num_wins + 1

        # Get the actual score calculated for each answer
        answers = self.data.get_student_answers()
        answer_scores = {}
        for answer in answers:
            if answer.assignment.id == self.assignment.id:
                answer_scores[answer.id] = answer.scores[0].score

        # Check that ranking by score and by wins match, this only works for low number of
        # comparisons
        sorted_expect_ranking = sorted(num_wins_by_id.items(), key=operator.itemgetter(1))
        expected_ranking_by_wins = [answer_id for (answer_id, wins) in sorted_expect_ranking]

        sorted_actual_ranking = sorted(answer_scores.items(), key=operator.itemgetter(1))
        actual_ranking_by_scores = [answer_id for (answer_id, score) in sorted_actual_ranking]

        self.assertSequenceEqual(actual_ranking_by_scores, expected_ranking_by_wins)

    def test_comparison_count_matched_pairing(self):
        # Make sure all answers are compared first
        answer_ids = self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)
        answer_ids2 = self._submit_all_possible_comparisons_for_user(
            self.data.get_secondary_authorized_student().id)
        compared_ids = \
            answer_ids['winners'] + answer_ids2['winners'] + \
            answer_ids['losers'] + answer_ids2['losers']

        # Just a simple test for now, make sure that answers with the smaller number of
        # comparisons are matched up with each other
        # Count number of comparisons done for each answer
        num_comp_by_id = {}
        for answer_id in compared_ids:
            num_comp = num_comp_by_id.setdefault(answer_id, 0)
            num_comp_by_id[answer_id] = num_comp + 1

        comp_groups = {}
        for answerId in num_comp_by_id:
            count = num_comp_by_id[answerId]
            comp_groups.setdefault(count, [])
            comp_groups[count].append(answerId)
        counts = sorted(comp_groups)
        # get the answerIds with the lowest count of comparisons
        possible_answer_ids = comp_groups[counts[0]]
        if len(possible_answer_ids) < 2:
            # if the lowest count group does not have enough to create a pair - add the next group
            possible_answer_ids += comp_groups[counts[1]]

        # Check that the 2 answers with 1 win gets returned
        with self.login(self.data.get_authorized_student_with_no_answers().username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            self.assertIn(rv.json['objects'][0]['answer1_id'], possible_answer_ids)
            self.assertIn(rv.json['objects'][0]['answer2_id'], possible_answer_ids)

    def test_get_comparison_count(self):
        url = self._build_url(self.data.get_course().id, self.assignment.id)

        # test login required
        tail = '/users/' + str(self.data.get_authorized_student().id) + '/count'
        rv = self.client.get(url + tail)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            tail = '/users/' + str(self.data.get_unauthorized_student().id) + '/count'
            rv = self.client.get(url + tail)
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            tail = '/users/' + str(self.data.get_authorized_instructor().id) + '/count'
            # test invalid course id
            invalid_url = self._build_url(999, self.assignment.id)
            rv = self.client.get(invalid_url + tail)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self._build_url(self.data.get_course().id, 999)
            rv = self.client.get(invalid_url + tail)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url + tail)
            self.assert200(rv)
            self.assertEqual(rv.json['count'], 0)

        # test authorized student
        winners = self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)['winners']
        tail = '/users/' + str(self.data.get_authorized_student().id) + '/count'
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url + tail)
            self.assert200(rv)
            self.assertEqual(rv.json['count'], len(winners))

    def test_get_all_comparison_count(self):
        url = '/api/courses/' + str(self.data.get_course().id) + '/comparisons/count'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.get('/api/courses/999/comparisons/count')
            self.assert404(rv)

            assignments = self.data.get_assignments()
            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            count = rv.json['comparisons']

            for assignment in assignments:
                assignment_id = str(assignment.id)
                self.assertTrue(assignment_id in count)
                self.assertEqual(count[assignment_id], 0)

        # test authorized student
        winners = self._submit_all_possible_comparisons_for_user(
            self.data.get_authorized_student().id)['winners']
        comparison_count = len(winners)
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            count = rv.json['comparisons']

            for assignment in assignments:
                assignment_id = str(assignment.id)
                self.assertTrue(assignment_id in count)
                jcount = comparison_count if assignment.id == self.assignment.id else 0
                self.assertEqual(count[assignment_id], jcount)

    def test_get_all_available(self):
        url = '/api/courses/' + str(self.data.get_course().id) + '/comparisons/available'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            # test invalid course id
            invalid_url = '/api/courses/999/comparisons/available'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            first_assignment = self.data.get_assignments()[0]
            last_assignment = self.data.get_assignments()[-1]
            expected = {assignment.id: True for assignment in self.data.get_assignments()}
            expected[last_assignment.id] = False
            # test authorized student - when haven't compared
            rv = self.client.get(url)
            self.assert200(rv)
            logic = rv.json['available']
            for assignment in self.data.get_assignments():
                self.assertEqual(logic[str(assignment.id)], expected[assignment.id])

        self._submit_all_possible_comparisons_for_user(self.data.get_authorized_student().id)
        with self.login(self.data.get_authorized_student().username):
            # test authorized student - when have compared all
            rv = self.client.get(url)
            self.assert200(rv)
            available = rv.json['available']
            expected[first_assignment.id] = False
            for assignment in self.data.get_assignments():
                self.assertEqual(available[str(assignment.id)], expected[assignment.id])

    def test_get_available(self):
        url = self._build_url(self.data.get_course().id, self.assignment.id)

        tail = '/users/' + str(self.data.get_unauthorized_student().id) + '/available'
        # test login required
        rv = self.client.get(url + tail)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(url + tail)
            self.assert403(rv)

        # test invalid course id
        tail = '/users/' + str(self.data.get_authorized_student().id) + '/available'
        with self.login(self.data.get_authorized_student().username):
            invalid_url = self._build_url(999, self.assignment.id)
            rv = self.client.get(invalid_url + tail)
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self._build_url(self.data.get_course().id, 999)
            rv = self.client.get(invalid_url + tail)
            self.assert404(rv)

        with self.login(self.data.get_authorized_student().username):
            # test authorized student - when haven't compared
            rv = self.client.get(url + tail)
            self.assert200(rv)
            self.assertTrue(rv.json['available'])

            self._submit_all_possible_comparisons_for_user(self.data.get_authorized_student().id)
            # test authorized student - when have compared all
            self.login(self.data.get_authorized_student().username)
            rv = self.client.get(url + tail)
            self.assert200(rv)
            self.assertFalse(rv.json['available'])
