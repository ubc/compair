from .pair_generator import RandomPairGenerator

def generate_pair(scored_objects=[], comparison_pairs=[], log=None):
    pair_algorithm = RandomPairGenerator()
    pair_algorithm.log = log
    return pair_algorithm.generate_pair(scored_objects, comparison_pairs)