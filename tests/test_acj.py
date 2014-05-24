import json
import unittest
from flask.ext.testing import TestCase
from acj import create_app
from acj.manage.database import populate
from acj.core import db
from tests import test_app_settings


class ACJTestCase(TestCase):

	def create_app(self):
		return create_app(settings_override=test_app_settings)

	def setUp(self):
		db.create_all()
		#self.default_data = get_dbfixture(db).data(*all_data)
		#self.default_data.setup()
		self.fixture_data = populate(default_data=True)

	def tearDown(self):
		# need to destroy the fixture data object, otherwise DB session will complain
		# that the same object is registered to different sessions
		self.fixture_data.teardown()
		db.session.remove()
		db.drop_all()

	def test_unauthorized(self):
		rv = self.client.get('/api/users')
		self.assert401(rv)

	def test_login(self):
		rv = self.login('root', 'password')
		self.assert200(rv)
		self.assertEqual(rv.json, {'userid': 1})

	def test_users_1(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/1')
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['username'], 'root')
		self.assertEqual(root['displayname'], 'root')

	def login(self, username, password):
		payload = json.dumps(dict(
			username=username,
			password=password
		))
		return self.client.post('/login/login', data=payload, content_type='application/json', follow_redirects=True)

	def logout(self):
		return self.client.get('/login/logout', follow_redirects=True)


if __name__ == '__main__':
	unittest.main()