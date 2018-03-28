"""
 Script will run scoring algorithms against set of csv input comaprisons

 Excepts:
 - input file to be named input.csv in scripts folder
 - input file rows to be structure: "key1, key2, winner"

 Outputs:
 - for every algorithms: file named 'out'+algorithm name+'.csv' in the scripts folder
 - output file rows are structured "id, score, rounds, wins, normalized score"

"""
import unicodecsv as csv
import os

from compair.algorithms import ComparisonPair, ScoredObject, ComparisonWinner
from compair.algorithms.score import calculate_score
from compair.models.score_algorithm import ScoringAlgorithm
import unicodecsv as csv

KEY1 = 0
KEY2 = 1
WINNER = 2

CURRENT_FOLDER = os.getcwd() + '/scripts'

comparisons = []

with open(CURRENT_FOLDER+'/input.csv', 'rU') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        if row:
            comparisons.append(ComparisonPair(
                int(row[KEY1]), int(row[KEY2]), ComparisonWinner(row[WINNER])
            ))

packages = [
    ScoringAlgorithm.comparative_judgement.value,
    ScoringAlgorithm.elo.value,
    ScoringAlgorithm.true_skill.value
]
for package_name in packages:
    results = calculate_score(
        package_name=package_name,
        comparison_pairs=comparisons
    )

    with open(CURRENT_FOLDER+"/out_"+package_name+".csv", "w+") as csvfile:
        out = csv.writer(csvfile)

        out.writerow(["id", "score", "rounds", "wins", "normal score"])

        for key, result in results.items():
            out.writerow([result.key, result.score,
                result.rounds, result.wins, ""])



