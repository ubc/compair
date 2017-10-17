import random
import math

from compair.algorithms.pair.pair_generator import PairGenerator
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.comparison_winner import ComparisonWinner
from compair.algorithms.scored_object import ScoredObject
from compair.algorithms.exceptions import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class AdaptiveMinDeltaPairGenerator(PairGenerator):
    def __init__(self):
        PairGenerator.__init__(self)

        # holds comparison pairs the user has already completed
        self.comparison_pairs = []
        self.scored_objects = []

        self.rounds = []
        self.round_objects = {}

    def generate_pair(self, scored_objects, comparison_pairs, criterion_scores={}, criterion_weights={}):
        """
        Returns a pair to be compared by the current user.
        If no valid pair can be found, an error is raised
        param scored_objects: list of all scored objects that can be compared
        param comparison_pairs: list of all comparisons compelted by the current user.
        param criterion_scores: dictionary of scored_object key to a dictionary of criterion key to score
        param criterion_weights: dictionary of criterion key to weight
        """

        self.comparison_pairs = comparison_pairs
        self.scored_objects = scored_objects
        self.criterion_scores = criterion_scores
        self.criterion_weights = criterion_weights
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

        comparison_pair = self._find_pair()

        if comparison_pair == None:
            raise

        return comparison_pair

    def _find_pair(self):
        """
        Returns an comparison pair by matching them up by criteria score.
        - First key is selected by random within the lowest round possible
        - First key must have a valid opponent with the current user or else its skipped
        - Second key candidates are filters by previous opponents to first key
        - Second key is selected by minimum sum of weighted delta of each criteria
          (if tied, select with closest score. if also tied, choose randomly)
          with the lowest round possible
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
        """
        score = score_object_1.score
        for round in self.rounds:
            scored_objects = self.round_objects.get(round, [])

            """
            sort by followings, in order:
            (1) sum of weighted criterion scores delta;
            (2) absolute diff between the scores;
            (3) a random number
            """
            scored_objects = sorted(scored_objects,
                key=lambda scored_object: (
                    self._criterion_score_delta_sum(score_object_1.key, scored_object.key),
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
            key1=score_object_1.key,
            key2=score_object_2.key,
            winner=None
        )

    def _criterion_score_delta_sum(self, scored_object_key1, scored_object_key2):
        """
        Returns the sum of delta of criterion scores between the the scored obj
        """
        theSum = 0
        criterion_scores_1 = self.criterion_scores.setdefault(scored_object_key1, {})
        criterion_scores_2 = self.criterion_scores.setdefault(scored_object_key2, {})

        criterion_key_list = criterion_scores_1.keys()
        criterion_key_list.extend(criterion_scores_2.keys())
        criterion_key_list = set(criterion_key_list)

        for criterion in criterion_key_list:
            score1 = 0 if criterion_scores_1.setdefault(criterion, 0) == None \
                else criterion_scores_1.get(criterion)
            score2 = 0 if criterion_scores_2.setdefault(criterion, 0) == None \
                else criterion_scores_2.get(criterion)
            weight = 0 if self.criterion_weights.setdefault(criterion, 0) == None \
                else self.criterion_weights.get(criterion)

            theSum += math.fabs((score1 - score2)) * weight

        return theSum

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
