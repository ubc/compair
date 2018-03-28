import json
import random
import math
import unittest
import os
import unicodecsv as csv
from enum import Enum

from data.fixtures.test_data import ComparisonTestData
from compair.models import Answer, Comparison, \
    WinningAnswer, AnswerScore, AnswerCriterionScore, \
    PairingAlgorithm, ScoringAlgorithm
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db
from compair.tests import test_app_settings
from compair import create_app

SKIP_VALIDITY_TEST = False
try:
    from scipy.stats import spearmanr, pearsonr, kendalltau
    import numpy
except:
    SKIP_VALIDITY_TEST = True

class WinnerSelector(Enum):
    always_correct = "always_correct"
    correct_with_error = "correct_with_error"
    guessing = "guessing"
    closely_matched_errors = "closely_matched_errors"

class AlgorithmValidityTests(ComPAIRAPITestCase):
    # def create_app(self):
    #     settings = test_app_settings.copy()
    #     settings['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+self._sqlite_db()
    #     app = create_app(settings_override=settings)
    #     return app

    def setUp(self):
        if SKIP_VALIDITY_TEST:
            self.skipTest("scipy and numpy not installed. run `make deps`")
        # remove existing sqlite db if exists
        # self._delete_sqlite_db()

        # TODO: Modify conditions to be more fuzzy (closely_matched_errors with 0.05 correct rate)
        # Depends on results of research
        super(AlgorithmValidityTests, self).setUp()
        self.data = ComparisonTestData()
        self.ACCEPTABLE_CORRELATION = 0.8
        self.NUMBER_OF_ANSWERS = 40
        self.WINNER_SELECTOR = WinnerSelector.always_correct
        self.CORRECT_RATE = 1.0

        self.MAX_COMPARSIONS = (self.NUMBER_OF_ANSWERS - 1) * (self.NUMBER_OF_ANSWERS - 2) / 2
        self.TOTAL_MAX_ROUNDS = 6 # 3 comparisons per student
        self.COMPARISONS_IN_ROUND = math.ceil(self.NUMBER_OF_ANSWERS / 2)
        # stop after lowest of total comparisons possible or 100 rounds worth of comparisons are complete
        self.TOTAL_MAX_COMPARISONS = min(
            self.COMPARISONS_IN_ROUND * self.TOTAL_MAX_ROUNDS,
            self.NUMBER_OF_ANSWERS * self.MAX_COMPARSIONS
        )

        self.course = self.data.create_course()
        self.instructor = self.data.create_instructor()
        self.data.enrol_instructor(self.instructor, self.course)
        self.assignment = self.data.create_assignment_in_comparison_period(
            self.course, self.instructor,
            number_of_comparisons=self.MAX_COMPARSIONS,
            scoring_algorithm=ScoringAlgorithm.elo,
            pairing_algorithm=PairingAlgorithm.adaptive_min_delta
        )

        self.students = []
        self.answers = []
        self.grade_by_answer_uuid = {}
        actual_grades = numpy.random.normal(0.78, 0.1, self.NUMBER_OF_ANSWERS)
        for grade in actual_grades:
            student = self.data.create_normal_user()
            self.data.enrol_student(student, self.course)
            self.students.append(student)

            answer = self.data.create_answer(self.assignment, student, with_score=False)
            self.answers.append(answer)
            self.grade_by_answer_uuid[answer.uuid] = grade

        self.base_url = self._build_url(self.course.uuid, self.assignment.uuid)
        db.session.commit()

    # def tearDown(self):
    #     self._delete_sqlite_db()

    # def _sqlite_db(self):
    #     return 'test_comparison'+str(os.getpid())+'.db'

    # def _delete_sqlite_db(self):
    #     file_path = os.path.join(os.getcwd(), 'compair', self._sqlite_db())
    #     if os.path.isfile(file_path):
    #         try:
    #             os.remove(file_path)
    #         except Exception as e:
    #             print(e)

    def _decide_winner(self, answer1_uuid, answer2_uuid):
        answer1_grade = self.grade_by_answer_uuid[answer1_uuid]
        answer2_grade = self.grade_by_answer_uuid[answer2_uuid]

        if self.WINNER_SELECTOR == WinnerSelector.always_correct:
            return self.always_correct(answer1_grade, answer2_grade)
        elif self.WINNER_SELECTOR == WinnerSelector.guessing:
            return self.guessing()
        elif self.WINNER_SELECTOR == WinnerSelector.correct_with_error:
            return self.correct_with_error(answer1_grade, answer2_grade, self.CORRECT_RATE)
        elif self.WINNER_SELECTOR == WinnerSelector.closely_matched_errors:
            return self.closely_matched_errors(answer1_grade, answer2_grade, self.CORRECT_RATE)
        else:
            raise Exception()

    def always_correct(self, value1, value2):
        return self.correct_with_error(value1, value2, 1.0)

    def correct_with_error(self, value1, value2, correct_rate):
        if value1 == value2:
            return self.guessing()
        correct_answer = WinningAnswer.answer1 if value1 > value2 else WinningAnswer.answer2
        incorrect_answer = WinningAnswer.answer1 if value1 < value2 else WinningAnswer.answer2

        return correct_answer if random.random() <= correct_rate else incorrect_answer

    def guessing(self):
        return WinningAnswer.answer1 if random.random() <= 0.5 else WinningAnswer.answer2

    def closely_matched_errors(self, value1, value2, sigma):
        # make the actual values of answers fuzzy (represents perceived value errors)
        fuzzy_value1 = numpy.random.normal(value1, sigma, 1)[0]
        fuzzy_value2 = numpy.random.normal(value2, sigma, 1)[0]
        # return the correct winner using fuzzy perceived values
        return self.always_correct(fuzzy_value1, fuzzy_value2)

    def _build_url(self, course_uuid, assignment_uuid, tail=""):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/comparisons' + tail
        return url

    def _build_comparison_submit(self, winner, draft=False):
        submit = {
            'comparison_criteria': [],
            'draft': draft
        }

        for criterion in self.assignment.criteria:
            submit['comparison_criteria'].append({
                'criterion_id': criterion.uuid,
                'winner': winner,
                'content': None
            })
        return submit

    def test_random_students_perform_comparisons(self):
        self.student_comparison_count = {
            student.id: 0 for student in self.students
        }

        comparison_count = 0
        round_count = 0
        r_value = None

        while comparison_count < self.TOTAL_MAX_COMPARISONS:
            # select a random student to answer
            student = random.choice(self.students)

            with self.login(student.username):
                # perform selection algorithm
                rv = self.client.get(self.base_url)
                self.assert200(rv)
                winner = self._decide_winner(rv.json['comparison']['answer1_id'], rv.json['comparison']['answer2_id'])
                comparison_submit = self._build_comparison_submit(winner.value)

                rv = self.client.post(self.base_url, data=json.dumps(comparison_submit), content_type='application/json')
                self.assert200(rv)

            comparison_count += 1

            # remove students who have completed all comparisons
            self.student_comparison_count[student.id] += 1
            if self.student_comparison_count[student.id] >= self.MAX_COMPARSIONS:
                indexes = [i for i, s in enumerate(self.students) if student.id == s.id]
                del self.students[indexes[0]]

            if comparison_count % self.COMPARISONS_IN_ROUND == 0:
                round_count += 1

                actual_grades = []
                current_scores = []
                for answer in self.answers:
                    answer_score = AnswerScore.query.filter_by(answer_id=answer.id).first()
                    if answer_score:
                        current_scores.append(answer_score.score)
                        actual_grades.append(self.grade_by_answer_uuid[answer.uuid])

                r_value, pearsonr_p_value = pearsonr(actual_grades, current_scores)
                if r_value >= self.ACCEPTABLE_CORRELATION:
                    break

        self.assertGreaterEqual(r_value, self.ACCEPTABLE_CORRELATION)
        self.assertLessEqual(round_count, self.TOTAL_MAX_ROUNDS)