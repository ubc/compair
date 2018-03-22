from abc import ABCMeta, abstractmethod
from compair.algorithms.exceptions import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

class PairGenerator:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.log = None

        # holds comparison pairs the user has already completed
        self.comparison_pairs = []
        self.scored_objects = []

        self.rounds = []
        self.round_objects = {}

    def _debug(self, message):
        if self.log != None:
            self.log.debug(message)

    @abstractmethod
    def generate_pair(self, scored_objects, completed_comparison_pairs):
        pass

    def _setup_rounds(self, comparison_pairs, scored_objects):
        """
        set rounds using all existing scored objects instead (allows up to n(n-1)/2 comparsions)
        forces user to have previously seen all scored objects almost all scored objects at least
        once before they will be assigned a scored object again
        """

        self.comparison_pairs = comparison_pairs
        self.scored_objects = scored_objects
        self.rounds = []
        self.round_objects = {}

        # check valid
        if len(self.scored_objects) < 2:
            raise InsufficientObjectsForPairException

        # check if there are any scored objects that haven't been previously used
        all_keys = set([a.key for a in self.scored_objects])
        used_keys = set([cp.key1 for cp in self.comparison_pairs]) | set([cp.key2 for cp in self.comparison_pairs])
        unused_keys = all_keys - used_keys
        if len(unused_keys) >= 2:
            # set rounds using only unused scored objects (available for up to n/2 comparsions)
            self.scored_objects = [a for a in self.scored_objects if a.key in unused_keys]

        self.rounds = list(set([a.rounds for a in self.scored_objects]))
        self.rounds.sort()

        for scored_object in self.scored_objects:
            round = self.round_objects.setdefault(scored_object.rounds, [])
            round.append(scored_object)

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