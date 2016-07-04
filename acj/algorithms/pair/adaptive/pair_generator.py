import random
import math

from acj.algorithms.pair.pair_generator import PairGenerator
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.scored_object import ScoredObject
from acj.algorithms.exceptions import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class AdaptivePairGenerator(PairGenerator):
    def __init__(self):
        PairGenerator.__init__(self)

        # holds comparison pairs the user has already completed
        self.comparison_pairs = []
        self.scored_objects = []

        self.rounds = []
        # round_objects[round_number] = [ScoredObject]
        self.round_objects = {}


    def generate_pair(self, scored_objects, comparison_pairs):
        """
        Returns a pair to be compared by the current user.
        If no valid pair can be found, an error is raised
        param scored_objects: list of all scored objects that can be compared
        param comparison_pairs: list of all comparisons compelted by the current user.
        """

        self.comparison_pairs = comparison_pairs
        self.scored_objects = scored_objects
        self.rounds = []
        self.round_objects = {}

        # change None value scores to zero
        for (index, scored_object) in enumerate(self.scored_objects):
            if scored_object.score == None:
                self.scored_objects[index] = scored_object._replace(score=0)

        self.rounds = list(set([a.rounds for a in self.scored_objects]))
        self.rounds.sort()

        for scored_object in self.scored_objects:
            round = self.round_objects.setdefault(scored_object.rounds, [])
            round.append(scored_object)

        # check valid
        if len(self.scored_objects) < 2:
            raise InsufficientObjectsForPairException

        if self._has_compared_all():
            raise UserComparedAllObjectsException

        comparison_pair = self._find_pair()

        if comparison_pair == None:
            raise

        return comparison_pair

    def _has_compared_all(self):
        """
        Returns True if the user has already compared all objects, False otherwise.
        """
        compared_keys = set()
        for comparison_pair in self.comparison_pairs:
            compared_keys.add(comparison_pair.key1)
            compared_keys.add(comparison_pair.key2)

        all_keys = set([scored_object.key for scored_object in self.scored_objects])

        # some comparison keys may have been soft deleted hence we need to use
        # the set subtraction operation instead of comparing sizes
        all_keys -= compared_keys

        return not all_keys


    def _find_pair(self):
        """
        Returns an comparison pair by matching them up by score.
        - First key is selected by random within the lowest round possible
        - First key must have a valid opponent with the current user or else its skipped
        - Second key canidates are filters by previous opponents to first key
        - Second key is selected by most similar score (randomly if tied) in the lowest round possible
        """
        score_object_1 = None
        score_object_2 = None

        # step 1: select valid first element in pair
        for round in self.rounds:
            scored_objects = self.round_objects.get(round, [])

            # place objects in round in random order
            random.shuffle(scored_objects)

            # find a scored_object that has a valid opponent
            for index, scored_object in enumerate(scored_objects):
                if self._has_valid_opponent(scored_object.key):
                    score_object_1 = scored_object
                    break

            if score_object_1 != None:
                break

        # Note this should be caught in get_pair
        if score_object_1 == None:
            raise UserComparedAllObjectsException

        # step 2: remove invalid opponents
        self._remove_invalid_opponents(score_object_1.key)

        # step 3: select valid second element in pair
        """
        select second element in pair
        second object must be in same round unless:
            - there are no other objects in that round
            - or there are no objects that haven't been comapred
              to it by current user already
        """
        score = score_object_1.score
        for round in self.rounds:
            scored_objects = self.round_objects.get(round, [])

            # sort by absolute difference between first element's score
            # and order similar scored objects randomly
            scored_objects = sorted(scored_objects,
                key=lambda scored_object: (
                    math.fabs(score - scored_object.score),
                    random.random()
                )
            )

            # take the first score object
            if len(scored_objects) > 0:
                score_object_2 = scored_objects[0]
                break

        if score_object_2 == None:
            raise UnknownPairGeneratorException

        return ComparisonPair(
            score_object_1.key, score_object_2.key, winning_key=None
        )


    def _has_valid_opponent(self, key):
        """
        Returns True if scored object has at least one other scored object it
        hasn't been compared to by the current user, False otherwise.
        """
        compared_keys = set()
        compared_keys.add(key)
        for comparison_pair in self.comparison_pairs:
            # add opponents of key to compared_keys set
            if comparison_pair.key1 == key:
                compared_keys.add(comparison_pair.key2)
            elif comparison_pair.key2 == key:
                compared_keys.add(comparison_pair.key1)

        all_keys = set([scored_object.key for scored_object in self.scored_objects])

        # some comparison keys may have been soft deleted hence we need to use
        # the set subtraction operation instead of comparing sizes
        all_keys -= compared_keys

        return all_keys

    def _remove_invalid_opponents(self, key):
        """
        removes key and all opponents of key from score objects lists
        """
        filter_keys = set()
        filter_keys.add(key)
        for comparison_pair in self.comparison_pairs:
            # add opponents of key to compared_keys set
            if comparison_pair.key1 == key:
                filter_keys.add(comparison_pair.key2)
            elif comparison_pair.key2 == key:
                filter_keys.add(comparison_pair.key1)

        self.scored_objects = [so for so in self.scored_objects if so.key not in filter_keys]

        # reinit round_objects
        self.round_objects = {}
        for scored_object in self.scored_objects:
            round = self.round_objects.setdefault(scored_object.rounds, [])
            round.append(scored_object)