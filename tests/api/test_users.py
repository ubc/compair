from flask.ext.bouncer import ensure
from flask.ext.login import login_user, logout_user
from werkzeug.exceptions import Unauthorized
from acj import db, Users
from data.fixtures import DefaultFixture
from data.fixtures import UsersFactory
from tests.test_acj import ACJTestCase
from acj.models import UserTypesForSystem
from data.fixtures.test_data import BasicTestData


class UsersAPITests(ACJTestCase):
	def setUp(self):
		super(UsersAPITests, self).setUp()
		self.data = BasicTestData()

	def test_unauthorized(self):
		rv = self.client.get('/api/users')
		self.assert401(rv)

	def test_login(self):
		rv = self.login('root', 'password')
		userid = rv.json['userid']
		self.assertEqual(userid, 1, "Logged in user's id does not match!")
		self._verify_permissions(userid, rv.json['permissions'])

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
		user = UsersFactory(password='password', usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)
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
		self.assertEqual(users['num_results'], 6)
		self.assertEqual(users['objects'][0]['username'], 'root')

	def test_usertypes(self):
		# test login required
		rv = self.client.get('/api/usertypes')
		self.assert401(rv)

		# test results
		self.login('root', 'password')
		rv = self.client.get('/api/usertypes')
		self.assert200(rv)
		types = rv.json
		self.assertEqual(len(types), 3)
		self.assertEqual(types[0]['name'], UserTypesForSystem.TYPE_NORMAL)
		self.assertEqual(types[1]['name'], UserTypesForSystem.TYPE_INSTRUCTOR)
		self.assertEqual(types[2]['name'], UserTypesForSystem.TYPE_SYSADMIN)
		self.logout()

	def test_get_instructors(self):
		# test login required
		rv = self.client.get('/api/usertypes/instructors')
		self.assert401(rv)

		# test results
		self.login('root', 'password')
		rv = self.client.get('/api/usertypes/instructors')
		self.assert200(rv)
		instructors = rv.json['instructors']
		expected = {
			str(self.data.get_authorized_instructor().id): self.data.get_authorized_instructor().fullname,
			str(self.data.get_unauthorized_instructor().id): self.data.get_unauthorized_instructor().fullname,
			str(self.data.get_dropped_instructor().id): self.data.get_dropped_instructor().fullname
		}
		for id in instructors:
			self.assertEqual(expected[id], instructors[id])
		self.logout()


	def _verify_permissions(self, userid, permissions):
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
