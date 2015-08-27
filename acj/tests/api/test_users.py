import json
import string
import random

from flask.ext.bouncer import ensure
from flask.ext.login import login_user, logout_user
from werkzeug.exceptions import Unauthorized

from data.fixtures import DefaultFixture
from data.fixtures import UsersFactory
from data.fixtures.test_data import BasicTestData
from acj import db, Users
from acj.tests.test_acj import ACJTestCase
from acj.models import UserTypesForSystem, UserTypesForCourse


class UsersAPITests(ACJTestCase):
    def setUp(self):
        super(UsersAPITests, self).setUp()
        self.data = BasicTestData()

    def test_unauthorized(self):
        rv = self.client.get('/api/users')
        self.assert401(rv)

    def test_login(self):
        with self.login('root', 'password') as rv:
            userid = rv.json['userid']
            self.assertEqual(userid, 1, "Logged in user's id does not match!")
            self._verify_permissions(userid, rv.json['permissions'])

    def test_users_root(self):
        with self.login('root', 'password'):
            rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
            self.assert200(rv)
            root = rv.json
            self.assertEqual(root['username'], 'root')
            self.assertEqual(root['displayname'], 'root')
            self.assertNotIn('_password', root)

    def test_users_invalid_id(self):
        with self.login('root', 'password'):
            rv = self.client.get('/api/users/99999')
            self.assert404(rv)

    def test_users_info_unrestricted(self):
        with self.login('root', 'password'):
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

        with self.login(user.username, 'password'):
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
        with self.login('root', 'password'):
            rv = self.client.get('/api/users')
            self.assert200(rv)
            users = rv.json
            self.assertEqual(users['total'], 7)
            self.assertEqual(users['objects'][0]['username'], 'root')

            rv = self.client.get('/api/users?search={}'.format(self.data.get_unauthorized_instructor().firstname))
            self.assert200(rv)
            users = rv.json
            self.assertEqual(users['total'], 1)
            self.assertEqual(users['objects'][0]['username'], self.data.get_unauthorized_instructor().username)

    def test_usertypes(self):
        # test login required
        rv = self.client.get('/api/usertypes')
        self.assert401(rv)

        # test results
        with self.login('root', 'password'):
            rv = self.client.get('/api/usertypes')
            self.assert200(rv)
            types = rv.json
            self.assertEqual(len(types), 3)
            self.assertEqual(types[0]['name'], UserTypesForSystem.TYPE_NORMAL)
            self.assertEqual(types[1]['name'], UserTypesForSystem.TYPE_INSTRUCTOR)
            self.assertEqual(types[2]['name'], UserTypesForSystem.TYPE_SYSADMIN)

    def test_get_instructors(self):
        # test login required
        rv = self.client.get('/api/usertypes/instructors')
        self.assert401(rv)

        # test results
        with self.login('root', 'password'):
            rv = self.client.get('/api/usertypes/instructors')
            self.assert200(rv)
            instructors = rv.json['instructors']
            expected = {
                self.data.get_authorized_instructor().id: self._generate_search_users(
                    self.data.get_authorized_instructor()),
                self.data.get_unauthorized_instructor().id: self._generate_search_users(
                    self.data.get_unauthorized_instructor()),
                self.data.get_dropped_instructor().id: self._generate_search_users(self.data.get_dropped_instructor())
            }
            for instructor in instructors:
                self.assertEqual(expected[instructor['id']], instructor)

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
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

        # test duplicate username
        with self.login(self.data.get_authorized_instructor().username):
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

            # test creating users of all user types for system
            for user_type in types:
                user = {
                    'username': ''.join(random.choice(string.ascii_letters) for _ in range(8)),
                    'usertypesforsystem_id': user_type.id,
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
        user = self.data.get_authorized_instructor()
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
        # currently, instructors cannot edit users - except their own profile
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

        # test invalid user id
        with self.login('root'):
            rv = self.client.post('/api/users/999', data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test unmatched user's id
            invalid_url = '/api/users/' + str(self.data.get_unauthorized_instructor().id)
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

            # test successful update by admin
            valid = expected.copy()
            valid['displayname'] = "displayzzz"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("displayzzz", rv.json['displayname'])

        # test successful update by user
        with self.login(self.data.get_authorized_instructor().username):
            valid = expected.copy()
            valid['displayname'] = "thebest"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])

        # test unable to update username, student_no, usertypesforsystem_id - instructor
        student = UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_NORMAL).first()
        with self.login(user.username):
            valid = expected.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.username, rv.json['username'])

            valid = expected.copy()
            valid['student_no'] = "999999999999"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.student_no, rv.json['student_no'])

            valid = expected.copy()
            valid['usertypesforsystem_id'] = student.id
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.usertypesforsystem_id, rv.json['usertypesforsystem_id'])

        # test updating username, student number, usertype for system - admin
        with self.login('root'):
            valid = expected.copy()
            valid['username'] = 'newUsername'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('newUsername', rv.json['username'])

            valid = expected.copy()
            valid['student_no'] = '99999999'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('99999999', rv.json['student_no'])

            valid = expected.copy()
            valid['usertypesforsystem_id'] = student.id
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.usertypesforsystem_id, rv.json['usertypesforsystem_id'])

    def test_get_course_list(self):
        # test login required
        url = '/api/users/' + str(self.data.get_authorized_instructor().id) + '/courses'
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid user id
        with self.login('root'):
            url = '/api/users/999/courses'
            rv = self.client.get(url)
            self.assert404(rv)

            # test admin
            admin_id = Users.query.filter_by(username='root').first().id
            url = '/api/users/' + str(admin_id) + '/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json['objects']))

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/' + str(self.data.get_authorized_instructor().id) + '/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

        # test authorized student
        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/' + str(self.data.get_authorized_student().id) + '/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

        # test authorized teaching assistant
        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/' + str(self.data.get_authorized_ta().id) + '/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

        # test dropped instructor
        with self.login(self.data.get_dropped_instructor().username):
            url = '/api/users/' + str(self.data.get_dropped_instructor().id) + '/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

    def test_get_teaching_course(self):
        url = '/api/users/courses/teaching'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['courses']))

        # test TA
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['courses']))

        # test instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['courses']))

        # test admin
        with self.login('root'):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json['courses']))

    def test_update_password(self):
        url = '/api/users/password/' + str(self.data.get_authorized_instructor().id)
        data = {
            'oldpassword': 'password',
            'newpassword': 'abcd1234'
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assert401(rv)

        # test invalid user id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = '/api/users/password/999'
            rv = self.client.post(invalid_url, data=json.dumps(data), content_type='application/json')
            self.assert404(rv)

            # test incorrect old password
            invalid_input = data.copy()
            invalid_input['oldpassword'] = 'wrong'
            rv = self.client.post(url, data=json.dumps(invalid_input), content_type='application/json')
            self.assert403(rv)
            self.assertEqual("The old password is incorrect.", rv.json['error'])

            # test unauthorized user
            invalid_url = '/api/users/password/' + str(self.data.get_authorized_student().id)
            rv = self.client.post(invalid_url, data=json.dumps(data), content_type='application/json')
            self.assert403(rv)

            # test changing own password
            rv = self.client.post(url, data=json.dumps(data), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_instructor().id, rv.json['id'])

    def test_get_course_roles(self):
        url = '/api/courseroles'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test successful query
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(url)
            self.assert200(rv)
            types = rv.json
            self.assertEqual(len(types), 3)
            self.assertEqual(types[0]['name'], UserTypesForCourse.TYPE_INSTRUCTOR)
            self.assertEqual(types[1]['name'], UserTypesForCourse.TYPE_TA)
            self.assertEqual(types[2]['name'], UserTypesForCourse.TYPE_STUDENT)

    def test_get_edit_button(self):
        url = '/api/users/' + str(self.data.get_authorized_student().id) + '/edit'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid user id
        with self.login(self.data.get_unauthorized_student().username):
            invalid_url = '/api/users/999/edit'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test unavailable button
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

        # test available button
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertTrue(rv.json['available'])

    def _verify_permissions(self, userid, permissions):
        user = Users.query.get(userid)
        with self.app.app_context():
            # can't figure out how to get into logged in app context, so just force a login here
            login_user(user, force=True)
            admin = user.usertypeforsystem.name == 'System Administrator'
            for model_name, operations in permissions.items():
                for operation, permission in operations.items():
                    expected = True
                    try:
                        ensure(operation, model_name)
                    except Unauthorized:
                        expected = False
                    expected = expected or admin
                    self.assertEqual(
                        permission['global'], expected,
                        "Expected permission " + operation + " on " + model_name + " to be " + str(expected))
            # undo the forced login earlier
            logout_user()

    def _generate_search_users(self, user):
        return {
            'id': user.id,
            'display': user.fullname + ' (' + user.displayname + ') - ' + user.usertypeforsystem.name,
            'name': user.fullname}
