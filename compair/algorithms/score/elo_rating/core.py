from .score_algorithm import EloAlgorithmWrapper

def calculate_score(comparison_pairs=[], log=None):
    score_algorithm = EloAlgorithmWrapper()
    score_algorithm.log = log
    return score_algorithm.calculate_score(comparison_pairs)

def calculate_score_1vs1(key1_scored_object, key2_scored_object, winner, other_comparison_pairs=[], log=None):
    score_algorithm = EloAlgorithmWrapper()
    score_algorithm.log = log
    return score_algorithm.calculate_score_1vs1(key1_scored_object, key2_scored_object, winner, other_comparison_pairs)