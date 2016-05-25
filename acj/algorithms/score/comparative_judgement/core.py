from score_algorithm import ComparativeJudgementScoreAlgorithm

def calculate_score(comparison_pairs=[], log=None):
    score_algorithm = ComparativeJudgementScoreAlgorithm()
    score_algorithm.log = log
    return score_algorithm.calculate_score(comparison_pairs)