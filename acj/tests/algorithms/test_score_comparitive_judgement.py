import unittest

from acj.algorithms.score_acj import ScoreACJ
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.comparison_result import ComparisonResult
        
class TestScoreACJ(unittest.TestCase):
    score_algorithm = ScoreACJ(None)

    def setUp(self):
        pass

    def test_calculate_scores(self):
        # empty comparison set
        comparisons = []
        results = self.score_algorithm.calculate_scores(comparisons)
        
        self.assertEqual(len(results.items()), 0)
        
        # one comparison set with key 1 being the winner
        comparisons = [
            ComparisonPair(1,2,winning_key=1)
        ]
        results = self.score_algorithm.calculate_scores(comparisons)
            
        self.assertEqual(len(results.items()), 2)
        
        self.assertIsInstance(results.get(1), ComparisonResult)
        self.assertEqual(results.get(1).total_rounds, 1)
        self.assertEqual(results.get(1).total_opponents, 1)
        self.assertEqual(results.get(1).total_wins, 1)
        self.assertEqual(results.get(1).total_loses, 0)
        
        self.assertIsInstance(results.get(2), ComparisonResult)
        self.assertEqual(results.get(2).total_rounds, 1)
        self.assertEqual(results.get(2).total_opponents, 1)
        self.assertEqual(results.get(2).total_wins, 0)
        self.assertEqual(results.get(2).total_loses, 1)
        
        self.assertGreater(results.get(1).score, results.get(2).score)
        self.assertGreater(results.get(2).score, 0)
        
        # one comparison set with no winner
        comparisons = [
            ComparisonPair(1,2,winning_key=None)
        ]
        results = self.score_algorithm.calculate_scores(comparisons)
            
        self.assertEqual(len(results.items()), 2)
        
        self.assertEqual(results.get(1).total_rounds, 1)
        self.assertEqual(results.get(1).total_opponents, 1)
        self.assertEqual(results.get(1).total_wins, 0)
        self.assertEqual(results.get(1).total_loses, 0)
        
        self.assertEqual(results.get(2).total_rounds, 1)
        self.assertEqual(results.get(2).total_opponents, 1)
        self.assertEqual(results.get(2).total_wins, 0)
        self.assertEqual(results.get(2).total_loses, 0)
        
        self.assertAlmostEqual(results.get(1).score, results.get(2).score)
        self.assertGreater(results.get(2).score, 0)
        
        # comparison set with scores 1 > 2 ~= 3 > 4
        comparisons = [
            ComparisonPair(1,2, winning_key=1),
            ComparisonPair(3,4, winning_key=3),
            ComparisonPair(1,3, winning_key=1),
            ComparisonPair(2,4, winning_key=2)
        ]
        results = self.score_algorithm.calculate_scores(comparisons)
        
        self.assertEqual(len(results.items()), 4)
        
        self.assertEqual(results.get(1).total_rounds, 2)
        self.assertEqual(results.get(1).total_opponents, 2)
        self.assertEqual(results.get(1).total_wins, 2)
        self.assertEqual(results.get(1).total_loses, 0)
        
        self.assertEqual(results.get(2).total_rounds, 2)
        self.assertEqual(results.get(2).total_opponents, 2)
        self.assertEqual(results.get(2).total_wins, 1)
        self.assertEqual(results.get(2).total_loses, 1)
        
        self.assertEqual(results.get(3).total_rounds, 2)
        self.assertEqual(results.get(3).total_opponents, 2)
        self.assertEqual(results.get(3).total_wins, 1)
        self.assertEqual(results.get(3).total_loses, 1)
        
        self.assertEqual(results.get(4).total_rounds, 2)
        self.assertEqual(results.get(4).total_opponents, 2)
        self.assertEqual(results.get(4).total_wins, 0)
        self.assertEqual(results.get(4).total_loses, 2)
        
        self.assertGreater(results.get(1).score, results.get(2).score)
        self.assertAlmostEqual(results.get(2).score, results.get(3).score)
        self.assertGreater(results.get(3).score, results.get(4).score)
        self.assertGreater(results.get(4).score, 0)
        
        # comparison set with no winner
        comparisons = [
            ComparisonPair(1,2, winning_key=None)
        ]
        results = self.score_algorithm.calculate_scores(comparisons)
        
        self.assertEqual(len(results.items()), 2)
        
        self.assertEqual(results.get(1).total_rounds, 1)
        self.assertEqual(results.get(1).total_opponents, 1)
        self.assertEqual(results.get(1).total_wins, 0)
        self.assertEqual(results.get(1).total_loses, 0)
        
        self.assertEqual(results.get(2).total_rounds, 1)
        self.assertEqual(results.get(2).total_opponents, 1)
        self.assertEqual(results.get(2).total_wins, 0)
        self.assertEqual(results.get(2).total_loses, 0)
        
        self.assertAlmostEqual(results.get(1).score, results.get(2).score)
        self.assertGreater(results.get(2).score, 0)
        
        
        # multiple comparisons between same pairs
        comparisons_1 = [
            ComparisonPair(1,2, winning_key=1)
        ]
        comparisons_2 = [
            ComparisonPair(1,2, winning_key=1),
            ComparisonPair(1,2, winning_key=2)
        ]
        results_1 = self.score_algorithm.calculate_scores(comparisons_1)
        results_2 = self.score_algorithm.calculate_scores(comparisons_2)
        
        self.assertEqual(results_2.get(1).total_opponents, 1)
        self.assertEqual(results_2.get(2).total_opponents, 1)
        
        # 1 win should have a higher score than 1 win & 1 lose against same opponent
        self.assertGreater(results_1.get(1).score, results_2.get(1).score)
        # 1 lose should have a lower score than 1 win & 1 lose against same opponent
        self.assertLess(results_1.get(2).score, results_2.get(2).score)
        
        comparisons_1 = [
            ComparisonPair(1,2, winning_key=1)
        ]
        comparisons_2 = [
            ComparisonPair(1,2, winning_key=1),
            ComparisonPair(1,2, winning_key=1)
        ]
        results_1 = self.score_algorithm.calculate_scores(comparisons_1)
        results_2 = self.score_algorithm.calculate_scores(comparisons_2)
        
        # 1 win should have a lower score than 2 wins against same opponent
        self.assertLess(results_1.get(1).score, results_2.get(1).score)
        # 1 lose should have a higher score than 2 loses against same opponent
        self.assertGreater(results_1.get(2).score, results_2.get(2).score)
        

if __name__ == '__main__':
    unittest.main()
