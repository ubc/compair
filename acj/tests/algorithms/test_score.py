import unittest

import acj.algorithms
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.comparison_result import ComparisonResult
        
class TestAlgorithms(unittest.TestCase):
    logger = None

    def setUp(self):
        self.comparisons = [
            ComparisonPair(1,2,winning_key=1),
            ComparisonPair(1,3,winning_key=1),
            ComparisonPair(2,3,winning_key=2)
        ]

    def test_calculate_scores(self):
        # test acj score algorithm
        self.algorithm = "acj"
        
        results = acj.algorithms.calculate_scores(
            self.comparisons, self.algorithm, self.logger
        )
        self.assertEqual(len(results.items()), 3)
        
        self.assertIsInstance(results.get(1), ComparisonResult)
        self.assertEqual(results.get(1).total_rounds, 2)
        self.assertEqual(results.get(1).total_opponents, 2)
        self.assertEqual(results.get(1).total_wins, 2)
        self.assertEqual(results.get(1).total_loses, 0)
        
        self.assertIsInstance(results.get(2), ComparisonResult)
        self.assertEqual(results.get(2).total_rounds, 2)
        self.assertEqual(results.get(2).total_opponents, 2)
        self.assertEqual(results.get(2).total_wins, 1)
        self.assertEqual(results.get(2).total_loses, 1)
        
        self.assertIsInstance(results.get(3), ComparisonResult)
        self.assertEqual(results.get(3).total_rounds, 2)
        self.assertEqual(results.get(3).total_opponents, 2)
        self.assertEqual(results.get(3).total_wins, 0)
        self.assertEqual(results.get(3).total_loses, 2)
        
        
        

if __name__ == '__main__':
    unittest.main()
