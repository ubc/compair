import math
from collections import namedtuple

from acj.algorithms.score.score_algorithm import ScoreAlgorithm
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.comparison_result import ComparisonResult

OpponentStats = namedtuple('OpponentStats', ['rounds', 'wins', 'loses'])

class ComparativeJudgementScoreAlgorithm(ScoreAlgorithm):
    def __init__(self):
        ScoreAlgorithm.__init__(self)

        # storage[key][opponent_key] = OpponentStats
        self.storage = {}

    def calculate_score(self, comparison_pairs):
        """
        Calculate scores for a set of comparisons
        :param comparisons: array of
        :return: dictionary key -> ComparisonResult
        """
        self.storage = {}

        for comparison_pair in comparison_pairs:
            key1 = comparison_pair.key1
            key2 = comparison_pair.key2
            winning_key = comparison_pair.winning_key

            # update round counts for both keys
            self._update_rounds(key1, key2)
            self._update_rounds(key2, key1)

            # if there was a winner
            if winning_key != None:
                # update win/lose counts for both keys
                self._update_win_lose(
                    key1, key2, key1 == winning_key
                )
                self._update_win_lose(
                    key2, key1, key2 == winning_key
                )

        comparison_results = {}

        for key, opponents in self.storage.items():
            score = self._get_expected_score(key)
            total_rounds = 0
            total_opponents = 0
            total_wins = 0
            total_loses = 0

            for opponent_key, opponent_stats in opponents.items():
                total_opponents += 1
                total_rounds += opponent_stats.rounds
                total_wins += opponent_stats.wins
                total_loses += opponent_stats.loses

            comparison_results[key] = ComparisonResult(
                key, score, total_rounds, total_opponents, total_wins, total_loses
            )

        return comparison_results

    def _update_rounds(self, key, opponent_key):
        """
        Update number of rounds against an opponent
        :param key: Key to update
        :param opponent_key: Key of the opponent
        """

        opponents = self.storage.setdefault(key, {})
        opponent_stats = opponents.get(
            opponent_key,
            OpponentStats(0,0,0)
        )
        opponents[opponent_key] = opponent_stats._replace(
            rounds=opponent_stats.rounds + 1
        )

    def _update_win_lose(self, key, opponent_key, did_win):
        """
        Update number of wins/loses against an opponent
        :param key: Key to update
        :param opponent_key: Key of the opponent
        :param did_win: Weither the key won or lost the round
        """
        opponents = self.storage.setdefault(key, {})
        opponent_stats = opponents.get(
            opponent_key,
            OpponentStats(0,0,0)
        )
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

