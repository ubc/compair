import unittest

from acj.models import Users, Judgements, update_scores, WinsTable, Scores
from test_acj import ACJTestCase


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
        wins = WinsTable([1])
        scores = update_scores([], [1, 2], [1], wins, {})
        self.assertEqual(len(scores), 2)
        for score in scores:
            self.assertIsNone(score.id)

        score = Scores(answers_id=1, criteriaandquestions_id=1, id=2)
        scores = update_scores([score], [1, 2], [1], wins, {})
        self.assertEqual(len(scores), 2)
        self.assertEqual(scores[0].id, 2)
        self.assertIsNone(scores[1].id)

        wins = WinsTable([1, 2])
        score = Scores(answers_id=1, criteriaandquestions_id=1, id=2)
        scores = update_scores([score], [1, 2], [1, 2], wins, {})
        self.assertEqual(len(scores), 4)
        # self.assertEqual(scores[0].id, 2)
        # self.assertIsNone(scores[1].id)

if __name__ == '__main__':
    unittest.main()
