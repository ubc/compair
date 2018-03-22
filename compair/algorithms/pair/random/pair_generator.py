import random
import math

from compair.algorithms.pair.pair_generator import PairGenerator
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.comparison_winner import ComparisonWinner
from compair.algorithms.scored_object import ScoredObject
from compair.algorithms.exceptions import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class RandomPairGenerator(PairGenerator):
    def __init__(self):
        PairGenerator.__init__(self)

    def generate_pair(self, scored_objects, comparison_pairs):
        """
        Returns a pair to be compared by the current user.
        If no valid pair can be found, an error is raised
        param scored_objects: list of all scored objects that can be compared
        param comparison_pairs: list of all comparisons completed by the current user.
        """

        self._setup_rounds(comparison_pairs, scored_objects)
        comparison_pair = self._find_pair()

        if comparison_pair == None:
            raise

        return comparison_pair

    def _find_pair(self):
        """
        Returns a comparison pair by matching them up randomly within a round.
        - First key is selected by random within the lowest round possible
        - First key must have a valid opponent with the current user or else its skipped
        - Second key candidates are filters by previous opponents to first key
        - Second key is selected randomly in the lowest round possible
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

        if score_object_1 == None:
            raise UserComparedAllObjectsException

        # step 2: remove invalid opponents
        self._remove_invalid_opponents(score_object_1.key)

        # step 3: select valid second element in pair
        """
        select second element in pair
        second object must be in same round unless:
            - there are no other objects in that round
            - or there are no objects that haven't been compared
              to it by current user already
        """
        for round in self.rounds:
            scored_objects = self.round_objects.get(round, [])

            # randomly sort
            random.shuffle(scored_objects)

            # take the first score object
            if len(scored_objects) > 0:
                score_object_2 = scored_objects[0]
                break

        if score_object_2 == None:
            raise UnknownPairGeneratorException

        return ComparisonPair(
            key1=score_object_1.key,
            key2=score_object_2.key,
            winner=None
        )