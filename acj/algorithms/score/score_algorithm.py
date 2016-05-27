from abc import ABCMeta, abstractmethod, abstractproperty


class ScoreAlgorithm:
    __metaclass__ = ABCMeta
    
    def __init__(self):
        self.log = None
        
    def _debug(self, message):
        if self.log != None:
            self.log.debug(message)
    
    @abstractmethod
    def calculate_score(self, comparison_pairs):
        pass
    
    