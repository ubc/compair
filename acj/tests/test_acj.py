import json
import unittest

from flask.ext.testing import TestCase

from acj import create_app
from acj.manage.database import populate
from acj.core import db
from acj.tests import test_app_settings


# Tests Checklist
# - Unauthenticated users refused access with 401
# - Authenticated but unauthorized users refused access with 403
# - Non-existent entry errors out with 404
# - If post request, bad input format gets rejected with 400

class ACJTestCase(TestCase):

	def create_app(self):
		return create_app(settings_override=test_app_settings)

	def setUp(self):
		db.create_all()
		populate(default_data=True)

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def login(self, username, password="password"):
		payload = json.dumps(dict(
			username=username,
			password=password
		))
		rv = self.client.post('/api/login', data=payload, content_type='application/json', follow_redirects=True)
		self.assert200(rv)

		return rv

	def logout(self):
		return self.client.delete('/api/logout', follow_redirects=True)


class SessionTests(ACJTestCase):
	def test_loggedin_user_session(self):
		self.login('root', 'password')
		rv = self.client.get('/api/session')
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['id'], 1)

	def test_non_loggedin_user_session(self):
		rv = self.client.get('/api/session')
		self.assert401(rv)

if __name__ == '__main__':
	unittest.main()
