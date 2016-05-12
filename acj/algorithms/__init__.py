from score_acj import ScoreACJ
        
def calculate_scores(comparison_pairs=[], algorithm="acj", log=None):
    if algorithm == "acj":
        score_algorithm = ScoreACJ(log)
        
        return score_algorithm.calculate_scores(comparison_pairs)
    return []