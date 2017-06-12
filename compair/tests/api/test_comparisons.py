import json
import copy
import operator
import datetime

from data.fixtures.test_data import ComparisonTestData, LTITestData
from data.factories import AssignmentCriterionFactory
from compair.models import Answer, Comparison, CourseGrade, AssignmentGrade
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db

import mock

class ComparisonAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(ComparisonAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.course = self.data.get_course()
        self.assignment = self.data.get_assignments()[0]
        self.base_url = self._build_url(self.course.uuid, self.assignment.uuid)
        self.lti_data = LTITestData()

        secondary_criterion = self.data.create_criterion(self.data.authorized_instructor)
        AssignmentCriterionFactory(criterion=secondary_criterion, assignment=self.assignment)
        db.session.commit()

    def _build_url(self, course_uuid, assignment_uuid, tail=""):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/comparisons' + tail
        return url

    def _build_comparison_submit(self, winner_uuid, draft=False):
        submit = {
            'comparisons': [
                {
                    'criterion_id': self.assignment.criteria[0].uuid,
                    'winner_id': winner_uuid,
                    'draft': draft
                },
                {
                    'criterion_id': self.assignment.criteria[1].uuid,
                    'winner_id': winner_uuid,
                    'draft': draft
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
            rv = self.client.get(self._build_url("9993929", self.assignment.uuid))
            self.assert404(rv)
            # test non-existent assignment
            rv = self.client.get(self._build_url(self.course.uuid, "23902390"))
            self.assert404(rv)
            # no comparisons has been entered yet, assignment is not in comparing period
            rv = self.client.get(self._build_url(
                self.course.uuid, self.data.get_assignment_in_answer_period().uuid))
            self.assert403(rv)

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
            # expected_comparisons = rv.json
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

        # authorized user from this point
        with self.login(self.data.get_authorized_student().username):
            # test non-existent course
            rv = self.client.post(
                self._build_url("9999999", self.assignment.uuid),
                data=json.dumps(comparison_submit),
                content_type='application/json')
            self.assert404(rv)
            # test non-existent assignment
            rv = self.client.post(
                self._build_url(self.course.uuid, "9999999"),
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
            del faulty_comparisons['comparisons'][0]['criterion_id']
            rv = self.client.post(
                self.base_url,
                data=json.dumps(faulty_comparisons),
                content_type='application/json')
            self.assert400(rv)
            # test invalid criterion id
            faulty_comparisons = copy.deepcopy(comparison_submit)
            faulty_comparisons['comparisons'][0]['criterion_id'] = 3930230
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

            # test past grace period
            self.assignment.compare_start = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            self.assignment.compare_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
            db.session.add(self.assignment)
            db.session.commit()
            ok_comparisons = copy.deepcopy(comparison_submit)
            rv = self.client.post(
                self.base_url,
                data=json.dumps(ok_comparisons),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual("Assignment comparison deadline has passed.", rv.json['error'])

            # test within grace period
            self.assignment.compare_start = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            self.assignment.compare_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
            db.session.add(self.assignment)
            db.session.commit()
            ok_comparisons = copy.deepcopy(comparison_submit)
            rv = self.client.post(
                self.base_url,
                data=json.dumps(ok_comparisons),
                content_type='application/json')
            self.assert200(rv)

        self.assignment.educators_can_compare = False
        db.session.commit()

        # instructors can access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

            self.assignment.educators_can_compare = True
            db.session.commit()

            rv = self.client.get(self.base_url)
            self.assert200(rv)
            # expected_comparisons = rv.json
            comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'])

            ok_comparisons = copy.deepcopy(comparison_submit)
            rv = self.client.post(
                self.base_url,
                data=json.dumps(ok_comparisons),
                content_type='application/json')
            self.assert200(rv)

        self.assignment.educators_can_compare = False
        db.session.commit()

        # ta can access
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

            self.assignment.educators_can_compare = True
            db.session.commit()

            rv = self.client.get(self.base_url)
            self.assert200(rv)
            # expected_comparisons = rv.json
            comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'])

            ok_comparisons = copy.deepcopy(comparison_submit)
            rv = self.client.post(
                self.base_url,
                data=json.dumps(ok_comparisons),
                content_type='application/json')
            self.assert200(rv)


    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_get_and_submit_comparison(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        lti_consumer = self.lti_data.lti_consumer
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            self.data.get_authorized_student(), self.course, self.assignment)

        users = [self.data.get_authorized_student(), self.data.get_authorized_instructor(), self.data.get_authorized_ta()]
        for user in users:
            max_comparisons = 0
            other_student_answers = 0
            valid_answer_uuids = set()
            for answer in self.data.get_student_answers():
                if answer.assignment.id == self.assignment.id and answer.user_id != user.id:
                    other_student_answers += 1
                    valid_answer_uuids.add(answer.uuid)
            max_comparisons = int(other_student_answers * (other_student_answers - 1) / 2)

            if user.id == self.data.get_authorized_student().id:
                for comparison_example in self.data.comparisons_examples:
                    if comparison_example.assignment_id == self.assignment.id:
                        max_comparisons += 1
                        valid_answer_uuids.add(comparison_example.answer1_uuid)
                        valid_answer_uuids.add(comparison_example.answer2_uuid)

            with self.login(user.username):
                if user.id in [self.data.get_authorized_instructor().id, self.data.get_authorized_ta().id]:
                    self.assignment.educators_can_compare = False
                    db.session.commit()

                    # cannot compare answers unless educators_can_compare is set for assignment
                    rv = self.client.get(self.base_url)
                    self.assert403(rv)

                    self.assignment.educators_can_compare = True
                    db.session.commit()

                current = 0
                while current < max_comparisons:
                    current += 1
                    if user.id == self.data.get_authorized_student().id:
                        course_grade = CourseGrade.get_user_course_grade(self.course, user).grade
                        assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, user).grade

                    # establish expected data by first getting an answer pair
                    rv = self.client.get(self.base_url)
                    self.assert200(rv)
                    actual_answer1_uuid = rv.json['objects'][0]['answer1_id']
                    actual_answer2_uuid = rv.json['objects'][0]['answer2_id']
                    self.assertIn(actual_answer1_uuid, valid_answer_uuids)
                    self.assertIn(actual_answer2_uuid, valid_answer_uuids)
                    self.assertNotEqual(actual_answer1_uuid, actual_answer2_uuid)
                    self.assertTrue(rv.json['new_pair'])
                    self.assertEqual(rv.json['current'], current)

                    # fetch again
                    rv = self.client.get(self.base_url)
                    self.assert200(rv)
                    expected_comparisons = rv.json
                    self.assertEqual(actual_answer1_uuid, rv.json['objects'][0]['answer1_id'])
                    self.assertEqual(actual_answer2_uuid, rv.json['objects'][0]['answer2_id'])
                    self.assertFalse(rv.json['new_pair'])
                    self.assertEqual(rv.json['current'], current)

                    # test draft post
                    comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'], True)
                    rv = self.client.post(
                        self.base_url,
                        data=json.dumps(comparison_submit),
                        content_type='application/json')
                    self.assert200(rv)
                    actual_comparisons = rv.json['objects']
                    self._validate_comparison_submit(comparison_submit, actual_comparisons, expected_comparisons)

                    # test draft post (no answer id)
                    comparison_submit = self._build_comparison_submit(None)
                    rv = self.client.post(
                        self.base_url,
                        data=json.dumps(comparison_submit),
                        content_type='application/json')
                    self.assert200(rv)
                    actual_comparisons = rv.json['objects']
                    self._validate_comparison_submit(comparison_submit, actual_comparisons, expected_comparisons)

                    # test normal post
                    comparison_submit = self._build_comparison_submit(rv.json['objects'][0]['answer1_id'])
                    rv = self.client.post(
                        self.base_url,
                        data=json.dumps(comparison_submit),
                        content_type='application/json')
                    self.assert200(rv)
                    actual_comparisons = rv.json['objects']
                    self._validate_comparison_submit(comparison_submit, actual_comparisons, expected_comparisons)

                    # grades should increase for every comparison
                    if user.id == self.data.get_authorized_student().id:
                        new_course_grade = CourseGrade.get_user_course_grade(self.course, user)
                        new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, user)
                        self.assertGreater(new_course_grade.grade, course_grade)
                        self.assertGreater(new_assignment_grade.grade, assignment_grade)

                        mocked_update_course_grades_run.assert_called_once_with(
                            lti_consumer.id,
                            [(lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id)]
                        )
                        mocked_update_course_grades_run.reset_mock()

                        mocked_update_assignment_grades_run.assert_called_once_with(
                            lti_consumer.id,
                            [(lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id)]
                        )
                        mocked_update_assignment_grades_run.reset_mock()
                    else:
                        new_course_grade = CourseGrade.get_user_course_grade(self.course, user)
                        new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, user)
                        self.assertIsNone(new_course_grade)
                        self.assertIsNone(new_assignment_grade)
                        mocked_update_assignment_grades_run.assert_not_called()
                        mocked_update_course_grades_run.assert_not_called()

                    # Resubmit of same comparison should fail
                    rv = self.client.post(
                        self.base_url,
                        data=json.dumps(comparison_submit),
                        content_type='application/json')
                    self.assert400(rv)

                # all answers has been compared by the user, errors out when trying to get another pair
                rv = self.client.get(self.base_url)
                self.assert400(rv)

    def _validate_comparison_submit(self, comparison_submit, actual_comparisons, expected_comparisons):
        self.assertEqual(
            len(actual_comparisons), len(comparison_submit['comparisons']),
            "The number of comparisons saved does not match the number sent")
        for actual_comparison in actual_comparisons:
            self.assertEqual(
                expected_comparisons['objects'][0]['answer1_id'],
                actual_comparison['answer1_id'],
                "Expected and actual comparison answer1 id did not match")
            self.assertEqual(
                expected_comparisons['objects'][0]['answer2_id'],
                actual_comparison['answer2_id'],
                "Expected and actual comparison answer2 id did not match")
            found_comparison = False
            for expected_comparison in comparison_submit['comparisons']:
                if expected_comparison['criterion_id'] != \
                        actual_comparison['criterion_id']:
                    continue
                self.assertEqual(
                    expected_comparison['winner_id'],
                    actual_comparison['winner_id'],
                    "Expected and actual winner answer id did not match.")
                found_comparison = True
            self.assertTrue(
                found_comparison,
                "Actual comparison received contains a comparison that was not sent.")

    def _submit_all_possible_comparisons_for_user(self, user_id):
        example_winner_ids = []
        example_loser_ids = []

        for comparison_example in self.data.comparisons_examples:
            if comparison_example.assignment_id == self.assignment.id:
                comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
                self.assertEqual(comparisons[0].answer1_id, comparison_example.answer1_id)
                self.assertEqual(comparisons[0].answer2_id, comparison_example.answer2_id)
                min_id = min([comparisons[0].answer1_id, comparisons[0].answer2_id])
                max_id = max([comparisons[0].answer1_id, comparisons[0].answer2_id])
                example_winner_ids.append(min_id)
                example_loser_ids.append(max_id)
                for comparison in comparisons:
                    comparison.completed = True
                    comparison.winner_id = min_id
                    db.session.add(comparison)
                db.session.commit()

        # self.login(username)
        # calculate number of comparisons to do before user has compared all the pairs it can
        num_eligible_answers = 0  # need to minus one to exclude the logged in user's own answer
        for answer in self.data.get_student_answers():
            if answer.assignment_id == self.assignment.id and answer.user_id != user_id:
                num_eligible_answers += 1
        # n(n-1)/2 possible pairs before all answers have been compared
        num_possible_comparisons = int(num_eligible_answers * (num_eligible_answers - 1) / 2)
        winner_ids = []
        loser_ids = []
        for i in range(num_possible_comparisons):
            comparisons = Comparison.create_new_comparison_set(self.assignment.id, user_id, False)
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
        return {
            'comparisons': {
                'winners': winner_ids, 'losers': loser_ids
            },
            'comparison_examples': {
                'winners': example_winner_ids, 'losers': example_loser_ids
            }
        }

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

        loser_ids = comparisons_auth['comparisons']['losers'] + comparisons_secondary['comparisons']['losers']
        winner_ids = comparisons_auth['comparisons']['winners'] + comparisons_secondary['comparisons']['winners']

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
        sorted_expect_ranking = sorted(num_wins_by_id.items(), key=operator.itemgetter(0))
        sorted_expect_ranking = sorted(sorted_expect_ranking, key=operator.itemgetter(1))
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
            answer_ids['comparisons']['winners'] + answer_ids2['comparisons']['winners'] + \
            answer_ids['comparisons']['losers'] + answer_ids2['comparisons']['losers'] + \
            answer_ids['comparison_examples']['winners'] + answer_ids2['comparison_examples']['winners'] + \
            answer_ids['comparison_examples']['losers'] + answer_ids2['comparison_examples']['losers']

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
            answer1 = Answer.query.filter_by(uuid=rv.json['objects'][0]['answer1_id']).first()
            answer2 = Answer.query.filter_by(uuid=rv.json['objects'][0]['answer2_id']).first()
            self.assertIsNotNone(answer1)
            self.assertIsNotNone(answer2)
            self.assertIn(answer1.id, possible_answer_ids)
            self.assertIn(answer2.id, possible_answer_ids)
