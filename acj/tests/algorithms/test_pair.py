import unittest

from acj.algorithms import ComparisonPair, ScoredObject
from acj.algorithms.pair import generate_pair

class TestPair(unittest.TestCase):

    def setUp(self):
        self.scored_objects = [
            ScoredObject(
                key=1, score=0.7, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.2, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            )
        ]

        self.comparisons = []

    def test_generate_pair(self):
        # test adaptive pair algorithm
        self.package_name = "adaptive"

        results = generate_pair(
            package_name=self.package_name,
            scored_objects=self.scored_objects,
            comparison_pairs=self.comparisons
        )

        self.assertIsInstance(results, ComparisonPair)
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])

        # round zero items should be selected
        self.assertEqual(min_key, 3)
        self.assertEqual(max_key, 4)
        self.assertEqual(results.winning_key, None)

        # test random pair algorithm
        self.package_name = "random"

        results = generate_pair(
            package_name=self.package_name,
            scored_objects=self.scored_objects,
            comparison_pairs=self.comparisons
        )

        self.assertIsInstance(results, ComparisonPair)
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])

        # round zero items should be selected
        self.assertEqual(min_key, 3)
        self.assertEqual(max_key, 4)
        self.assertEqual(results.winning_key, None)