"""
    Algorithm Tests
    uses mocked unit testing ComPAIR backend
"""

import concurrencytest
import json
import random
import math
import unittest
import os
import unicodecsv as csv
from scipy.stats import spearmanr, pearsonr, kendalltau
import numpy
from enum import Enum

from data.fixtures.test_data import ComparisonTestData
from compair.models import Answer, Comparison, \
    WinningAnswer, AnswerScore, AnswerCriterionScore, \
    PairingAlgorithm, ScoringAlgorithm
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db
from compair.tests import test_app_settings
from compair import create_app

CURRENT_FOLDER = os.getcwd() + '/scripts'
REPETITIONS = 1 #1000
ACCEPTABLE_CORRELATION = 0.8
NUMBER_OF_ANSWERS = 40
CONCURRENCY = 4
#allows using same grade distribution across all tests
ACTUAL_GRADES = None #numpy.random.normal(0.78, 0.1, NUMBER_OF_ANSWERS)

class WinnerSelector(Enum):
    always_correct = "always_correct"
    correct_with_error = "correct_with_error"
    guessing = "guessing"
    closely_matched_errors = "closely_matched_errors"

scoring_algorithms = [ScoringAlgorithm.true_skill, ScoringAlgorithm.elo] #ScoringAlgorithm.comparative_judgement
pairing_algorithms = [PairingAlgorithm.adaptive_min_delta] #PairingAlgorithm.adaptive, PairingAlgorithm.random
winner_selectors = [
    (WinnerSelector.always_correct, 1.0, "100% Correct"),
    (WinnerSelector.correct_with_error, 0.9, "90% Correct"),
    (WinnerSelector.correct_with_error, 0.8, "80% Correct"),
    (WinnerSelector.correct_with_error, 0.7, "70% Correct"),
    (WinnerSelector.correct_with_error, 0.6, "60% Correct"),
    (WinnerSelector.closely_matched_errors, 0.05, "Sigma 0.05"),
    (WinnerSelector.closely_matched_errors, 0.06, "Sigma 0.06"),
    (WinnerSelector.closely_matched_errors, 0.07, "Sigma 0.07"),
    (WinnerSelector.closely_matched_errors, 0.08, "Sigma 0.08"),
    (WinnerSelector.closely_matched_errors, 0.09, "Sigma 0.09"),
    (WinnerSelector.closely_matched_errors, 0.10, "Sigma 0.10"),
]

REPORT_FOLDER = "{}/report correlation {}% answers {} repetitions {}".format(
    CURRENT_FOLDER, int(ACCEPTABLE_CORRELATION*100), NUMBER_OF_ANSWERS, REPETITIONS
)

if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

if ACTUAL_GRADES:
    grade_path = "{}/{}".format(REPORT_FOLDER, "actual grades.csv")
    with open(grade_path, "w+") as csvfile:
        out = csv.writer(csvfile)
        out.writerow(ACTUAL_GRADES)

class AlgorithmValidityTests(ComPAIRAPITestCase):
    SCORING_ALGORITHM = ScoringAlgorithm.elo
    PAIRING_ALGORITHM = PairingAlgorithm.adaptive_min_delta
    NUMBER_OF_ANSWERS = 100
    REPORT_PATH = None
    WINNER_SELECTOR = WinnerSelector.always_correct
    CORRECT_RATE = 1.0
    ACTUAL_GRADES = None

    def create_app(self):
        settings = test_app_settings.copy()
        settings['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+self._sqlite_db()
        app = create_app(settings_override=settings)
        return app

    def setUp(self):
        # remove existing sqlite db if exists
        self._delete_sqlite_db()

        # get a new seed (needed for ConcurrentTestSuite so they don't produce the same results)
        random.seed()
        numpy.random.seed()

        super(AlgorithmValidityTests, self).setUp()
        self.data = ComparisonTestData()

        self.MAX_COMPARSIONS = (NUMBER_OF_ANSWERS - 1) * (NUMBER_OF_ANSWERS - 2) / 2
        self.TOTAL_MAX_ROUNDS = 50
        self.COMPARISONS_IN_ROUND = math.ceil(NUMBER_OF_ANSWERS / 2)
        # stop after lowest of total comparisons possible or 100 rounds worth of comparisons are complete
        self.TOTAL_MAX_COMPARISONS = min(
            self.COMPARISONS_IN_ROUND * self.TOTAL_MAX_ROUNDS,
            NUMBER_OF_ANSWERS * self.MAX_COMPARSIONS
        )

        self.course = self.data.create_course()
        self.instructor = self.data.create_instructor()
        self.data.enrol_instructor(self.instructor, self.course)
        self.assignment = self.data.create_assignment_in_comparison_period(
            self.course, self.instructor,
            number_of_comparisons=self.MAX_COMPARSIONS,
            scoring_algorithm=AlgorithmValidityTests.SCORING_ALGORITHM,
            pairing_algorithm=AlgorithmValidityTests.PAIRING_ALGORITHM)

        self.students = []
        self.answers = []
        self.grade_by_answer_uuid = {}
        actual_grades = ACTUAL_GRADES
        if not actual_grades:
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

    def tearDown(self):
        self._delete_sqlite_db()

    def _sqlite_db(self):
        return 'test_comparison'+str(os.getpid())+'.db'

    def _delete_sqlite_db(self):
        file_path = os.path.join(os.getcwd(), 'compair', self._sqlite_db())
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(e)

    def _decide_winner(self, answer1_uuid, answer2_uuid):
        answer1_grade = self.grade_by_answer_uuid[answer1_uuid]
        answer2_grade = self.grade_by_answer_uuid[answer2_uuid]

        if AlgorithmValidityTests.WINNER_SELECTOR == WinnerSelector.always_correct:
            return self.always_correct(answer1_grade, answer2_grade)
        elif AlgorithmValidityTests.WINNER_SELECTOR == WinnerSelector.guessing:
            return self.guessing()
        elif AlgorithmValidityTests.WINNER_SELECTOR == WinnerSelector.correct_with_error:
            return self.correct_with_error(answer1_grade, answer2_grade, AlgorithmValidityTests.CORRECT_RATE)
        elif AlgorithmValidityTests.WINNER_SELECTOR == WinnerSelector.closely_matched_errors:
            return self.closely_matched_errors(answer1_grade, answer2_grade, AlgorithmValidityTests.CORRECT_RATE)
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

        results = []

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
                #rho, spearmanr_p_value = spearmanr(actual_grades, current_scores)
                #tau, kendalltau_p_value = kendalltau(actual_grades, current_scores)
                results.append(str(r_value))
                #results.append(str(rho))
                #results.append(str(tau))
                #print("Round {} ----------- pearsonr={} value=={} spearmanr={} value=={} kendalltau={} value=={}".format(
                #    round_count, r_value, pearsonr_p_value, rho, spearmanr_p_value, tau, kendalltau_p_value
                #))

                if r_value >= ACCEPTABLE_CORRELATION:
                    break

        with open(AlgorithmValidityTests.REPORT_PATH, "a") as csvfile:
            out = csv.writer(csvfile)
            out.writerow(results)

for (winner_selector, correct_rate, correct_rate_str) in winner_selectors:
    for pairing_algorithm in pairing_algorithms:
        for scoring_algorithm in scoring_algorithms:
            file_name = "{} {} {}.csv".format(
                scoring_algorithm.value, pairing_algorithm.value, correct_rate_str
            )
            report_path = "{}/{}".format(REPORT_FOLDER, file_name)
            with open(report_path, "w+") as csvfile:
                out = csv.writer(csvfile)
                heading = []
                for index in range(1, 101):
                    heading.append("Round {}".format(index))
                out.writerow(heading)

            AlgorithmValidityTests.SCORING_ALGORITHM = scoring_algorithm
            AlgorithmValidityTests.PAIRING_ALGORITHM = pairing_algorithm
            AlgorithmValidityTests.REPORT_PATH = report_path
            AlgorithmValidityTests.WINNER_SELECTOR = winner_selector
            AlgorithmValidityTests.CORRECT_RATE = correct_rate

            loader = unittest.TestLoader()
            test = loader.loadTestsFromName('test_random_students_perform_comparisons', AlgorithmValidityTests)

            suite = unittest.TestSuite()
            for _ in range(REPETITIONS):
                suite.addTest(test)

            runner = unittest.TextTestRunner()
            concurrent_suite = concurrencytest.ConcurrentTestSuite(suite, concurrencytest.fork_for_tests(CONCURRENCY))
            print("Starting Test for {}".format(file_name))
            runner.run(concurrent_suite)
            print("Finished Test for {}".format(file_name))
            print("")