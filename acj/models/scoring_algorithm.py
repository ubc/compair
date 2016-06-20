from enum import Enum

class ScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating"
    true_skill = "true_skill_rating"
