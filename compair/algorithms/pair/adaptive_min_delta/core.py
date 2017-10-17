from .pair_generator import AdaptiveMinDeltaPairGenerator

def generate_pair(scored_objects=[], comparison_pairs=[], criterion_scores={}, criterion_weights={}, log=None):
    pair_algorithm = AdaptiveMinDeltaPairGenerator()
    pair_algorithm.log = log
    return pair_algorithm.generate_pair(scored_objects, comparison_pairs, criterion_scores, criterion_weights)
