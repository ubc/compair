import unittest

from acj.models import User, Comparison, Score
from acj.models.comparison import update_scores
from test_acj import ACJTestCase
from acj.algorithms import ComparisonPair
from acj.algorithms.score import calculate_score

class TestUsersModel(ACJTestCase):
    user = User()

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


class TestUtils(ACJTestCase):
    def test_update_scores(self):

        criteria_comparison_results = {
            1: calculate_score(comparison_pairs=[
                ComparisonPair(1,2, winning_key=1)
            ])
        }
        scores = update_scores([], 1, criteria_comparison_results)
        self.assertEqual(len(scores), 2)
        for score in scores:
            self.assertIsNone(score.id)

        score = Score(answer_id=1, criteria_id=1, id=2)
        scores = update_scores([score], 1, criteria_comparison_results)
        self.assertEqual(len(scores), 2)
        self.assertEqual(scores[0].id, 2)
        self.assertIsNone(scores[1].id)


        criteria_comparison_results = {
            1: calculate_score(comparison_pairs=[
                   ComparisonPair(1,2, winning_key=1)
            ]),
            2: calculate_score(comparison_pairs=[
               ComparisonPair(1,2, winning_key=1)
            ])
        }
        score = Score(answer_id=1, criteria_id=1, id=2)
        scores = update_scores([score], 1, criteria_comparison_results)
        self.assertEqual(len(scores), 4)

if __name__ == '__main__':
    unittest.main()
