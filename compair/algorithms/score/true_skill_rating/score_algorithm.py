import trueskill

from acj.algorithms.score.score_algorithm_base import ScoreAlgorithmBase
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.scored_object import ScoredObject

from acj.algorithms.exceptions import InvalidWinningKeyException

class TrueSkillAlgorithmWrapper(ScoreAlgorithmBase):
    def __init__(self):
        ScoreAlgorithmBase.__init__(self)

        # storage[key] = ScoredObject
        self.storage = {}
        # storage[key] = set() of opponent keys
        self.opponents = {}
        # storage[key] = true skill rating object
        self.ratings = {}

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
        self.ratings = {}
        trueskill.setup()

        key1 = key1_scored_object.key
        key2 = key2_scored_object.key

        # Note: if value are None, trueskill.Rating will use default mu 25 and sigma 8.333
        r1 = trueskill.Rating(
            mu=key1_scored_object.variable1,
            sigma=key1_scored_object.variable2
        )

        r2 = trueskill.Rating(
            mu=key2_scored_object.variable1,
            sigma=key2_scored_object.variable2
        )

        if winning_key == key1:
            r1, r2 = trueskill.rate_1vs1(r1, r2)
        elif winning_key == key2:
            r2, r1 = trueskill.rate_1vs1(r2, r1)
        else:
            raise InvalidWinningKeyException

        self.ratings[key1] = r1
        self.ratings[key2] = r2

        for key in [key1, key2]:
            self.opponents[key] = set()
            self.storage[key] = ScoredObject(
                key=key,
                score=trueskill.expose(self.ratings[key]),
                variable1=self.ratings[key].mu,
                variable2=self.ratings[key].sigma,
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
        self.ratings = {}
        trueskill.setup()

        keys = self.get_keys_from_comparison_pairs(comparison_pairs)
        # create default ratings for every available key
        for key in keys:
            rating = trueskill.Rating()
            self.ratings[key] = rating
            self.opponents[key] = set()

            self.storage[key] = ScoredObject(
                key=key,
                score=trueskill.expose(rating),
                variable1=rating.mu,
                variable2=rating.sigma,
                rounds=0,
                opponents=0,
                wins=0,
                loses=0
            )

        # calculate rating by for every match
        for comparison_pair in comparison_pairs:
            key1 = comparison_pair.key1
            key2 = comparison_pair.key2
            winning_key = comparison_pair.winning_key

            # skip incomplete comparisosns
            if winning_key is None:
                self._update_rounds_only(key1)
                self._update_rounds_only(key2)
                continue

            r1 = self.ratings[key1]
            r2 = self.ratings[key2]

            if winning_key == comparison_pair.key1:
                r1, r2 = trueskill.rate_1vs1(r1, r2)
            elif winning_key == comparison_pair.key2:
                r2, r1 = trueskill.rate_1vs1(r2, r1)
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
            variable1=self.ratings[key].mu,
            variable2=self.ratings[key].sigma,
            rounds=self.storage[key].rounds+1,
            opponents=len(self.opponents[key]),
            wins=wins+1 if winning_key == key else wins,
            loses=loses+1 if winning_key == opponent_key else loses,
        )

    def _update_rating(self, key, new_rating, opponent_key, winning_key):
        self.ratings[key] = new_rating
        self.opponents[key].add(opponent_key)
        wins = self.storage[key].wins
        loses = self.storage[key].loses

        # winning_key == None should not increase total wins or loses
        self.storage[key] = ScoredObject(
            key=key,
            score=trueskill.expose(new_rating),
            variable1=new_rating.mu,
            variable2=new_rating.sigma,
            rounds=self.storage[key].rounds+1,
            opponents=len(self.opponents[key]),
            wins=wins+1 if winning_key == key else wins,
            loses=loses+1 if winning_key == opponent_key else loses,
        )

