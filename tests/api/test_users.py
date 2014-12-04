from flask.ext.bouncer import ensure
from flask.ext.login import login_user, logout_user
from werkzeug.exceptions import Unauthorized
from acj import db, Users
from data.fixtures import DefaultFixture
from data.fixtures import UsersFactory
from tests.test_acj import ACJTestCase
from acj.models import UserTypesForSystem, UserTypesForCourse
from data.fixtures.test_data import BasicTestData
import json, string, random


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
		self.assertEqual(users['num_results'], 7)
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
			self.data.get_authorized_instructor().id: self._generate_search_users(self.data.get_authorized_instructor()),
			self.data.get_unauthorized_instructor().id: self._generate_search_users(self.data.get_unauthorized_instructor()),
			self.data.get_dropped_instructor().id: self._generate_search_users(self.data.get_dropped_instructor())
		}
		for instructor in instructors:
			self.assertEqual(expected[instructor['id']], instructor)
		self.logout()

	def test_get_all_user_list(self):
		url = '/api/usertypes/all'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test successful query
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(url)
		self.assert200(rv)
		users = rv.json['users']
		admin = Users.query.filter_by(username='root').first()
		expected = {
			admin.id: self._generate_search_users(admin),
			self.data.get_authorized_instructor().id: self._generate_search_users(self.data.get_authorized_instructor()),
			self.data.get_authorized_ta().id: self._generate_search_users(self.data.get_authorized_ta()),
			self.data.get_authorized_student().id: self._generate_search_users(self.data.get_authorized_student()),
			self.data.get_unauthorized_instructor().id: self._generate_search_users(self.data.get_unauthorized_instructor()),
			self.data.get_unauthorized_student().id: self._generate_search_users(self.data.get_unauthorized_student()),
			self.data.get_dropped_instructor().id: self._generate_search_users(self.data.get_dropped_instructor())
		}
		self.assertEqual(len(expected), 7)
		for user in users:
			self.assertEqual(expected[user['id']], user)
		self.logout()

	def test_create_user(self):
		url = '/api/users'
		types = UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_NORMAL).all()
		expected = {
			'username': ''.join(random.choice(string.ascii_letters) for _ in range(8)),
			'usertypesforsystem_id': types[0].id,
			'student_no': ''.join(random.choice(string.digits) for _ in range(4)),
			'firstname': "First" + ''.join(random.choice(string.digits) for _ in range(4)),
			'lastname': "Last" + ''.join(random.choice(string.digits) for _ in range(4)),
			'displayname': "display" + ''.join(random.choice(string.digits) for _ in range(4)),
			'email': 'test' + ''.join(random.choice(string.digits) for _ in range(4)) + "@testserver.ca",
			'password': 'password'
		}

		# test login required
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_authorized_student().username)
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# test duplicate username
		self.login(self.data.get_authorized_instructor().username)
		duplicate = expected.copy()
		duplicate['username'] = self.data.get_authorized_student().username
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This username already exists. Please pick another.", rv.json['error'])

		# test duplicate student number
		duplicate = expected.copy()
		duplicate['student_no'] = self.data.get_authorized_student().student_no
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This student number already exists. Please pick another.", rv.json['error'])

		# test duplicate display name
		duplicate = expected.copy()
		duplicate['displayname'] = self.data.get_authorized_student().displayname
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This display name already exists. Please pick another.", rv.json['error'])

		# test creating users of all user types for system
		for type in types:
			user = {
				'username': ''.join(random.choice(string.ascii_letters) for _ in range(8)),
				'usertypesforsystem_id': type.id,
				'student_no': ''.join(random.choice(string.digits) for _ in range(4)),
				'firstname': "First" + ''.join(random.choice(string.digits) for _ in range(4)),
				'lastname': "Last" + ''.join(random.choice(string.digits) for _ in range(4)),
				'displayname': "display" + ''.join(random.choice(string.digits) for _ in range(4)),
				'email': 'test' + ''.join(random.choice(string.digits) for _ in range(4)) + "@testserver.ca",
				'password': 'password'
			}
			rv = self.client.post(url, data=json.dumps(user), content_type="application/json")
			self.assert200(rv)
			self.assertEqual(user['displayname'], rv.json['displayname'])

	def test_edit_user(self):
		user = self.data.get_authorized_student()
		url = 'api/users/' + str(user.id)
		expected = {
			'id': user.id,
			'username': user.username,
			'student_no': user.student_no,
			'usertypesforsystem_id': user.usertypesforsystem_id,
			'firstname': user.firstname,
			'lastname': user.lastname,
			'displayname': user.displayname,
			'email': user.email
		}

		# test login required
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		# currently, instructors cannot edit users
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# test invalid user id
		self.login('root')
		rv = self.client.post('/api/users/999', data=json.dumps(expected), content_type='application/json')
		self.assert404(rv)

		# test unmatched user's id
		invalid_url = '/api/users/' + str(self.data.get_authorized_instructor().id)
		rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
		self.assert400(rv)

		# test duplicate username
		duplicate = expected.copy()
		duplicate['username'] = self.data.get_unauthorized_student().username
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This username already exists. Please pick another.", rv.json['error'])

		# test duplicate student number
		duplicate = expected.copy()
		duplicate['student_no'] = self.data.get_unauthorized_student().student_no
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This student number already exists. Please pick another.", rv.json['error'])

		# test duplicate display name
		duplicate = expected.copy()
		duplicate['displayname'] = self.data.get_unauthorized_student().displayname
		rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
		self.assertStatus(rv, 409)
		self.assertEqual("This display name already exists. Please pick another.", rv.json['error'])

		# test successful update by admin
		valid = expected.copy()
		valid['displayname'] = "displayzzz"
		rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
		self.assert200(rv)
		self.assertEqual("displayzzz", rv.json['displayname'])
		self.logout()

		# test successful update by user
		self.login(self.data.get_authorized_student().username)
		valid = expected.copy()
		valid['displayname'] = "thebest"
		rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
		self.assert200(rv)
		self.assertEqual("thebest", rv.json['displayname'])
		self.logout()

	def get_course_list(self):
		# test login required
		url = '/api/users/'+str(self.data.get_authorized_instructor().id)+'/courses'
		rv = self.client.get(url)
		self.assert401(rv)

		# test invalid user id
		self.login('root')
		url = '/api/users/999/courses'
		rv = self.client.get(url)
		self.assert404(rv)

		# test admin
		adminId = Users.query.filter_by(username='root').first().id
		url = '/api/users/'+str(adminId)+'/courses'
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(2, len(rv.json['objects']))
		self.logout()

		# test authorized instructor
		self.login(self.data.get_authorized_instructor().username)
		url = '/api/users/'+str(self.data.get_authorized_instructor().id)+'/courses'
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(1, len(rv.json['objects']))
		self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])
		self.logout()

		# test authorized student
		self.login(self.data.get_authorized_student().username)
		url = '/api/users/'+str(self.data.get_authorized_student().id)+'/courses'
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(1, len(rv.json['objects']))
		self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])
		self.logout()

		# test authorized teaching assistant
		self.login(self.data.get_authorized_ta().username)
		url = '/api/users/'+str(self.data.get_authorized_ta().id)+'/courses'
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(1, len(rv.json['objects']))
		self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])
		self.logout()

		# test dropped instructor
		self.login(self.data.get_dropped_instructor().username)
		url = '/api/users/'+str(self.data.get_dropped_instructor().id)+'/courses'
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(0, len(rv.json['objects']))

	def test_update_password(self):
		url = '/api/users/password/'+ str(self.data.get_authorized_instructor().id)
		input = {
			'oldpassword': 'password',
			'newpassword': 'abcd1234'
		}

		# test login required
		rv = self.client.post(url, data=json.dumps(input), content_type='application/json')
		self.assert401(rv)

		# test invalid user id
		self.login(self.data.get_authorized_instructor().username)
		invalid_url = '/api/users/password/999'
		rv = self.client.post(invalid_url, data=json.dumps(input), content_type='application/json')
		self.assert404(rv)

		# test incorrect old password
		invalid_input = input.copy()
		invalid_input['oldpassword'] = 'wrong'
		rv = self.client.post(url, data=json.dumps(invalid_input), content_type='application/json')
		self.assert403(rv)
		self.assertEqual("The old password is incorrect.", rv.json['error'])

		# test unauthorized user
		invalid_url = '/api/users/password/'+str(self.data.get_authorized_student().id)
		rv = self.client.post(invalid_url, data=json.dumps(input), content_type='application/json')
		self.assert403(rv)

		# test changing own password
		rv = self.client.post(url, data=json.dumps(input), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(self.data.get_authorized_instructor().id, rv.json['id'])
		self.logout()

	def test_get_course_roles(self):
		url = '/api/courseroles'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test successful query
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(url)
		self.assert200(rv)
		types = rv.json
		self.assertEqual(len(types), 3)
		self.assertEqual(types[0]['name'], UserTypesForCourse.TYPE_INSTRUCTOR)
		self.assertEqual(types[1]['name'], UserTypesForCourse.TYPE_TA)
		self.assertEqual(types[2]['name'], UserTypesForCourse.TYPE_STUDENT)
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

	def _generate_search_users(self, user):
		return {'id': user.id, 'display': user.fullname+' ('+user.displayname+') - '+user.usertypeforsystem.name, 'name': user.fullname}
