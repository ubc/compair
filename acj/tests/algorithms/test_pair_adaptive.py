import unittest
import mock

from acj.algorithms.pair.adaptive.pair_generator import AdaptivePairGenerator
from acj.algorithms import ComparisonPair, ScoredObject, InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException
        
class TestPairAdaptive(unittest.TestCase):
    pair_algorithm = AdaptivePairGenerator()

    def setUp(self):
        pass
        
    @mock.patch('random.shuffle')
    def test_generate_pair(self, mock_shuffle):
        # empty scored objects set
        scored_objects = []
        comparisons = []
        
        with self.assertRaises(InsufficientObjectsForPairException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            
        # not enough scored objects for comparison (only 1 scored object)
        scored_objects = [
            ScoredObject(1, None, 0)
        ]
        comparisons = []
        
        with self.assertRaises(InsufficientObjectsForPairException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            
        # User compard all objects error
        scored_objects = [
            ScoredObject(1, 0.7, 1),
            ScoredObject(2, 0.2, 1)
        ]
        comparisons = [
            ComparisonPair(1,2,winning_key=1)
        ]
        
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            
        # User compard all objects error
        scored_objects = [
            ScoredObject(1, 0.7, 4),
            ScoredObject(2, 0.2, 4),
            ScoredObject(3, 0.5, 3),
            ScoredObject(4, 0.2, 3)
        ]
        comparisons = [
            ComparisonPair(1,2,winning_key=1),
            ComparisonPair(1,3,winning_key=1),
            ComparisonPair(1,4,winning_key=1)
        ]
        
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            
        # Returns a comparison pair
        scored_objects = [
            ScoredObject(1, None, 0),
            ScoredObject(2, None, 0)
        ]
        comparisons = []
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
        
        self.assertIsInstance(results, ComparisonPair)
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        
        self.assertEqual(min_key, 1)
        self.assertEqual(max_key, 2)
        self.assertEqual(results.winning_key, None)
        
        
        # Selects lowest round objects first
        scored_objects = [
            ScoredObject(1, 0.5, 2),
            ScoredObject(2, 0.5, 2),
            ScoredObject(3, 0.5, 2),
            ScoredObject(4, 0.5, 2),
            ScoredObject(5, 0.5, 1),
            ScoredObject(6, 0.5, 1)
        ]
        comparisons = []
        
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
        
        # 5 & 6 should be selected as the lowest valid round objects
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        self.assertEqual(min_key, 5)
        self.assertEqual(max_key, 6)
        
        # Can select previously compared object but not with same opponent
        scored_objects = [
            ScoredObject(1, 0.5, 2),
            ScoredObject(2, 0.5, 2),
            ScoredObject(3, 0.9, 3)
        ]
        comparisons = [
            ComparisonPair(1,2,winning_key=1)
        ]
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
        
        self.assertEqual(results.key1, 1)
        self.assertEqual(results.key2, 3)
        
        # Select opponent with closest score (mock shuffle order)
        scored_objects = [
            ScoredObject(1, 0.5, 3),
            ScoredObject(2, 0.7, 3),
            ScoredObject(3, 0.2, 3),
            ScoredObject(4, 0.4, 3)
        ]
        comparisons = []
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
        
        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1) 
        # object 4 should be selected as 0.4 is the closest value to 0.5
        self.assertEqual(results.key2, 4) 
        
        
        # Select opponent with closest score (mock shuffle order)
        scored_objects = [
            ScoredObject(1, 0.5, 3),
            ScoredObject(2, 0.5, 3),
            ScoredObject(3, 0.2, 3),
            ScoredObject(4, 0.4, 3)
        ]
        comparisons = [
            ComparisonPair(1,2,winning_key=1)
        ]
        
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
        
        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1) 
        # object 4 should be selected as 0.4 is the closest value to 0.5 
        self.assertEqual(results.key2, 4) 
        
        

if __name__ == '__main__':
    unittest.main()
