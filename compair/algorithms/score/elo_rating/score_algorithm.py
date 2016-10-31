import elo

from compair.algorithms.score.score_algorithm_base import ScoreAlgorithmBase
from compair.algorithms.comparison_pair import ComparisonPair
from compair.algorithms.scored_object import ScoredObject

from compair.algorithms.exceptions import InvalidWinningKeyException

class EloAlgorithmWrapper(ScoreAlgorithmBase):
    def __init__(self):
        ScoreAlgorithmBase.__init__(self)

        # storage[key] = ScoredObject
        self.storage = {}
        # storage[key] = set() of opponent keys
        self.opponents = {}
        # storage[key] = # of rounds
        self.rounds = {}

    def calculate_score_1vs1(self, key1_scored_object, key2_scored_object, winning_key, other_comparison_pairs):
        """
        Calcualtes the scores for a new 1vs1 comparison without re-calculating all previous scores
        :param key1_scored_object: Contains score parameters for key1
        :param key2_scored_object: Contains score parameters for key2
        :param winning_key: indicates with key is the winning key
        :param other_comparison_pairs: Contains all previous comparison_pairs that the 2 keys took part in.
            This is a subset of all comparison pairs and is used to calculate round, wins, loses, and opponent counts
        :return: tuple of ScoredObject (key1, key2)
        """
        self.storage = {}
        self.opponents = {}
        elo.setup()

        key1 = key1_scored_object.key
        key2 = key2_scored_object.key

        # Note: if value are None, elo.Rating will use default rating 1400
        r1 = elo.Rating(
            value=key1_scored_object.variable1
        )
        r2 = elo.Rating(
            value=key2_scored_object.variable1
        )

        if winning_key == key1:
            r1, r2 = elo.rate_1vs1(r1, r2)
        elif winning_key == key2:
            r2, r1 = elo.rate_1vs1(r2, r1)
        else:
            raise InvalidWinningKeyException

        for key in [key1, key2]:
            self.opponents[key] = set()
            self.storage[key] = ScoredObject(
                key=key,
                score=r1 if key == key1 else r2,
                variable1=r1 if key == key1 else r2,
                variable2=None,
                rounds=0,
                opponents=0,
                wins=0,
                loses=0
            )

        # calculate opponents, wins, loses, rounds for every match for key1 and key2
        for comparison_pair in (other_comparison_pairs + [ComparisonPair(key1, key2, winning_key)]):
            cp_key1 = comparison_pair.key1
            cp_key2 = comparison_pair.key2
            cp_winning_key = comparison_pair.winning_key

            if cp_key1 == key1 or cp_key1 == key2:
                if cp_winning_key is None:
                    self._update_rounds_only(cp_key1)
                else:
                    self._update_result_stats(cp_key1, cp_key2, cp_winning_key)

            if cp_key2 == key1 or cp_key2 == key2:
                if cp_winning_key is None:
                    self._update_rounds_only(cp_key2)
                else:
                    self._update_result_stats(cp_key2, cp_key1, cp_winning_key)

        return (self.storage[key1], self.storage[key2])

    def calculate_score(self, comparison_pairs):
        """
        Calculate scores for a set of comparisons
        :param comparisons: array of
        :return: dictionary key -> ScoredObject
        """
        self.storage = {}
        self.opponents = {}
        elo.setup()

        keys = self.get_keys_from_comparison_pairs(comparison_pairs)
        # create default ratings for every available key
        for key in keys:
            self.storage[key] = ScoredObject(
                key=key,
                score=elo.Rating(),
                variable1=elo.Rating(),
                variable2=None,
                rounds=0,
                opponents=0,
                wins=0,
                loses=0
            )
            self.opponents[key] = set()

        # calculate rating for every match
        for comparison_pair in comparison_pairs:
            key1 = comparison_pair.key1
            key2 = comparison_pair.key2
            winning_key = comparison_pair.winning_key

            # skip incomplete comparisosns
            if winning_key is None:
                self._update_rounds_only(key1)
                self._update_rounds_only(key2)
                continue

            r1 = self.storage[key1].score
            r2 = self.storage[key2].score

            if winning_key == comparison_pair.key1:
                r1, r2 = elo.rate_1vs1(r1, r2)
            elif winning_key == comparison_pair.key2:
                r2, r1 = elo.rate_1vs1(r2, r1)
            else:
                raise InvalidWinningKeyException

            self._update_rating(key1, r1, key2, winning_key)
            self._update_rating(key2, r2, key1, winning_key)

        # return comparison results
        return self.storage

    def _update_rounds_only(self, key):
        rounds = self.storage[key].rounds
        self.storage[key] = self.storage[key]._replace(rounds=rounds+1)

    def _update_result_stats(self, key, opponent_key, winning_key):
        self.opponents[key].add(opponent_key)
        wins = self.storage[key].wins
        loses = self.storage[key].loses

        # winning_key == None should not increase total wins or loses
        self.storage[key] = ScoredObject(
            key=key,
            score=self.storage[key].score,
            variable1=self.storage[key].score,
            variable2=None,
            rounds=self.storage[key].rounds+1,
            opponents=len(self.opponents[key]),
            wins=wins+1 if winning_key == key else wins,
            loses=loses+1 if winning_key == opponent_key else loses,
        )

    def _update_rating(self, key, new_rating, opponent_key, winning_key):
        self.opponents[key].add(opponent_key)
        wins = self.storage[key].wins
        loses = self.storage[key].loses

        # winning_key == None should not increase total wins or loses
        self.storage[key] = ScoredObject(
            key=key,
            score=new_rating,
            variable1=new_rating,
            variable2=None,
            rounds=self.storage[key].rounds+1,
            opponents=len(self.opponents[key]),
            wins=wins+1 if winning_key == key else wins,
            loses=loses+1 if winning_key == opponent_key else loses,
        )

