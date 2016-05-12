import unittest

from acj.models import Users, Judgements, update_scores, Scores
from test_acj import ACJTestCase
import acj.algorithms
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.comparison_result import ComparisonResult


class TestUsersModel(ACJTestCase):
    user = Users()

    def setUp(self):
        self.user.firstname = "John"
        self.user.lastname = "Smith"

    def test_fullname(self):
        self.assertEqual(self.user.fullname, "John Smith")

    def test_avatar(self):
        self.user.email = "myemailaddress@example.com"
        self.assertEqual(self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346')
        self.user.email = " myemailaddress@example.com "
        self.assertEqual(
            self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346',
            'Email with leading and trailing whilespace')
        self.user.email = "MyEmailAddress@example.com"
        self.assertEqual(
            self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346',
            'Email with upper case letters')

    def test_set_password(self):
        self.user.password = '123456'
        self.assertTrue(self.user.verify_password('123456'))


class TestJudgementModel(ACJTestCase):
    judgement = Judgements()

    def setUp(self):
        pass

    def test_caculate_scores(self):
        pass
        # Judgements.calculate_scores(1)


class TestUtils(ACJTestCase):
    def test_update_scores(self):
    
        criteria_comparison_results = {
            1: acj.algorithms.calculate_scores(
               [ComparisonPair(1,2, winning_key=1)], "acj", None
            )
        }
        scores = update_scores([], criteria_comparison_results)
        self.assertEqual(len(scores), 2)
        for score in scores:
            self.assertIsNone(score.id)

        score = Scores(answers_id=1, criteriaandquestions_id=1, id=2)
        scores = update_scores([score], criteria_comparison_results)
        self.assertEqual(len(scores), 2)
        self.assertEqual(scores[0].id, 2)
        self.assertIsNone(scores[1].id)

    
        criteria_comparison_results = {
            1: acj.algorithms.calculate_scores(
               [ComparisonPair(1,2, winning_key=1)], "acj", None
            ),
            2: acj.algorithms.calculate_scores(
               [ComparisonPair(1,2, winning_key=1)], "acj", None
            )
        }
        score = Scores(answers_id=1, criteriaandquestions_id=1, id=2)
        scores = update_scores([score], criteria_comparison_results)
        self.assertEqual(len(scores), 4)

if __name__ == '__main__':
    unittest.main()
