import unittest

from acj.algorithms import ComparisonPair, ScoredObject
from acj.algorithms.pair import generate_pair

class TestPair(unittest.TestCase):

    def setUp(self):
        self.scored_objects = [
            ScoredObject(1, 0.7, 1),
            ScoredObject(2, 0.2, 1),
            ScoredObject(3, None, 0),
            ScoredObject(4, None, 0),
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


if __name__ == '__main__':
    unittest.main()
