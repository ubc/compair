import unittest

from compair.algorithms.score.comparative_judgement.score_algorithm import ComparativeJudgementScoreAlgorithm
from compair.algorithms import ComparisonPair, ScoredObject, ComparisonWinner, InvalidWinnerException

class TestScoreComparitiveJudgement(unittest.TestCase):
    score_algorithm = ComparativeJudgementScoreAlgorithm()

    def setUp(self):
        pass

    def test_calculate_score(self):
        # empty comparison set
        comparisons = []
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 0)

        # one comparison set with key 1 being the winner
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 2)

        self.assertIsInstance(results.get(1), ScoredObject)
        self.assertIsNone(results.get(1).variable2)
        self.assertEqual(results.get(1).rounds, 1)
        self.assertEqual(results.get(1).opponents, 1)
        self.assertEqual(results.get(1).wins, 1)
        self.assertEqual(results.get(1).loses, 0)

        self.assertIsInstance(results.get(2), ScoredObject)
        self.assertIsNone(results.get(2).variable2)
        self.assertEqual(results.get(2).rounds, 1)
        self.assertEqual(results.get(2).opponents, 1)
        self.assertEqual(results.get(2).wins, 0)
        self.assertEqual(results.get(2).loses, 1)

        self.assertGreater(results.get(1).score, results.get(2).score)
        self.assertGreater(results.get(2).score, 0)

        self.assertGreater(results.get(1).variable1, results.get(2).variable1)
        self.assertGreater(results.get(2).variable1, 0)


        # one comparison set with no winner
        # it should only increment rounds and not effect score
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=None)
        ]
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 2)

        self.assertEqual(results.get(1).rounds, 1)
        self.assertEqual(results.get(1).opponents, 0)
        self.assertEqual(results.get(1).wins, 0)
        self.assertEqual(results.get(1).loses, 0)

        self.assertEqual(results.get(2).rounds, 1)
        self.assertEqual(results.get(2).opponents, 0)
        self.assertEqual(results.get(2).wins, 0)
        self.assertEqual(results.get(2).loses, 0)

        self.assertAlmostEqual(results.get(1).score, results.get(2).score)
        self.assertAlmostEqual(results.get(1).variable1, results.get(2).variable1)

        # one comparison set with a draw
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.draw)
        ]
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 2)

        self.assertEqual(results.get(1).rounds, 1)
        self.assertEqual(results.get(1).opponents, 1)
        self.assertEqual(results.get(1).wins, 0)
        self.assertEqual(results.get(1).loses, 0)

        self.assertEqual(results.get(2).rounds, 1)
        self.assertEqual(results.get(2).opponents, 1)
        self.assertEqual(results.get(2).wins, 0)
        self.assertEqual(results.get(2).loses, 0)

        self.assertAlmostEqual(results.get(1).score, results.get(2).score)
        self.assertAlmostEqual(results.get(1).variable1, results.get(2).variable1)

        # comparison set with scores 1 > 2 ~= 3 > 4
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1),
            ComparisonPair(key1=3,key2=4,winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1)
        ]
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 4)

        self.assertEqual(results.get(1).rounds, 2)
        self.assertEqual(results.get(1).opponents, 2)
        self.assertEqual(results.get(1).wins, 2)
        self.assertEqual(results.get(1).loses, 0)

        self.assertEqual(results.get(2).rounds, 2)
        self.assertEqual(results.get(2).opponents, 2)
        self.assertEqual(results.get(2).wins, 1)
        self.assertEqual(results.get(2).loses, 1)

        self.assertEqual(results.get(3).rounds, 2)
        self.assertEqual(results.get(3).opponents, 2)
        self.assertEqual(results.get(3).wins, 1)
        self.assertEqual(results.get(3).loses, 1)

        self.assertEqual(results.get(4).rounds, 2)
        self.assertEqual(results.get(4).opponents, 2)
        self.assertEqual(results.get(4).wins, 0)
        self.assertEqual(results.get(4).loses, 2)

        self.assertGreater(results.get(1).score, results.get(2).score)
        self.assertAlmostEqual(results.get(2).score, results.get(3).score)
        self.assertGreater(results.get(3).score, results.get(4).score)
        self.assertGreater(results.get(4).score, 0)

        self.assertGreater(results.get(1).variable1, results.get(2).variable1)
        self.assertAlmostEqual(results.get(2).variable1, results.get(3).variable1)
        self.assertGreater(results.get(3).variable1, results.get(4).variable1)
        self.assertGreater(results.get(4).variable1, 0)

        # comparison set with scores 1 > 2 ~= 3 > 4 (with draw)
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1),
            ComparisonPair(key1=3,key2=4,winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=3,winner=ComparisonWinner.draw)
        ]
        results = self.score_algorithm.calculate_score(comparisons)

        self.assertEqual(len(results.items()), 4)

        self.assertEqual(results.get(1).rounds, 2)
        self.assertEqual(results.get(1).opponents, 2)
        self.assertEqual(results.get(1).wins, 2)
        self.assertEqual(results.get(1).loses, 0)

        self.assertEqual(results.get(2).rounds, 3)
        self.assertEqual(results.get(2).opponents, 3)
        self.assertEqual(results.get(2).wins, 1)
        self.assertEqual(results.get(2).loses, 1)

        self.assertEqual(results.get(3).rounds, 3)
        self.assertEqual(results.get(3).opponents, 3)
        self.assertEqual(results.get(3).wins, 1)
        self.assertEqual(results.get(3).loses, 1)

        self.assertEqual(results.get(4).rounds, 2)
        self.assertEqual(results.get(4).opponents, 2)
        self.assertEqual(results.get(4).wins, 0)
        self.assertEqual(results.get(4).loses, 2)

        self.assertGreater(results.get(1).score, results.get(2).score)
        self.assertAlmostEqual(results.get(2).score, results.get(3).score)
        self.assertGreater(results.get(3).score, results.get(4).score)
        self.assertGreater(results.get(4).score, 0)

        self.assertAlmostEqual(results.get(2).variable1, results.get(3).variable1)

        # multiple comparisons between same pairs
        comparisons_1 = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        comparisons_2 = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key2)
        ]
        results_1 = self.score_algorithm.calculate_score(comparisons_1)
        results_2 = self.score_algorithm.calculate_score(comparisons_2)

        self.assertEqual(results_2.get(1).opponents, 1)
        self.assertEqual(results_2.get(2).opponents, 1)

        # 1 win should have a higher score than 1 win & 1 lose against same opponent
        self.assertGreater(results_1.get(1).score, results_2.get(1).score)
        # 1 lose should have a lower score than 1 win & 1 lose against same opponent
        self.assertLess(results_1.get(2).score, results_2.get(2).score)

        # 1 win should have a higher expected score than 1 win & 1 lose against same opponent
        self.assertGreater(results_1.get(1).variable1, results_2.get(1).variable1)
        # 1 lose should have a lower expected score than 1 win & 1 lose against same opponent
        self.assertLess(results_1.get(2).variable1, results_2.get(2).variable1)

        comparisons_1 = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        comparisons_2 = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        results_1 = self.score_algorithm.calculate_score(comparisons_1)
        results_2 = self.score_algorithm.calculate_score(comparisons_2)

        # 1 win should have a lower score than 2 wins against same opponent
        self.assertLess(results_1.get(1).score, results_2.get(1).score)
        # 1 lose should have a higher score than 2 loses against same opponent
        self.assertGreater(results_1.get(2).score, results_2.get(2).score)

        # 1 win should have a lower expected score than 2 wins against same opponent
        self.assertLess(results_1.get(1).variable1, results_2.get(1).variable1)
        # 1 lose should have a higher expected score than 2 loses against same opponent
        self.assertGreater(results_1.get(2).variable1, results_2.get(2).variable1)

    def test_calculate_score_1vs1(self):
        # comparative judgement 1 vs 1 does not rely on the variables in scored object
        # it acts very similar to calculate score except limited to the 2 keys provided

        # no winning key error raised
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = None
        comparisons = []

        with self.assertRaises(InvalidWinnerException):
            self.score_algorithm.calculate_score_1vs1(
                key1_scored_object, key2_scored_object, winner, comparisons)

        # one comparison and empty comparison set
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = []
        key1_results, key2_results = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertIsInstance(key1_results, ScoredObject)
        self.assertIsInstance(key1_results.score, float)
        self.assertIsInstance(key1_results.variable1, float)
        self.assertIsNone(key1_results.variable2)
        self.assertEqual(key1_results.rounds, 1)
        self.assertEqual(key1_results.opponents, 1)
        self.assertEqual(key1_results.wins, 1)
        self.assertEqual(key1_results.loses, 0)

        self.assertIsInstance(key2_results, ScoredObject)
        self.assertIsInstance(key2_results.score, float)
        self.assertIsInstance(key2_results.variable1, float)
        self.assertIsNone(key2_results.variable2)
        self.assertEqual(key2_results.rounds, 1)
        self.assertEqual(key2_results.opponents, 1)
        self.assertEqual(key2_results.wins, 0)
        self.assertEqual(key2_results.loses, 1)

        self.assertGreater(key1_results.score, key2_results.score)
        self.assertGreater(key2_results.score, 0)

        self.assertGreater(key1_results.variable1, key2_results.variable1)
        self.assertGreater(key2_results.variable1, 0)

        # one comparison and comparison set without winners
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=None),
            ComparisonPair(key1=1,key2=2,winner=None),
            ComparisonPair(key1=1,key2=2,winner=None)
        ]
        key1_results, key2_results = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertEqual(key1_results.rounds, 4)
        self.assertEqual(key1_results.opponents, 1)
        self.assertEqual(key1_results.wins, 1)
        self.assertEqual(key1_results.loses, 0)

        self.assertEqual(key2_results.rounds, 4)
        self.assertEqual(key2_results.opponents, 1)
        self.assertEqual(key2_results.wins, 0)
        self.assertEqual(key2_results.loses, 1)

        self.assertGreater(key1_results.score, key2_results.score)
        self.assertGreater(key2_results.score, 0)

        self.assertGreater(key1_results.variable1, key2_results.variable1)
        self.assertGreater(key2_results.variable1, 0)

        # one comparison draw
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.draw
        comparisons = []
        key1_results, key2_results = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertIsInstance(key1_results, ScoredObject)
        self.assertIsInstance(key1_results.score, float)
        self.assertIsInstance(key1_results.variable1, float)
        self.assertIsNone(key1_results.variable2)
        self.assertEqual(key1_results.rounds, 1)
        self.assertEqual(key1_results.opponents, 1)
        self.assertEqual(key1_results.wins, 0)
        self.assertEqual(key1_results.loses, 0)

        self.assertIsInstance(key2_results, ScoredObject)
        self.assertIsInstance(key2_results.score, float)
        self.assertIsInstance(key2_results.variable1, float)
        self.assertIsNone(key2_results.variable2)
        self.assertEqual(key2_results.rounds, 1)
        self.assertEqual(key2_results.opponents, 1)
        self.assertEqual(key2_results.wins, 0)
        self.assertEqual(key2_results.loses, 0)

        self.assertAlmostEqual(key1_results.score, key2_results.score)
        self.assertGreater(key2_results.score, 0)

        self.assertAlmostEqual(key1_results.variable1, key2_results.variable1)
        self.assertGreater(key2_results.variable1, 0)

        # comparison set with scores 1 > 2 ~= 3 > 4
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = [
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1)
        ]
        key1_results, key2_results = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertEqual(key1_results.rounds, 2)
        self.assertEqual(key1_results.opponents, 2)
        self.assertEqual(key1_results.wins, 2)
        self.assertEqual(key1_results.loses, 0)

        self.assertEqual(key2_results.rounds, 2)
        self.assertEqual(key2_results.opponents, 2)
        self.assertEqual(key2_results.wins, 1)
        self.assertEqual(key2_results.loses, 1)

        self.assertGreater(key1_results.score, key2_results.score)
        self.assertGreater(key2_results.score, 0)

        self.assertGreater(key1_results.variable1, key2_results.variable1)
        self.assertGreater(key2_results.variable1, 0)

        # comparison set with scores 1 ~= 2 ~= 3 > 4 (with draw)
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.draw
        comparisons = [
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1)
        ]
        key1_results, key2_results = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertEqual(key1_results.rounds, 2)
        self.assertEqual(key1_results.opponents, 2)
        self.assertEqual(key1_results.wins, 1)
        self.assertEqual(key1_results.loses, 0)

        self.assertEqual(key2_results.rounds, 2)
        self.assertEqual(key2_results.opponents, 2)
        self.assertEqual(key2_results.wins, 1)
        self.assertEqual(key2_results.loses, 0)

        self.assertAlmostEqual(key1_results.score, key2_results.score)
        self.assertGreater(key2_results.score, 0)

        self.assertAlmostEqual(key1_results.variable1, key2_results.variable1)
        self.assertGreater(key2_results.variable1, 0)

        # multiple comparisons between same pairs
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = []
        key1_results_1, key2_results_1 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key2
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        key1_results_2, key2_results_2 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        # 1 win should have a higher score than 1 win & 1 lose against same opponent
        self.assertGreater(key1_results_1.score, key1_results_2.score)
        # 1 lose should have a lower score than 1 win & 1 lose against same opponent
        self.assertLess(key2_results_1.score, key2_results_2.score)

        # 1 win should have a higher expected score than 1 win & 1 lose against same opponent
        self.assertGreater(key1_results_1.variable1, key1_results_2.variable1)
        # 1 lose should have a lower expected score than 1 win & 1 lose against same opponent
        self.assertLess(key2_results_1.variable1, key2_results_2.variable1)


        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = []
        key1_results_1, key2_results_1 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = [
            ComparisonPair(key1=1,key2=2,winner=ComparisonWinner.key1)
        ]
        key1_results_2, key2_results_2 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        # 1 win should have a lower score than 2 wins against same opponent
        self.assertLess(key1_results_1.score, key1_results_2.score)
        # 1 lose should have a higher score than 2 loses against same opponent
        self.assertGreater(key2_results_1.score, key2_results_2.score)

        # 1 win should have a lower expected score than 2 wins against same opponent
        self.assertLess(key1_results_1.variable1, key1_results_2.variable1)
        # 1 lose should have a higher expected score than 2 loses against same opponent
        self.assertGreater(key2_results_1.variable1, key2_results_2.variable1)


        # adding unrelated comparisons should not effect 1 vs 1 scores or stats results
        key1_scored_object = ScoredObject(
            key=1, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1
        comparisons = [
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1)
        ]
        key1_results_1, key2_results_1 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        comparisons = [
            ComparisonPair(key1=3,key2=4,winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=3,winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=4,winner=ComparisonWinner.key1)
        ]
        key1_results_2, key2_results_2 = self.score_algorithm.calculate_score_1vs1(
            key1_scored_object, key2_scored_object, winner, comparisons)

        self.assertAlmostEqual(key1_results_1.score, key1_results_2.score)
        self.assertAlmostEqual(key1_results_1.variable1, key1_results_2.variable1)
        self.assertAlmostEqual(key1_results_1.variable2, key1_results_2.variable2)
        self.assertEqual(key1_results_1.rounds, key1_results_2.rounds)
        self.assertEqual(key1_results_1.opponents, key1_results_2.opponents)
        self.assertEqual(key1_results_1.wins, key1_results_2.wins)
        self.assertEqual(key1_results_1.loses, key1_results_2.loses)

        self.assertAlmostEqual(key2_results_1.score, key2_results_2.score)
        self.assertAlmostEqual(key2_results_1.variable1, key2_results_2.variable1)
        self.assertAlmostEqual(key2_results_1.variable2, key2_results_2.variable2)
        self.assertEqual(key2_results_1.rounds, key2_results_2.rounds)
        self.assertEqual(key2_results_1.opponents, key2_results_2.opponents)
        self.assertEqual(key2_results_1.wins, key2_results_2.wins)
        self.assertEqual(key2_results_1.loses, key2_results_2.loses)