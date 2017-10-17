"""
 Script will generate mock comparisons and output ranking/scoring data after every round of comparisons

 Outputs:
 - for every algorithms: file named 'out'+algorithm name+'.csv' in the scripts folder
 - for every round: display a row with the current rankings, the current scores, and placement stats

 Note: placement stats measure the percentage of answers in the correct range:
 EX: Top 10% answers in:
 the Top 10% ranks = 0.6 = 60% of the Top 10% of answers are in the Top 10% ranks
 the Top 20% ranks = 0.9 = 90% of the Top 10% of answers are in the Top 20% ranks
 the Top 30% ranks = 1.0 = 100% of the Top 10% of answers are in the Top 30% ranks
 the Top 40% ranks = 1.0 = 100% of the Top 10% of answers are in the Top 40% ranks
 the Top 50% ranks = 1.0 = 100% of the Top 10% of answers are in the Top 50% ranks
 This is disabled for now
"""

import csv
import os
import random
import math
import unicodecsv as csv

from compair.algorithms import ComparisonPair, ScoredObject, ComparisonWinner
from compair.algorithms.score import calculate_score_1vs1
from compair.algorithms.pair import generate_pair
from compair.models import PairingAlgorithm, ScoringAlgorithm

CURRENT_FOLDER = os.getcwd() + '/scripts'

TIMES_TO_RUN_PER_ALGORITHM = 3

NUMBER_OF_STUDENTS = 1000
NUMBER_OF_BAD_STUDENTS = 0
NUMBER_OF_ANSWERS = 1000
NUMBER_OF_COMPARISONS_PER_STUDENT = 6
NUMBER_OF_ROUNDS = NUMBER_OF_COMPARISONS_PER_STUDENT * 2
ROUND_LENGTH = NUMBER_OF_ANSWERS / 2

# for all comparison functions value1 and value2 represent the true rank of the answers
ALWAYS_CORRECT = lambda value1, value2: 1
ALWAYS_WRONG = lambda value1, value2: 0
MOSTLY_CORRECT = lambda value1, value2: 0.8
GUESSING = lambda value1, value2: 0.5
# when numbers are closely matched, there should be at worst
# about 50% chance or selecting correctly/incorrectly
# when they are far apart, it should be easier to select the correct answer (a little less than 100%)
CLOSELY_MATCHED_ERRORS = lambda value1, value2: 0.5 + (abs(value1-value2) / NUMBER_OF_ANSWERS / 2)

# add a round # to array to have all comparisons for that round be incorrectly selected
# ex ROUNDS_TO_GIVE_INCORRECT_SELECTION = [3,6] will cause comparisons on round 3 or 6 to always
# select the wrong answer in select_winner
ROUNDS_TO_GIVE_INCORRECT_SELECTION = []

def select_winner(round, student_key, key1, key2):
    correct_answer = ComparisonWinner.key1 if key1 > key2 else ComparisonWinner.key2
    incorrect_answer = ComparisonWinner.key2 if key1 > key2 else ComparisonWinner.key1

    if round in ROUNDS_TO_GIVE_INCORRECT_SELECTION:
        return incorrect_answer
    if student_key in range(1, NUMBER_OF_BAD_STUDENTS+1):
        return incorrect_answer

    # switch function here to one of:
    # ALWAYS_CORRECT, ALWAYS_WRONG, MOSTLY_CORRECT, GUESSING, CLOSELY_MATCHED_ERRORS
    return correct_answer if random.random() <= ALWAYS_CORRECT(key1, key2) else incorrect_answer


# placement stats - measures

def update_bottom_stats(stats, index):
    if index in BOTTOM_10_PERCENT:
        stats[0] += 1
    if index in BOTTOM_20_PERCENT:
        stats[1] += 1
    if index in BOTTOM_30_PERCENT:
        stats[2] += 1
    if index in BOTTOM_40_PERCENT:
        stats[3] += 1
    if index in BOTTOM_50_PERCENT:
        stats[4] += 1

def update_mid_stats(stats, index):
    if index in MID_10_PERCENT:
        stats[0] += 1
    if index in MID_20_PERCENT:
        stats[1] += 1
    if index in MID_30_PERCENT:
        stats[2] += 1
    if index in MID_40_PERCENT:
        stats[3] += 1
    if index in MID_50_PERCENT:
        stats[4] += 1

def update_top_stats(stats, index):
    if index in TOP_10_PERCENT:
        stats[0] += 1
    if index in TOP_20_PERCENT:
        stats[1] += 1
    if index in TOP_30_PERCENT:
        stats[2] += 1
    if index in TOP_40_PERCENT:
        stats[3] += 1
    if index in TOP_50_PERCENT:
        stats[4] += 1

def output_bottom_stats(stats, stat_range):
    return [
        float(stats[0]) / float(min(len(BOTTOM_10_PERCENT), len(stat_range))),
        float(stats[1]) / float(min(len(BOTTOM_20_PERCENT), len(stat_range))),
        float(stats[2]) / float(min(len(BOTTOM_30_PERCENT), len(stat_range))),
        float(stats[3]) / float(min(len(BOTTOM_40_PERCENT), len(stat_range))),
        float(stats[4]) / float(min(len(BOTTOM_50_PERCENT), len(stat_range)))
    ]

def output_mid_stats(stats, stat_range):
    return [
        float(stats[0]) / float(min(len(MID_10_PERCENT), len(stat_range))),
        float(stats[1]) / float(min(len(MID_20_PERCENT), len(stat_range))),
        float(stats[2]) / float(min(len(MID_30_PERCENT), len(stat_range))),
        float(stats[3]) / float(min(len(MID_40_PERCENT), len(stat_range))),
        float(stats[4]) / float(min(len(MID_50_PERCENT), len(stat_range)))
    ]

def output_top_stats(stats, stat_range):
    return [
        float(stats[0]) / float(min(len(TOP_10_PERCENT), len(stat_range))),
        float(stats[1]) / float(min(len(TOP_20_PERCENT), len(stat_range))),
        float(stats[2]) / float(min(len(TOP_30_PERCENT), len(stat_range))),
        float(stats[3]) / float(min(len(TOP_40_PERCENT), len(stat_range))),
        float(stats[4]) / float(min(len(TOP_50_PERCENT), len(stat_range)))
    ]

heading = ["Round"] + ([""] * NUMBER_OF_ANSWERS) + ["Completed?", "Unique Scores"] + ([""] * NUMBER_OF_ANSWERS) + \
    ['B '+str(y)+'0% in B '+str(x)+'0%' for y in range(1,6) for x in range(1,6)] + \
    ['M '+str(y)+'0% in M '+str(x)+'0%' for y in range(1,6) for x in range(1,6)] + \
    ['T '+str(y)+'0% in T '+str(x)+'0%' for y in range(1,6) for x in range(1,6)]


STUDENT_RANGE = range(1, NUMBER_OF_STUDENTS+1)
ANSWER_RANGE = range(1, NUMBER_OF_ANSWERS+1)
BOTTOM_10_PERCENT = range(1, (NUMBER_OF_ANSWERS * 10 / 100)+1)
BOTTOM_20_PERCENT = range(1, (NUMBER_OF_ANSWERS * 20 / 100)+1)
BOTTOM_30_PERCENT = range(1, (NUMBER_OF_ANSWERS * 30 / 100)+1)
BOTTOM_40_PERCENT = range(1, (NUMBER_OF_ANSWERS * 40 / 100)+1)
BOTTOM_50_PERCENT = range(1, (NUMBER_OF_ANSWERS * 50 / 100)+1)

MID_10_PERCENT = range((NUMBER_OF_ANSWERS * 45 / 100), (NUMBER_OF_ANSWERS * 55 / 100)+1)
MID_20_PERCENT = range((NUMBER_OF_ANSWERS * 40 / 100), (NUMBER_OF_ANSWERS * 60 / 100)+1)
MID_30_PERCENT = range((NUMBER_OF_ANSWERS * 35 / 100), (NUMBER_OF_ANSWERS * 65 / 100)+1)
MID_40_PERCENT = range((NUMBER_OF_ANSWERS * 30 / 100), (NUMBER_OF_ANSWERS * 70 / 100)+1)
MID_50_PERCENT = range((NUMBER_OF_ANSWERS * 25 / 100), (NUMBER_OF_ANSWERS * 75 / 100)+1)

TOP_10_PERCENT = range((NUMBER_OF_ANSWERS * 90 / 100)+1, NUMBER_OF_ANSWERS+1)
TOP_20_PERCENT = range((NUMBER_OF_ANSWERS * 80 / 100)+1, NUMBER_OF_ANSWERS+1)
TOP_30_PERCENT = range((NUMBER_OF_ANSWERS * 70 / 100)+1, NUMBER_OF_ANSWERS+1)
TOP_40_PERCENT = range((NUMBER_OF_ANSWERS * 60 / 100)+1, NUMBER_OF_ANSWERS+1)
TOP_50_PERCENT = range((NUMBER_OF_ANSWERS * 50 / 100)+1, NUMBER_OF_ANSWERS+1)

pairing_packages = [
    PairingAlgorithm.adaptive.value,
#    PairingAlgorithm.adaptive_min_delta.value,
#    PairingAlgorithm.random.value
]

scoring_packages = [
#    ScoringAlgorithm.comparative_judgement.value,
    ScoringAlgorithm.elo.value,
#    ScoringAlgorithm.true_skill.value
]
for pairing_package_name in pairing_packages:
    for scoring_package_name in scoring_packages:
        results = []

        for runtime in range(1, TIMES_TO_RUN_PER_ALGORITHM+1):
            answers = []
            for key in ANSWER_RANGE:
                answers.append(ScoredObject(
                    key=key, score=0, variable1=None, variable2=None,
                    rounds=0, opponents=0, wins=0, loses=0
                ))

            students = []
            for key in STUDENT_RANGE:
                students.append({
                    'key': key,
                    'comparisons_left': NUMBER_OF_ROUNDS / 2,
                    'comparisons_completed': []
                })

            comparisons = []

            for round in range(1, NUMBER_OF_ROUNDS+1):
                if len(students) == 0:
                    break

                for comparison_in_round in range(ROUND_LENGTH):
                    if len(students) == 0:
                        break

                    random.shuffle(students)
                    student = students[0]
                    student_comparisons = student['comparisons_completed']

                    comparison_pair = generate_pair(
                        package_name=pairing_package_name,
                        scored_objects=answers,
                        comparison_pairs=student_comparisons
                    )
                    key1 = comparison_pair.key1
                    key2 = comparison_pair.key2
                    winner = select_winner(round, student['key'], key1, key2)
                    comparison_pair = comparison_pair._replace(winner=winner)

                    comparisons.append(comparison_pair)
                    student['comparisons_completed'].append(comparison_pair)
                    student['comparisons_left'] = student['comparisons_left'] - 1
                    if student['comparisons_left'] <= 0:
                        students.remove(student)

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

                # reverse key order on ties so that we know for sure that the
                # score order is eventually correct
                answers = sorted(answers,
                    key=lambda answer: (
                        answer.score,
                        -answer.key
                    )
                )

                completed = True
                previous_key = None

                top_10_stats = [0,0,0,0,0]
                top_20_stats = [0,0,0,0,0]
                top_30_stats = [0,0,0,0,0]
                top_40_stats = [0,0,0,0,0]
                top_50_stats = [0,0,0,0,0]

                mid_10_stats = [0,0,0,0,0]
                mid_20_stats = [0,0,0,0,0]
                mid_30_stats = [0,0,0,0,0]
                mid_40_stats = [0,0,0,0,0]
                mid_50_stats = [0,0,0,0,0]

                bottom_10_stats = [0,0,0,0,0]
                bottom_20_stats = [0,0,0,0,0]
                bottom_30_stats = [0,0,0,0,0]
                bottom_40_stats = [0,0,0,0,0]
                bottom_50_stats = [0,0,0,0,0]

                for index, answer in enumerate(answers):
                    rank_index = index + 1
                    if previous_key != None and previous_key > answer.key:
                        completed = False
                    previous_key = answer.key

                    if answer.key in BOTTOM_10_PERCENT:
                        update_bottom_stats(bottom_10_stats, rank_index)
                    if answer.key in BOTTOM_20_PERCENT:
                        update_bottom_stats(bottom_20_stats, rank_index)
                    if answer.key in BOTTOM_30_PERCENT:
                        update_bottom_stats(bottom_30_stats, rank_index)
                    if answer.key in BOTTOM_40_PERCENT:
                        update_bottom_stats(bottom_40_stats, rank_index)
                    if answer.key in BOTTOM_50_PERCENT:
                        update_bottom_stats(bottom_50_stats, rank_index)

                    if answer.key in MID_10_PERCENT:
                        update_mid_stats(mid_10_stats, rank_index)
                    if answer.key in MID_20_PERCENT:
                        update_mid_stats(mid_20_stats, rank_index)
                    if answer.key in MID_30_PERCENT:
                        update_mid_stats(mid_30_stats, rank_index)
                    if answer.key in MID_40_PERCENT:
                        update_mid_stats(mid_40_stats, rank_index)
                    if answer.key in MID_50_PERCENT:
                        update_mid_stats(mid_50_stats, rank_index)

                    if answer.key in TOP_10_PERCENT:
                        update_top_stats(top_10_stats, rank_index)
                    if answer.key in TOP_20_PERCENT:
                        update_top_stats(top_20_stats, rank_index)
                    if answer.key in TOP_30_PERCENT:
                        update_top_stats(top_30_stats, rank_index)
                    if answer.key in TOP_40_PERCENT:
                        update_top_stats(top_40_stats, rank_index)
                    if answer.key in TOP_50_PERCENT:
                        update_top_stats(top_50_stats, rank_index)

                results.append([str(round)] +
                    [str(answer.key) for answer in answers] +
                    ["Yes" if completed else "No"] +
                    [len(set([answer.score for answer in answers]))] +
                    [str(answer.score) for answer in answers] +
                    output_bottom_stats(bottom_10_stats, BOTTOM_10_PERCENT) +
                    output_bottom_stats(bottom_20_stats, BOTTOM_20_PERCENT) +
                    output_bottom_stats(bottom_30_stats, BOTTOM_30_PERCENT) +
                    output_bottom_stats(bottom_40_stats, BOTTOM_40_PERCENT) +
                    output_bottom_stats(bottom_50_stats, BOTTOM_50_PERCENT) +
                    output_mid_stats(mid_10_stats, MID_10_PERCENT) +
                    output_mid_stats(mid_20_stats, MID_20_PERCENT) +
                    output_mid_stats(mid_30_stats, MID_30_PERCENT) +
                    output_mid_stats(mid_40_stats, MID_40_PERCENT) +
                    output_mid_stats(mid_50_stats, MID_50_PERCENT) +
                    output_top_stats(top_10_stats, TOP_10_PERCENT) +
                    output_top_stats(top_20_stats, TOP_20_PERCENT) +
                    output_top_stats(top_30_stats, TOP_30_PERCENT) +
                    output_top_stats(top_40_stats, TOP_40_PERCENT) +
                    output_top_stats(top_50_stats, TOP_50_PERCENT)
                )

            results.append([""])
            results.append([""])

            # disabled opponent counts for now
            """
            results.append([""])
            results.append(["Opponent counts"])
            results.append([""])
            # count opponents for answers
            for answer in answers:
                opponents = {}
                for comparison in comparisons:
                    if comparison.key1 == answer.key:
                        opponents.setdefault(comparison.key2, 0)
                        opponents[comparison.key2] += 1
                    elif comparison.key2 == answer.key:
                        opponents.setdefault(comparison.key1, 0)
                        opponents[comparison.key1] += 1

                results.append(["key: "+str(answer.key)] + [str(opponent)+ "= "+str(count) for opponent, count in opponents.items()])
            """

        with open(CURRENT_FOLDER+"/out_"+pairing_package_name+"_"+scoring_package_name+".csv", "w+") as csvfile:
            out = csv.writer(csvfile)

            out.writerow(heading)
            for result in results:
                out.writerow(result)



