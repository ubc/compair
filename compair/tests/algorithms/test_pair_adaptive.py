import unittest
import mock

from compair.algorithms.pair.adaptive.pair_generator import AdaptivePairGenerator
from compair.algorithms import ComparisonPair, ScoredObject, InsufficientObjectsForPairException, \
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
        comparisons = []
        max_comparisons = 6 # n(n-1)/2 = 4*3/2
        for i in range(0, max_comparisons):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            comparisons.append(
                ComparisonPair(results.key1, results.key2, results.key1)
            )

        # if trying to run one more time, should run into all objects compared error
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
        self.assertEqual(results.winner, None)


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

        # Select opponent with closest score (mock shuffle order)
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
        # object 4 should be selected as 0.4 is the closest value to 0.5
        self.assertEqual(results.key2, 4)


        # Select opponent with closest score (mock shuffle order)
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
            ComparisonPair(1,2,None),
            ComparisonPair(3,4,None)
        ]

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 4 should be selected as 0.4 is the closest value to 0.5
        self.assertEqual(results.key2, 4)

        # ensure that all scored objects are seen only once until they have almost all been seen
        # (even number of scored objects)
        scored_objects = [ScoredObject(
            key=index, score=None, variable1=None, variable2=None,
            rounds=0, wins=None, loses=None, opponents=None
        ) for index in range(30)]
        comparisons = []

        used_keys = set()
        all_keys = set(range(30))

        # n/2 comparisons = 15
        for _ in range(15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            # neither key should have been seen before
            self.assertNotIn(results.key1, used_keys)
            self.assertNotIn(results.key2, used_keys)

            comparisons.append(results)
            used_keys.add(results.key1)
            used_keys.add(results.key2)

        self.assertEqual(used_keys, all_keys)

        # remaining comparisons for n(n-1)/2 = 435
        for _ in range(435 - 15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            # both keys should have been seen before
            self.assertIn(results.key1, used_keys)
            self.assertIn(results.key2, used_keys)
            comparisons.append(results)

        # next comparison should be an UserComparedAllObjectsException error
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # make sure all pairs are distinct
        self.assertEqual(
            len(comparisons),
            len(set([tuple(sorted([c.key1, c.key2])) for c in comparisons])))

        # ensure that all scored objects are seen only once until they have almost all been seen
        # (odd number of scored objects)
        scored_objects = [ScoredObject(
            key=index, score=None, variable1=None, variable2=None,
            rounds=0, wins=None, loses=None, opponents=None
        ) for index in range(31)]
        comparisons = []

        used_keys = set()
        all_keys = set(range(31))

        # floor(n/2) comparisons = 15
        for _ in range(15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            # neither key should have been seen before
            self.assertNotIn(results.key1, used_keys)
            self.assertNotIn(results.key2, used_keys)

            comparisons.append(results)
            used_keys.add(results.key1)
            used_keys.add(results.key2)

        # there should be only one key missing
        self.assertEqual(len(all_keys - used_keys), 1)

        # remaining comparisons for n(n-1)/2 = 435
        for _ in range(465 - 15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)
            # both keys should have been seen before
            self.assertIn(results.key1, all_keys)
            self.assertIn(results.key2, all_keys)
            comparisons.append(results)

        # next comparison should be an UserComparedAllObjectsException error
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons)

        # make sure all pairs are distinct
        self.assertEqual(
            len(comparisons),
            len(set([tuple(sorted([c.key1, c.key2])) for c in comparisons])))