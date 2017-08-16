import math
from collections import namedtuple

from compair.algorithms.score.score_algorithm_base import ScoreAlgorithmBase
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.comparison_winner import ComparisonWinner
from compair.algorithms.scored_object import ScoredObject

from compair.algorithms.exceptions import InvalidWinnerException

OpponentStats = namedtuple('OpponentStats', ['wins', 'loses'])

class ComparativeJudgementScoreAlgorithm(ScoreAlgorithmBase):
    def __init__(self):
        ScoreAlgorithmBase.__init__(self)

        # storage[key][opponent_key] = OpponentStats
        self.storage = {}
        # storage[key] = # of rounds
        self.rounds = {}


    def calculate_score_1vs1(self, key1_scored_object, key2_scored_object, winner, other_comparison_pairs):
        """
        Calculates the scores for a new 1vs1 comparison without re-calculating all previous scores
        :param key1_scored_object: Contains score parameters for key1
        :param key2_scored_object: Contains score parameters for key2
        :param winner: indicates comparison winner
        :param other_comparison_pairs: Contains all previous comparison_pairs that the 2 keys took part in.
            This is a subset of all comparison pairs and is used to calculate score, round, wins, loses, and opponent counts
        :return: tuple of ScoredObjects (key1, key2)
        """
        self.storage = {}
        self.rounds = {}

        key1 = key1_scored_object.key
        key2 = key2_scored_object.key

        if winner not in [ComparisonWinner.draw, ComparisonWinner.key1, ComparisonWinner.key2]:
            raise InvalidWinnerException

        for key in [key1, key2]:
            self.rounds[key] = 0
            self.storage[key] = {}

        # calculate opponents, wins, loses, rounds for every match for key1 and key2
        for comparison_pair in (other_comparison_pairs + [ComparisonPair(key1, key2, winner)]):
            cp_key1 = comparison_pair.key1
            cp_key2 = comparison_pair.key2
            cp_winner = comparison_pair.winner
            cp_key1_winner = cp_winner == ComparisonWinner.key1
            cp_key2_winner = cp_winner == ComparisonWinner.key2

            if cp_key1 == key1 or cp_key1 == key2:
                self.rounds[cp_key1] += 1

                if cp_winner != None:
                    self._update_win_lose(
                        cp_key1, cp_key2, cp_key1_winner, cp_key2_winner
                    )

            if cp_key2 == key1 or cp_key2 == key2:
                self.rounds[cp_key2] += 1

                if cp_winner != None:
                    self._update_win_lose(
                        cp_key2, cp_key1, cp_key2_winner, cp_key1_winner
                    )

        comparison_results = {}

        for key in [key1, key2]:
            expected_score = self._get_expected_score(key)
            rounds = self.rounds[key]
            opponents = 0
            wins = 0
            loses = 0

            for opponent_key, opponent_stats in self.storage[key].items():
                opponents += 1
                wins += opponent_stats.wins
                loses += opponent_stats.loses

            # an estimate of actual value can be gotten from excepted score / number of opponents
            score = expected_score / (opponents if opponents > 0 else 1)

            comparison_results[key] = ScoredObject(
                key=key,
                score=score,
                variable1=expected_score,
                variable2=None,
                rounds=rounds,
                opponents=opponents,
                wins=wins,
                loses=loses
            )

        return (comparison_results[key1], comparison_results[key2])

    def calculate_score(self, comparison_pairs):
        """
        Calculate scores for a set of comparison_pairs
        :param comparison_pairs: array of comparison_pairs
        :return: dictionary key -> ScoredObject
        """
        self.storage = {}
        self.rounds = {}

        keys = self.get_keys_from_comparison_pairs(comparison_pairs)

        # create default ratings for every available key
        for key in keys:
            self.storage.setdefault(key, {})
            self.rounds.setdefault(key, 0)

        for comparison_pair in comparison_pairs:
            key1 = comparison_pair.key1
            key2 = comparison_pair.key2
            winner = comparison_pair.winner

            key1_winner = winner == ComparisonWinner.key1
            key2_winner = winner == ComparisonWinner.key2

            self.rounds[key1] += 1
            self.rounds[key2] += 1

            # skip incomplete comparisons
            if winner is None:
                continue

            # if there was a winner
            if winner in [ComparisonWinner.key1, ComparisonWinner.key2, ComparisonWinner.draw]:
                # update win/lose counts for both keys
                self._update_win_lose(
                    key1, key2, key1_winner, key2_winner
                )
                self._update_win_lose(
                    key2, key1, key2_winner, key1_winner
                )
            else:
                raise InvalidWinnerException

        comparison_results = {}

        for key, opponents in self.storage.items():
            expected_score = self._get_expected_score(key)
            rounds = self.rounds[key]
            total_opponents = 0
            wins = 0
            loses = 0

            for opponent_key, opponent_stats in opponents.items():
                total_opponents += 1
                wins += opponent_stats.wins
                loses += opponent_stats.loses

            # an estimate of actual value can be gotten from excepted score / number of opponents
            score = expected_score / (total_opponents if total_opponents > 0 else 1)

            comparison_results[key] = ScoredObject(
                key=key,
                score=score,
                variable1=expected_score,
                variable2=None,
                rounds=rounds,
                opponents=total_opponents,
                wins=wins,
                loses=loses
            )

        return comparison_results

    def _update_win_lose(self, key, opponent_key, did_win, did_lose):
        """
        Update number of wins/loses against an opponent
        :param key: Key to update
        :param opponent_key: Key of the opponent
        :param did_win: Weither the key won or lost the round
        """
        opponents = self.storage[key]
        opponent_stats = opponents.setdefault(opponent_key, OpponentStats(0,0))
        if did_win:
            opponents[opponent_key] = opponent_stats._replace(
                wins=opponent_stats.wins + 1
            )
        elif did_lose:
            opponents[opponent_key] = opponent_stats._replace(
                loses=opponent_stats.loses + 1
            )

    def _get_expected_score(self, key):
        """
        Calculate excepted score for a key
        :param key: the key to search for
        :return: excepted score
        """
        opponents = self.storage.get(key, {})

        # see ACJ paper equation 3 for what we're doing here
        # http://www.tandfonline.com/doi/full/10.1080/0969594X.2012.665354
        expected_score = 0.0
        for opponent_key, opponent_stats in opponents.items():
            # skip comparing to self
            if opponent_key == key:
                continue
            wins = opponent_stats.wins
            loses = opponent_stats.loses
            prob_answer_wins = \
                (math.exp(wins - loses)) / \
                (1 + math.exp(wins - loses))
            expected_score += prob_answer_wins
        return expected_score

