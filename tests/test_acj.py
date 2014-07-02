import json
import unittest
from flask.ext.testing import TestCase
from flask_bouncer import ensure
from flask_login import login_user, logout_user
from werkzeug.exceptions import Unauthorized
from acj import create_app, Users
from acj.manage.database import populate
from acj.core import db
from data.fixtures import DefaultFixture
from tests import test_app_settings
from tests.factories import CourseFactory, UserFactory


class ACJTestCase(TestCase):

	def create_app(self):
		return create_app(settings_override=test_app_settings)

	def setUp(self):
		db.create_all()
		populate(default_data=True)

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_unauthorized(self):
		rv = self.client.get('/api/users')
		self.assert401(rv)

	def test_login(self):
		rv = self.login('root', 'password')
		userid = rv.json['userid']
		self.assertEqual(userid, 1, "Logged in user's id does not match!")
		self._verifyPermissions(userid, rv.json['permissions'])

	def test_users_root(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['username'], 'root')
		self.assertEqual(root['displayname'], 'root')
		self.assertNotIn('_password', root)

	def test_users_invalid_id(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/99999')
		self.assert404(rv)

	def test_users_info_unrestricted(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['displayname'], 'root')
		# personal information should be transmitted
		self.assertIn('firstname', root)
		self.assertIn('lastname', root)
		self.assertIn('fullname', root)
		self.assertIn('email', root)

	def test_users_info_restricted(self):
		user = UserFactory(password='password', usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)
		db.session.commit()

		self.login(user.username, 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['displayname'], 'root')
		# personal information shouldn't be transmitted
		self.assertNotIn('firstname', root)
		self.assertNotIn('lastname', root)
		self.assertNotIn('fullname', root)
		self.assertNotIn('email', root)

	def test_users_list(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users')
		self.assert200(rv)
		users = rv.json
		self.assertEqual(users['num_results'], 1)
		self.assertEqual(users['objects'][0]['username'], 'root')

	def test_get_course(self):
		course_expected = CourseFactory()
		db.session.commit()

		# Test login required
		rv = self.client.get('/api/courses/' + str(course_expected.id))
		self.assert401(rv)
		# TODO easy way to test permissions?
		# Test info
		self.login('root', 'password')
		rv = self.client.get('/api/courses/' + str(course_expected.id))
		self.assert200(rv)
		course_actual = rv.json
		self.assertEqual(course_expected.name, course_actual['name'],
			"Expected course name does not match actual.")
		self.assertEqual(course_expected.id, course_actual['id'],
			"Expected course id does not match actual.")

	def test_create_course(self):
		course_expected = {
			'name':'TestCourse1',
			'description':'Test Course One Description Test'
		}
		# Test course creation
		self.login('root', 'password')
		rv = self.client.post('/api/courses',
			data=json.dumps(course_expected), content_type='application/json')
		self.assert200(rv)
		# Verify return
		course_actual = rv.json
		self.assertEqual(course_expected['name'], course_actual['name'])
		self.assertEqual(course_expected['description'], course_actual['description'])
		# Verify you can get the course again
		rv = self.client.get('/api/courses/' + str(course_actual['id']))
		self.assert200(rv)
		course_actual = rv.json
		self.assertEqual(course_expected['name'], course_actual['name'])
		self.assertEqual(course_expected['description'], course_actual['description'])

	def login(self, username, password):
		payload = json.dumps(dict(
			username=username,
			password=password
		))
		rv = self.client.post('/login/login', data=payload, content_type='application/json', follow_redirects=True)
		self.assert200(rv)

		return rv

	def logout(self):
		return self.client.delete('/login/logout', follow_redirects=True)

	def _verifyPermissions(self, userid, permissions):
		user = Users.query.get(userid)
		with self.app.app_context():
			# can't figure out how to get into logged in app context, so just force a login here
			login_user(user, force=True)
			for model_name, operations in permissions.items():
				for operation, permission in operations.items():
					expected = True
					try:
						ensure(operation, model_name)
					except Unauthorized:
						expected = False
					self.assertEqual(permission, expected,
						"Expected permission " + operation + " on " +  model_name + " to be " + str(expected))
			# undo the forced login earlier
			logout_user()


if __name__ == '__main__':
	unittest.main()
