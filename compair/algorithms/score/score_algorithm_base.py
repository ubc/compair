from abc import ABCMeta, abstractmethod, abstractproperty


class ScoreAlgorithmBase:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.log = None

    def _debug(self, message):
        if self.log != None:
            self.log.debug(message)

    def get_keys_from_comparison_pairs(self, comparison_pairs):
        keys = set()

        for comparison_pair in comparison_pairs:
            keys.add(comparison_pair.key1)
            keys.add(comparison_pair.key2)

        return keys


    @abstractmethod
    def calculate_score(self, comparison_pairs):
        pass

    @abstractmethod
    def calculate_score_1vs1(self, key1_score_parameters, key2_score_parameters, winner, other_comparison_pairs):
        pass
