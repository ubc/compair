__author__ = 'compass'

import unittest
from acj.models import Users


class TestUsersModel(unittest.TestCase):
	user = Users()

	def setUp(self):
		self.user.firstname = "John"
		self.user.lastname = "Smith"

	def test_fullname(self):
		self.assertEqual(self.user.fullname, "John Smith")

	def test_avatar(self):
		self.user.email = "myemailaddress@example.com"
		self.assertEqual(self.user.avatar(), '0bc83cb571cd1c50ba6f3e8a78ef1346')
		self.user.email = " myemailaddress@example.com "
		self.assertEqual(
			self.user.avatar(), '0bc83cb571cd1c50ba6f3e8a78ef1346',
			'Email with leading and trailing whilespace')
		self.user.email = "MyEmailAddress@example.com"
		self.assertEqual(
			self.user.avatar(), '0bc83cb571cd1c50ba6f3e8a78ef1346',
			'Email with upper case letters')

if __name__ == '__main__':
	unittest.main()
