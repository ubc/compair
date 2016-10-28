import math
from collections import namedtuple

from compair.algorithms.score.score_algorithm_base import ScoreAlgorithmBase
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.scored_object import ScoredObject

from compair.algorithms.exceptions import InvalidWinningKeyException

OpponentStats = namedtuple('OpponentStats', ['wins', 'loses'])

class ComparativeJudgementScoreAlgorithm(ScoreAlgorithmBase):
    def __init__(self):
        ScoreAlgorithmBase.__init__(self)

        # storage[key][opponent_key] = OpponentStats
        self.storage = {}
        # storage[key] = # of rounds
        self.rounds = {}


    def calculate_score_1vs1(self, key1_scored_object, key2_scored_object, winning_key, other_comparison_pairs):
        """
        Calcualtes the scores for a new 1vs1 comparison without re-calculating all previous scores
        :param key1_scored_object: Contains score parameters for key1
        :param key2_scored_object: Contains score parameters for key2
        :param winning_key: indicates with key is the winning key
        :param other_comparison_pairs: Contains all previous comparison_pairs that the 2 keys took part in.
            This is a subset of all comparison pairs and is used to calculate score, round, wins, loses, and opponent counts
        :return: tuple of ScoredObjects (key1, key2)
        """
        self.storage = {}
        self.rounds = {}

        key1 = key1_scored_object.key
        key2 = key2_scored_object.key

        if winning_key != key1 and winning_key != key2:
            raise InvalidWinningKeyException

        for key in [key1, key2]:
            self.rounds[key] = 0
            self.storage[key] = {}

        # calculate opponents, wins, loses, rounds for every match for key1 and key2
        for comparison_pair in (other_comparison_pairs + [ComparisonPair(key1, key2, winning_key)]):
            cp_key1 = comparison_pair.key1
            cp_key2 = comparison_pair.key2
            cp_winning_key = comparison_pair.winning_key

            if cp_key1 == key1 or cp_key1 == key2:
                self.rounds[cp_key1] += 1

                if cp_winning_key != None:
                    self._update_win_lose(
                        cp_key1, cp_key2, cp_key1 == cp_winning_key
                    )

            if cp_key2 == key1 or cp_key2 == key2:
                self.rounds[cp_key2] += 1

                if cp_winning_key != None:
                    self._update_win_lose(
                        cp_key2, cp_key1, cp_key2 == cp_winning_key
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
        Calculate scores for a set of comparisons
        :param comparisons: array of
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
            winning_key = comparison_pair.winning_key

            self.rounds[key1] += 1
            self.rounds[key2] += 1

            # skip incomplete comparisosns
            if winning_key is None:
                continue

            # if there was a winner
            if winning_key == key1 or winning_key == key2:
                # update win/lose counts for both keys
                self._update_win_lose(
                    key1, key2, key1 == winning_key
                )
                self._update_win_lose(
                    key2, key1, key2 == winning_key
                )
            else:
                raise InvalidWinningKeyException

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

    def _update_win_lose(self, key, opponent_key, did_win):
        """
        Update number of wins/loses against an opponent
        :param key: Key to update
        :param opponent_key: Key of the opponent
        :param did_win: Weither the key won or lost the round
        """
        opponents = self.storage[key]
        opponent_stats = opponents.get(opponent_key, OpponentStats(0,0))
        if did_win:
            opponents[opponent_key] = opponent_stats._replace(
                wins=opponent_stats.wins + 1
            )
        else:
            opponents[opponent_key] = opponent_stats._replace(
                loses=opponent_stats.loses + 1
            )

    def _get_expected_score(self, key):
        """
        Calculate excepted score for a key
        :param key: the key to search for
        :return: excepted score
        """
        self._debug("Calculating score for key: " + str(key))
        opponents = self.storage.get(key, {})
        self._debug("\tThis key's opponents:" + str(opponents))

        # see ACJ paper equation 3 for what we're doing here
        # http://www.tandfonline.com/doi/full/10.1080/0969594X.2012.665354
        expected_score = 0
        for opponent_key, opponent_stats in opponents.items():
            # skip comparing to self
            if opponent_key == key:
                continue
            wins = opponent_stats.wins
            loses = opponent_stats.loses
            self._debug("\tVa = " + str(wins))
            self._debug("\tVi = " + str(loses))
            prob_answer_wins = \
                (math.exp(wins - loses)) / \
                (1 + math.exp(wins - loses))
            expected_score += prob_answer_wins
            self._debug("\tE(S) = " + str(expected_score))
        return expected_score

