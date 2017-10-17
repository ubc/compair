from abc import ABCMeta, abstractmethod

class PairGenerator:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.log = None

    def _debug(self, message):
        if self.log != None:
            self.log.debug(message)

    @abstractmethod
    def generate_pair(self, scored_objects, completed_comparison_pairs, criterion_scores={}, criterion_weights={}):
        pass

