import unittest
import mock

from acj.algorithms.pair.random.pair_generator import RandomPairGenerator
from acj.algorithms import ComparisonPair, ScoredObject, InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class TestPairAdaptive(unittest.TestCase):
    pair_algorithm = RandomPairGenerator()

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
            ScoredObject(
                key=1, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []

        with self.assertRaises(InsufficientObjectsForPairException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # User compard all objects error
        scored_objects = [
            ScoredObject(
                key=1, score=0.7, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.2, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = [
            ComparisonPair(1,2,None)
        ]

        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # User compard all objects error
        scored_objects = [
            ScoredObject(
                key=1, score=0.7, variable1=None, variable2=None,
                rounds=4, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.2, variable1=None, variable2=None,
                rounds=4, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.2, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = [
            ComparisonPair(1,2,None),
            ComparisonPair(1,3,None),
            ComparisonPair(1,4,None)
        ]

        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # Returns a comparison pair
        scored_objects = [
            ScoredObject(
                key=1, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            )
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
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=5, score=0.5, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=6, score=0.5, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            )
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
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = [
            ComparisonPair(1,2,None)
        ]
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        self.assertEqual(results.key1, 1)
        self.assertEqual(results.key2, 3)

        # Select opponent randomly (mock shuffle order)
        scored_objects = [
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.7, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.2, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.4, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 2 should be selected since random shuffle is disabled
        self.assertEqual(results.key2, 2)

        # Select opponent randomly (mock shuffle order)
        scored_objects = [
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.2, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.4, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = [
            ComparisonPair(1,2,None)
        ]

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 3 should be selected since random shuffle is disabled
        # and object 2 has already been compared with object 1
        self.assertEqual(results.key2, 3)