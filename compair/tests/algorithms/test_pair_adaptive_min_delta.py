import unittest
import mock

from compair.algorithms.pair.adaptive_min_delta.pair_generator import AdaptiveMinDeltaPairGenerator
from compair.algorithms import ComparisonPair, ScoredObject, InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class TestPairMinDelta(unittest.TestCase):
    pair_algorithm = AdaptiveMinDeltaPairGenerator()

    def setUp(self):
        pass

    @mock.patch('random.shuffle')
    @mock.patch('random.random')
    def test_generate_pair(self, mock_shuffle, mock_random):
        ##
        # empty scored objects set
        scored_objects = []
        comparisons = []
        criterion_scores = {}
        criterion_weights = { 'c1': 0.4, 'c2': 0.6 }

        with self.assertRaises(InsufficientObjectsForPairException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

        ##
        # not enough scored objects for comparison (only 1 scored object)
        scored_objects = [
            ScoredObject(
                key=1, score=None, variable1=None, variable2=None,
                rounds=0, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        criterion_scores = { 1: { 'c1': 100, 'c2': 200} }
        criterion_weights = { 'c1': 0.4, 'c2': 0.6 }

        with self.assertRaises(InsufficientObjectsForPairException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

        ##
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
        criterion_scores = {
            1: { 'c1': 100, 'c2': 200 },
            2: { 'c1': 110, 'c2': 220 }
        }
        criterion_weights = {
            'c1': 0.7, 'c2': 0.3
        }

        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

        ##
        # User compared all objects error
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
        criterion_scores = {
            1: { 'c1': 100, 'c2': 200 },
            2: { 'c1': 100, 'c2': 200 },
            3: { 'c1': 100, 'c2': 200 },
            4: { 'c1': 100, 'c2': 200 }
        }
        criterion_weights = {
            'c1': 0.7, 'c2': 0.3
        }

        max_comparisons = 6 # n(n-1)/2 = 4*3/2
        for i in range(0, max_comparisons):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)
            comparisons.append(
                ComparisonPair(results.key1, results.key2, results.key1)
            )

        # if trying to run one more time, should run into all objects compared error
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

        ##
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
        criterion_scores = {
            1: { 'c1': 100, 'c2': 200 },
            2: { 'c1': 110, 'c2': 220 }
        }
        criterion_weights = {
            'c1': 0.7, 'c2': 0.3
        }
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        self.assertIsInstance(results, ComparisonPair)
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])

        self.assertEqual(min_key, 1)
        self.assertEqual(max_key, 2)
        self.assertEqual(results.winner, None)

        ##
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
        criterion_scores = {
            1: { 'c1': 100, 'c2': 200 },
            2: { 'c1': 100, 'c2': 200 },
            3: { 'c1': 100, 'c2': 200 },
            4: { 'c1': 100, 'c2': 200 },
            5: { 'c1': 100, 'c2': 200 },
            6: { 'c1': 100, 'c2': 200 }
        }
        criterion_weights = {
            'c1': 0.7, 'c2': 0.3
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # 5 & 6 should be selected as the lowest valid round objects
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        self.assertEqual(min_key, 5)
        self.assertEqual(max_key, 6)

        ##
        # Selects lowest criterion score delta
        scored_objects = [
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        criterion_scores = {
            1: { 'c1': 100, 'c2': 100 },
            2: { 'c1': 110, 'c2': 110 },
            3: { 'c1': 115, 'c2': 100 }
        }
        criterion_weights = {
            'c1': 0.7, 'c2': 0.3
        }
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # 1 should be selected first as it has lowest round.
        # it should be paired with 2 as the criterion score delta is lowest.
        # (10 * 0.7 + 10 * 0.3 = 10 which is less than 15 * 0.7 = 10.5)
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        self.assertEqual(min_key, 1)
        self.assertEqual(max_key, 2)

        ##
        # Selects closest score when criterion score deta are the same
        scored_objects = [
            ScoredObject(
                key=1, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.4, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        criterion_scores = {
            1: { 'c1': 11, 'c2': 21 },
            2: { 'c1': 11, 'c2': 21 },
            3: { 'c1': 10.1, 'c2': 20.2 },
            4: { 'c1': 11, 'c2': 21 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # 3 should be selected first as it has lowest round.
        # it should be paired with 4 as the score (0.4) is closer to 0.5.
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        self.assertEqual(min_key, 3)
        self.assertEqual(max_key, 4)

        ##
        # Selects "randomly" if both criterion scores and scores are the same
        scored_objects = [
            ScoredObject(
                key=1, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=2, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=3, score=0.9, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.9, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        criterion_scores = {
            1: { 'c1': 11, 'c2': 21 },
            2: { 'c1': 11, 'c2': 21 },
            3: { 'c1': 11, 'c2': 21 },
            4: { 'c1': 11, 'c2': 21 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # 4 should be selected first as it has lowest round.
        # it should be paired with either 1, 2 or 3.
        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        # 1 should alwasys be selected because of mock random.random
        self.assertEqual(min_key, 1)
        self.assertEqual(max_key, 4)

        ##
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
        criterion_scores = {
            1: { 'c1': 10.1, 'c2': 20.2 },
            2: { 'c1': 10.1, 'c2': 20.2 },
            3: { 'c1': 10.1, 'c2': 20.2 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        min_key = min([results.key1, results.key2])
        max_key = max([results.key1, results.key2])
        self.assertEqual(min_key, 1)
        self.assertEqual(max_key, 3)

        ##
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
        criterion_scores = {
            1: { 'c1': 10.1, 'c2': 20.2 },
            2: { 'c1': 10.1, 'c2': 20.2 },
            3: { 'c1': 10.1, 'c2': 20.2 },
            4: { 'c1': 10.1, 'c2': 20.2 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 4 should be selected as 0.4 is the closest value to 0.5
        self.assertEqual(results.key2, 4)

        ##
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
        criterion_scores = {
            1: { 'c1': 10.1, 'c2': 20.2 },
            2: { 'c1': 10.1, 'c2': 20.2 },
            3: { 'c1': 10.1, 'c2': 20.2 },
            4: { 'c1': 10.1, 'c2': 20.2 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 4 should be selected as 0.4 is the closest value to 0.5 (object 2 already compared, so wont be considered)
        self.assertEqual(results.key2, 4)

        ##
        # Select opponent with min delta
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
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = []
        criterion_scores = {
            1: { 'c1': 10.1, 'c2': 20.2 },
            2: { 'c1': 10.2, 'c2': 20.3 },
            3: { 'c1': 20.1, 'c2': 20.2 },
            4: { 'c1': 10.1, 'c2': 30.2 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }
        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 2 should be selected as it has the min weighted criterion score delta
        self.assertEqual(results.key2, 2)

        ##
        # Select opponent with closest min delta
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
                key=3, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=4, score=0.5, variable1=None, variable2=None,
                rounds=3, wins=None, loses=None, opponents=None
            )
        ]
        comparisons = [
            ComparisonPair(1,2,None),
            ComparisonPair(3,4,None)
        ]
        criterion_scores = {
            1: { 'c1': 10.1, 'c2': 20.2 },
            2: { 'c1': 10.2, 'c2': 20.3 },
            3: { 'c1': 20.1, 'c2': 20.2 },
            4: { 'c1': 10.1, 'c2': 30.2 }
        }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # object 1 should be selected since random shuffle is disabled
        self.assertEqual(results.key1, 1)
        # object 3 should be selected as it has the min weighted criterion scores delta
        # after object 2 (which is already compared)
        self.assertEqual(results.key2, 3)

        ##
        # Select from long list
        scored_objects = [
            ScoredObject(
                key=1, score=0.5, variable1=None, variable2=None,
                rounds=1, wins=None, loses=None, opponents=None
            ),
            ScoredObject(
                key=500, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            )
        ]
        for keyNum in range (2, 500):
            scored_objects.append(ScoredObject(
                key=keyNum, score=0.5, variable1=None, variable2=None,
                rounds=2, wins=None, loses=None, opponents=None
            ))
        comparisons = []
        criterion_scores = {
            1: { 'c1': 10, 'c2': 20 },
            500: { 'c1': 15, 'c2': 24.9 }
        }
        for keyNum in range(2, 500):
            criterion_scores[keyNum] = { 'c1': 15, 'c2': 25 }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
            criterion_scores, criterion_weights)

        # object 1 should be selected since it has lowest round
        self.assertEqual(results.key1, 1)
        # object 500 should be select as it as the lowest criterion score delta
        self.assertEqual(results.key2, 500)

        # ensure that all scored objects are seen only once until they have almost all been seen
        # (even number of scored objects)
        scored_objects = [ScoredObject(
            key=index, score=None, variable1=None, variable2=None,
            rounds=0, wins=None, loses=None, opponents=None
        ) for index in range(30)]
        comparisons = []
        criterion_scores = {}
        for key in range(30):
            criterion_scores[key] = { 'c1': None, 'c2': None }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        used_keys = set()
        all_keys = set(range(30))

        # n/2 comparisons = 15
        for _ in range(15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)
            # neither key should have been seen before
            self.assertNotIn(results.key1, used_keys)
            self.assertNotIn(results.key2, used_keys)

            comparisons.append(results)
            used_keys.add(results.key1)
            used_keys.add(results.key2)

        self.assertEqual(used_keys, all_keys)

        # remaining comparisons for n(n-1)/2 = 435
        for _ in range(435 - 15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)
            # both keys should have been seen before
            self.assertIn(results.key1, used_keys)
            self.assertIn(results.key2, used_keys)
            comparisons.append(results)

        # next comparison should be an UserComparedAllObjectsException error
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

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
        criterion_scores = {}
        for key in range(30):
            criterion_scores[key] = { 'c1': None, 'c2': None }
        criterion_weights = {
            'c1': 0.4, 'c2': 0.6
        }

        used_keys = set()
        all_keys = set(range(31))

        # floor(n/2) comparisons = 15
        for _ in range(15):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)
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
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)
            # both keys should have been seen before
            self.assertIn(results.key1, all_keys)
            self.assertIn(results.key2, all_keys)
            comparisons.append(results)

        # next comparison should be an UserComparedAllObjectsException error
        with self.assertRaises(UserComparedAllObjectsException):
            results = self.pair_algorithm.generate_pair(scored_objects, comparisons,
                criterion_scores, criterion_weights)

        # make sure all pairs are distinct
        self.assertEqual(
            len(comparisons),
            len(set([tuple(sorted([c.key1, c.key2])) for c in comparisons])))