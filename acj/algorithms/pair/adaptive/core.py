from .pair_generator import AdaptivePairGenerator

def generate_pair(scored_objects=[], comparison_pairs=[], log=None):
    pair_algorithm = AdaptivePairGenerator()
    pair_algorithm.log = log
    return pair_algorithm.generate_pair(scored_objects, comparison_pairs)