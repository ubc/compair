import unittest

from compair.algorithms import ComparisonPair, ScoredObject, ComparisonWinner
from compair.algorithms.score import calculate_score, calculate_score_1vs1

class TestScore(unittest.TestCase):

    def setUp(self):
        self.comparisons = [
            ComparisonPair(key1=1,key2=2, winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=3, winner=ComparisonWinner.key1),
            ComparisonPair(key1=2,key2=3, winner=ComparisonWinner.key1)
        ]

    def test_calculate_score(self):
        # test comparitive judgement score algorithm
        self.package_name = "comparative_judgement"

        results = calculate_score(
            package_name=self.package_name,
            comparison_pairs=self.comparisons
        )

        self.assertEqual(len(results.items()), 3)

        self.assertIsInstance(results.get(1), ScoredObject)
        self.assertIsInstance(results.get(1).score, float)
        self.assertIsInstance(results.get(1).variable1, float)
        self.assertIsNone(results.get(1).variable2)
        self.assertEqual(results.get(1).rounds, 2)
        self.assertEqual(results.get(1).opponents, 2)
        self.assertEqual(results.get(1).wins, 2)
        self.assertEqual(results.get(1).loses, 0)

        self.assertIsInstance(results.get(2), ScoredObject)
        self.assertIsInstance(results.get(2).score, float)
        self.assertIsInstance(results.get(2).variable1, float)
        self.assertIsNone(results.get(2).variable2)
        self.assertEqual(results.get(2).rounds, 2)
        self.assertEqual(results.get(2).opponents, 2)
        self.assertEqual(results.get(2).wins, 1)
        self.assertEqual(results.get(2).loses, 1)

        self.assertIsInstance(results.get(3), ScoredObject)
        self.assertIsInstance(results.get(3).score, float)
        self.assertIsInstance(results.get(3).variable1, float)
        self.assertIsNone(results.get(3).variable2)
        self.assertEqual(results.get(3).rounds, 2)
        self.assertEqual(results.get(3).opponents, 2)
        self.assertEqual(results.get(3).wins, 0)
        self.assertEqual(results.get(3).loses, 2)

        # test elo rating algorithm
        self.package_name = "elo_rating"

        results = calculate_score(
            package_name=self.package_name,
            comparison_pairs=self.comparisons
        )

        self.assertEqual(len(results.items()), 3)

        self.assertIsInstance(results.get(1), ScoredObject)
        self.assertIsInstance(results.get(1).score, float)
        self.assertIsInstance(results.get(1).variable1, float)
        self.assertIsNone(results.get(1).variable2)
        self.assertEqual(results.get(1).rounds, 2)
        self.assertEqual(results.get(1).opponents, 2)
        self.assertEqual(results.get(1).wins, 2)
        self.assertEqual(results.get(1).loses, 0)

        self.assertIsInstance(results.get(2), ScoredObject)
        self.assertIsInstance(results.get(2).score, float)
        self.assertIsInstance(results.get(2).variable1, float)
        self.assertIsNone(results.get(2).variable2)
        self.assertEqual(results.get(2).rounds, 2)
        self.assertEqual(results.get(2).opponents, 2)
        self.assertEqual(results.get(2).wins, 1)
        self.assertEqual(results.get(2).loses, 1)

        self.assertIsInstance(results.get(3), ScoredObject)
        self.assertIsInstance(results.get(3).score, float)
        self.assertIsInstance(results.get(3).variable1, float)
        self.assertIsNone(results.get(3).variable2)
        self.assertEqual(results.get(3).rounds, 2)
        self.assertEqual(results.get(3).opponents, 2)
        self.assertEqual(results.get(3).wins, 0)
        self.assertEqual(results.get(3).loses, 2)

        # test true skill rating algorithm
        self.package_name = "true_skill_rating"

        results = calculate_score(
            package_name=self.package_name,
            comparison_pairs=self.comparisons
        )

        self.assertEqual(len(results.items()), 3)

        self.assertIsInstance(results.get(1), ScoredObject)
        self.assertIsInstance(results.get(1).score, float)
        self.assertIsInstance(results.get(1).variable1, float)
        self.assertIsInstance(results.get(1).variable2, float)
        self.assertEqual(results.get(1).rounds, 2)
        self.assertEqual(results.get(1).opponents, 2)
        self.assertEqual(results.get(1).wins, 2)
        self.assertEqual(results.get(1).loses, 0)

        self.assertIsInstance(results.get(2), ScoredObject)
        self.assertIsInstance(results.get(2).score, float)
        self.assertIsInstance(results.get(2).variable1, float)
        self.assertIsInstance(results.get(2).variable2, float)
        self.assertEqual(results.get(2).rounds, 2)
        self.assertEqual(results.get(2).opponents, 2)
        self.assertEqual(results.get(2).wins, 1)
        self.assertEqual(results.get(2).loses, 1)

        self.assertIsInstance(results.get(3), ScoredObject)
        self.assertIsInstance(results.get(3).score, float)
        self.assertIsInstance(results.get(3).variable1, float)
        self.assertIsInstance(results.get(3).variable2, float)
        self.assertEqual(results.get(3).rounds, 2)
        self.assertEqual(results.get(3).opponents, 2)
        self.assertEqual(results.get(3).wins, 0)
        self.assertEqual(results.get(3).loses, 2)

    def test_calculate_score_1vs1(self):
        self.comparisons = [
            ComparisonPair(key1=1,key2=2, winner=ComparisonWinner.key1),
            ComparisonPair(key1=1,key2=3, winner=ComparisonWinner.key1)
        ]

        # test comparative judgement score algorithm
        self.package_name = "comparative_judgement"

        key1_scored_object = ScoredObject(
            key=2, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=3, score=None, variable1=None, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1

        key2_results, key3_results = calculate_score_1vs1(
            package_name=self.package_name,
            key1_scored_object=key1_scored_object,
            key2_scored_object=key2_scored_object,
            winner=winner,
            other_comparison_pairs=self.comparisons
        )

        self.assertIsInstance(key2_results, ScoredObject)
        self.assertIsInstance(key2_results.score, float)
        self.assertIsInstance(key2_results.variable1, float)
        self.assertIsNone(key2_results.variable2)
        self.assertEqual(key2_results.rounds, 2)
        self.assertEqual(key2_results.opponents, 2)
        self.assertEqual(key2_results.wins, 1)
        self.assertEqual(key2_results.loses, 1)

        self.assertIsInstance(key3_results, ScoredObject)
        self.assertIsInstance(key3_results.score, float)
        self.assertIsInstance(key3_results.variable1, float)
        self.assertIsNone(key3_results.variable2)
        self.assertEqual(key3_results.rounds, 2)
        self.assertEqual(key3_results.opponents, 2)
        self.assertEqual(key3_results.wins, 0)
        self.assertEqual(key3_results.loses, 2)

        # test elo rating algorithm
        self.package_name = "elo_rating"

        key1_scored_object = ScoredObject(
            key=2, score=1395, variable1=1395, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=3, score=1396, variable1=1396, variable2=None,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1

        key2_results, key3_results = calculate_score_1vs1(
            package_name=self.package_name,
            key1_scored_object=key1_scored_object,
            key2_scored_object=key2_scored_object,
            winner=winner,
            other_comparison_pairs=self.comparisons
        )

        self.assertIsInstance(key2_results, ScoredObject)
        self.assertIsInstance(key2_results.score, float)
        self.assertIsInstance(key2_results.variable1, float)
        self.assertIsNone(key2_results.variable2)
        self.assertEqual(key2_results.rounds, 2)
        self.assertEqual(key2_results.opponents, 2)
        self.assertEqual(key2_results.wins, 1)
        self.assertEqual(key2_results.loses, 1)

        self.assertIsInstance(key3_results, ScoredObject)
        self.assertIsInstance(key3_results.score, float)
        self.assertIsInstance(key3_results.variable1, float)
        self.assertIsNone(key3_results.variable2)
        self.assertEqual(key3_results.rounds, 2)
        self.assertEqual(key3_results.opponents, 2)
        self.assertEqual(key3_results.wins, 0)
        self.assertEqual(key3_results.loses, 2)

        # test true skill rating algorithm
        self.package_name = "true_skill_rating"


        key1_scored_object = ScoredObject(
            key=2, score=-0.909, variable1=20.604, variable2=7.171,
            rounds=None, wins=None, loses=None, opponents=None
        )
        key2_scored_object = ScoredObject(
            key=3, score=-0.058, variable1=21.542, variable2=7.200,
            rounds=None, wins=None, loses=None, opponents=None
        )
        winner = ComparisonWinner.key1

        key2_results, key3_results = calculate_score_1vs1(
            package_name=self.package_name,
            key1_scored_object=key1_scored_object,
            key2_scored_object=key2_scored_object,
            winner=winner,
            other_comparison_pairs=self.comparisons
        )

        self.assertIsInstance(key2_results, ScoredObject)
        self.assertIsInstance(key2_results.score, float)
        self.assertIsInstance(key2_results.variable1, float)
        self.assertIsInstance(key2_results.variable2, float)
        self.assertEqual(key2_results.rounds, 2)
        self.assertEqual(key2_results.opponents, 2)
        self.assertEqual(key2_results.wins, 1)
        self.assertEqual(key2_results.loses, 1)

        self.assertIsInstance(key3_results, ScoredObject)
        self.assertIsInstance(key3_results.score, float)
        self.assertIsInstance(key3_results.variable1, float)
        self.assertIsInstance(key3_results.variable2, float)
        self.assertEqual(key3_results.rounds, 2)
        self.assertEqual(key3_results.opponents, 2)
        self.assertEqual(key3_results.wins, 0)
        self.assertEqual(key3_results.loses, 2)