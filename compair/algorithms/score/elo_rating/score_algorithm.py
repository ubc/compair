from trueskill import Rating, rate_1vs1, setup as ts_setup

from compair.algorithms.score.score_algorithm_base import ScoreAlgorithmBase
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.comparison_winner import ComparisonWinner
from compair.algorithms.scored_object import ScoredObject
from compair.algorithms.exceptions import InvalidWinnerException


class EloAlgorithmWrapper(ScoreAlgorithmBase):
    def __init__(self):
        super().__init__()

        self.storage = {}
        self.opponents = {}
        self.rounds = {}

        # Setup TrueSkill with standard Microsoft settings
        ts_setup(mu=25.0, sigma=8.333, beta=4.166, tau=0.0833, draw_probability=0.0)

    def calculate_score_1vs1(self, key1_scored_object, key2_scored_object, winner, other_comparison_pairs):
        self.storage = {}
        self.opponents = {}

        key1 = key1_scored_object.key
        key2 = key2_scored_object.key

        r1 = key1_scored_object.variable1 or Rating()
        r2 = key2_scored_object.variable1 or Rating()

        if winner == ComparisonWinner.key1:
            r1, r2 = rate_1vs1(r1, r2)
        elif winner == ComparisonWinner.key2:
            r2, r1 = rate_1vs1(r2, r1)
        elif winner == ComparisonWinner.draw:
            r1, r2 = rate_1vs1(r1, r2, drawn=True)
        else:
            raise InvalidWinnerException

        for key in [key1, key2]:
            rating = r1 if key == key1 else r2
            self.opponents[key] = set()
            self.storage[key] = ScoredObject(
                key=key,
                score=rating.mu,
                variable1=rating,
                variable2=None,
                rounds=0,
                opponents=0,
                wins=0,
                loses=0,
            )

        for comparison_pair in (other_comparison_pairs + [ComparisonPair(key1, key2, winner)]):
            cp_key1 = comparison_pair.key1
            cp_key2 = comparison_pair.key2
            cp_winner = comparison_pair.winner

            if cp_key1 in [key1, key2]:
                if cp_winner is None:
                    self._update_rounds_only(cp_key1)
                else:
                    self._update_result_stats(cp_key1, cp_key2, cp_winner == ComparisonWinner.key1, cp_winner == ComparisonWinner.key2)

            if cp_key2 in [key1, key2]:
                if cp_winner is None:
                    self._update_rounds_only(cp_key2)
                else:
                    self._update_result_stats(cp_key2, cp_key1, cp_winner == ComparisonWinner.key2, cp_winner == ComparisonWinner.key1)

        return self.storage[key1], self.storage[key2]

    def calculate_score(self, comparison_pairs):
        self.storage = {}
        self.opponents = {}

        keys = self.get_keys_from_comparison_pairs(comparison_pairs)
        for key in keys:
            default_rating = Rating()
            self.storage[key] = ScoredObject(
                key=key,
                score=default_rating.mu,
                variable1=default_rating,
                variable2=None,
                rounds=0,
                opponents=0,
                wins=0,
                loses=0,
            )
            self.opponents[key] = set()

        for comparison_pair in comparison_pairs:
            key1 = comparison_pair.key1
            key2 = comparison_pair.key2
            winner = comparison_pair.winner

            if winner is None:
                self._update_rounds_only(key1)
                self._update_rounds_only(key2)
                continue

            r1 = self.storage[key1].variable1
            r2 = self.storage[key2].variable1

            if winner == ComparisonWinner.key1:
                r1, r2 = rate_1vs1(r1, r2)
            elif winner == ComparisonWinner.key2:
                r2, r1 = rate_1vs1(r2, r1)
            elif winner == ComparisonWinner.draw:
                r1, r2 = rate_1vs1(r1, r2, drawn=True)
            else:
                raise InvalidWinnerException

            self._update_rating(key1, r1, key2, winner == ComparisonWinner.key1, winner == ComparisonWinner.key2)
            self._update_rating(key2, r2, key1, winner == ComparisonWinner.key2, winner == ComparisonWinner.key1)

        return self.storage

    def _update_rounds_only(self, key):
        rounds = self.storage[key].rounds
        self.storage[key] = self.storage[key]._replace(rounds=rounds + 1)

    def _update_result_stats(self, key, opponent_key, did_win, did_lose):
        self.opponents[key].add(opponent_key)
        wins = self.storage[key].wins
        loses = self.storage[key].loses
        rating = self.storage[key].variable1

        self.storage[key] = ScoredObject(
            key=key,
            score=rating.mu,
            variable1=rating,
            variable2=None,
            rounds=self.storage[key].rounds + 1,
            opponents=len(self.opponents[key]),
            wins=wins + 1 if did_win else wins,
            loses=loses + 1 if did_lose else loses,
        )

    def _update_rating(self, key, new_rating, opponent_key, did_win, did_lose):
        self.opponents[key].add(opponent_key)
        wins = self.storage[key].wins
        loses = self.storage[key].loses

        self.storage[key] = ScoredObject(
            key=key,
            score=new_rating.mu,
            variable1=new_rating,
            variable2=None,
            rounds=self.storage[key].rounds + 1,
            opponents=len(self.opponents[key]),
            wins=wins + 1 if did_win else wins,
            loses=loses + 1 if did_lose else loses,
        )



