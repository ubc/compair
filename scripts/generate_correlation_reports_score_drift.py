"""
 Script will generate mock comparisons and output ranking/scoring data after every round of comparisons

 uses Scoring and Pairing algorithms directly without using the full ComPAIR backend

 Outputs:
 - for every algorithms: file named 'out'+algorithm name+'.csv' in the scripts folder
 - for every round: display a row with the current rankings, the current scores, and placement stats
"""
import os
import random
import math
import unicodecsv as csv
from scipy.stats import spearmanr, pearsonr, kendalltau
import numpy
import multiprocessing
from enum import Enum

from compair.algorithms import ComparisonPair, ScoredObject, ComparisonWinner
from compair.algorithms.score import calculate_score_1vs1
from compair.algorithms.pair import generate_pair
from compair.models import PairingAlgorithm, ScoringAlgorithm

CURRENT_FOLDER = os.getcwd() + '/scripts'

REPETITIONS = 15
NUMBER_OF_STUDENTS = 100
NUMBER_OF_ANSWERS = 100
NUMBER_OF_COMPARISONS_PER_STUDENT = 2
NUMBER_OF_ROUNDS = NUMBER_OF_COMPARISONS_PER_STUDENT * 2
ROUND_LENGTH = NUMBER_OF_ANSWERS / 2
CONCURRENCY = 4
ACTUAL_GRADES = numpy.random.normal(0.78, 0.1, NUMBER_OF_ANSWERS)

class WinnerSelector(Enum):
    always_correct = "always_correct"
    correct_with_error = "correct_with_error"
    guessing = "guessing"
    closely_matched_errors = "closely_matched_errors"

pairing_packages = [
    #PairingAlgorithm.adaptive.value,
    PairingAlgorithm.adaptive_min_delta.value,
    #PairingAlgorithm.random.value
]

scoring_packages = [
    #ScoringAlgorithm.comparative_judgement.value,
    ScoringAlgorithm.elo.value,
    ScoringAlgorithm.true_skill.value
]

winner_selectors = [
    (WinnerSelector.always_correct, 1.0, "100% Correct"),
    (WinnerSelector.closely_matched_errors, 0.05, "Sigma 0.05"),
    (WinnerSelector.closely_matched_errors, 0.06, "Sigma 0.06"),
    (WinnerSelector.closely_matched_errors, 0.07, "Sigma 0.07"),
    (WinnerSelector.closely_matched_errors, 0.08, "Sigma 0.08"),
    (WinnerSelector.closely_matched_errors, 0.09, "Sigma 0.09"),
    (WinnerSelector.closely_matched_errors, 0.10, "Sigma 0.10"),
    (WinnerSelector.correct_with_error, 0.9, "90% Correct"),
    (WinnerSelector.correct_with_error, 0.8, "80% Correct"),
    (WinnerSelector.correct_with_error, 0.7, "70% Correct"),
    (WinnerSelector.correct_with_error, 0.6, "60% Correct"),
]

REPORT_FOLDER = "{}/score drift report comparisons {} answers {} students {} repetitions {}".format(
    CURRENT_FOLDER, NUMBER_OF_COMPARISONS_PER_STUDENT, NUMBER_OF_ANSWERS, NUMBER_OF_STUDENTS, REPETITIONS
)
if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

def _decide_winner(winner_selector, correct_rate, key1_grade, key2_grade):
    if winner_selector == WinnerSelector.always_correct:
        return always_correct(key1_grade, key2_grade)
    elif winner_selector == WinnerSelector.guessing:
        return guessing()
    elif winner_selector == WinnerSelector.correct_with_error:
        return correct_with_error(key1_grade, key2_grade, correct_rate)
    elif winner_selector == WinnerSelector.closely_matched_errors:
        return closely_matched_errors(key1_grade, key2_grade, correct_rate)
    else:
        raise Exception()

def always_correct(value1, value2):
    return correct_with_error(value1, value2, 1.0)

def correct_with_error(value1, value2, correct_rate):
    if value1 == value2:
        return guessing()
    correct_answer = ComparisonWinner.key1 if value1 > value2 else ComparisonWinner.key2
    incorrect_answer = ComparisonWinner.key1 if value1 < value2 else ComparisonWinner.key2

    return correct_answer if random.random() <= correct_rate else incorrect_answer

def guessing():
    return ComparisonWinner.key1 if random.random() <= 0.5 else ComparisonWinner.key2

def closely_matched_errors(value1, value2, sigma):
    # make the actual values of answers fuzzy (represents perceived value errors)
    fuzzy_value1 = numpy.random.normal(value1, sigma, 1)[0]
    fuzzy_value2 = numpy.random.normal(value2, sigma, 1)[0]
    # return the correct winner using fuzzy perceived values
    return always_correct(fuzzy_value1, fuzzy_value2)

def _run_helper(args):
    return _run(*args)

def _run(file_path, pairing_package_name, scoring_package_name, winner_selector, correct_rate, actual_grades, repetition_count):
    random.seed()
    numpy.random.seed()

    while repetition_count < REPETITIONS:
        grade_by_answer_key = {}
        answers = []
        results = []
        for key, grade in enumerate(actual_grades):
            grade_by_answer_key[key+1] = grade
            answers.append(ScoredObject(
                key=key+1, score=0, variable1=None, variable2=None,
                rounds=0, opponents=0, wins=0, loses=0
            ))

        students = []
        for key in range(NUMBER_OF_STUDENTS):
            students.append({
                'key': key,
                'comparisons_left': NUMBER_OF_COMPARISONS_PER_STUDENT,
                'comparisons_completed': []
            })

        comparisons = []

        for round_count in range(1, NUMBER_OF_ROUNDS+1):
            if len(students) == 0:
                break

            for comparison_in_round in range(ROUND_LENGTH):
                if len(students) == 0:
                    break

                student = random.choice(students)
                student_comparisons = student['comparisons_completed']

                comparison_pair = generate_pair(
                    package_name=pairing_package_name,
                    scored_objects=answers,
                    comparison_pairs=student_comparisons
                )
                key1 = comparison_pair.key1
                key1_grade = grade_by_answer_key[key1]
                key2 = comparison_pair.key2
                key2_grade = grade_by_answer_key[key2]

                winner = _decide_winner(
                    winner_selector, correct_rate,
                    key1_grade, key2_grade
                )
                comparison_pair = comparison_pair._replace(winner=winner)

                comparisons.append(comparison_pair)
                student['comparisons_completed'].append(comparison_pair)
                student['comparisons_left'] -= 1
                if student['comparisons_left'] <= 0:
                    indexes = [i for i, s in enumerate(students) if student['key'] == s['key']]
                    del students[indexes[0]]

                index1 = next(index for index, answer in enumerate(answers) if answer.key == key1)
                index2 = next(index for index, answer in enumerate(answers) if answer.key == key2)

                result1, results2 = calculate_score_1vs1(
                    package_name=scoring_package_name,
                    key1_scored_object=answers[index1],
                    key2_scored_object=answers[index2],
                    winner=winner,
                    other_comparison_pairs=comparisons
                )
                answers[index1] = result1
                answers[index2] = results2

            current_scores = [answer.score for answer in answers]

            r_value, pearsonr_p_value = pearsonr(ACTUAL_GRADES, current_scores)
            results.append(str(r_value))
            #print("Round {} ----------- pearsonr={} value=={}".format(
            #    round_count, r_value, pearsonr_p_value
            #))

        with open(file_path, "a") as csvfile:
            out = csv.writer(csvfile)
            out.writerow(results)

        # prepare for next run
        repetition_count += 1
        actual_grades = [answer.score for answer in answers]


repetition_count = 0
job_args = []
for (winner_selector, correct_rate, correct_rate_str) in winner_selectors:
    for pairing_package_name in pairing_packages:
        for scoring_package_name in scoring_packages:
            file_name = "{} {} {}.csv".format(
                scoring_package_name, pairing_package_name, correct_rate_str
            )
            file_path = "{}/{}".format(REPORT_FOLDER, file_name)
            with open(file_path, "w+") as csvfile:
                out = csv.writer(csvfile)
                out.writerow(["Round {}".format(index) for index in range(1, NUMBER_OF_ROUNDS+1)])

            args = (file_path, pairing_package_name, scoring_package_name, winner_selector, correct_rate, ACTUAL_GRADES, repetition_count)
            job_args.append(args)

print("Starting {} jobs".format(len(job_args)))

pool = multiprocessing.Pool(processes=CONCURRENCY)
pool.map(_run_helper, job_args)

print("")
print("Finished!")