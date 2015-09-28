import unittest

from acj.models import Users, Judgements
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

if __name__ == '__main__':
    unittest.main()
