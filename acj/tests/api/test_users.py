import json

from flask_bouncer import ensure
from flask_login import login_user, logout_user
from werkzeug.exceptions import Unauthorized

from data.fixtures import DefaultFixture, UserFactory
from data.fixtures.test_data import BasicTestData, LTITestData, ThirdPartyAuthTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import User, SystemRole, CourseRole, LTIContext, ThirdPartyUser, ThirdPartyType
from acj.core import db


class UsersAPITests(ACJAPITestCase):
    def setUp(self):
        super(UsersAPITests, self).setUp()
        self.data = BasicTestData()

    def test_unauthorized(self):
        rv = self.client.get('/api/users')
        self.assert401(rv)

    def test_login(self):
        with self.login('root', 'password') as rv:
            root = User.query.get(1)
            user_id = rv.json['user_id']
            self.assertEqual(root.uuid, user_id, "Logged in user's id does not match!")
            self._verify_permissions(root.id, rv.json['permissions'])

    def test_users_root(self):
        with self.login('root', 'password'):
            rv = self.client.get('/api/users/' + DefaultFixture.ROOT_USER.uuid)
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
            rv = self.client.get('/api/users/' + DefaultFixture.ROOT_USER.uuid)
            self.assert200(rv)
            root = rv.json
            self.assertEqual(root['displayname'], 'root')
            # personal information should be transmitted
            self.assertIn('firstname', root)
            self.assertIn('lastname', root)
            self.assertIn('fullname', root)
            self.assertIn('email', root)

    def test_users_info_restricted(self):
        user = UserFactory(system_role=SystemRole.student)

        with self.login(user.username, user.password):
            rv = self.client.get('/api/users/' + DefaultFixture.ROOT_USER.uuid)
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

    def test_create_user(self):
        url = '/api/users'

        # test login required
        expected = UserFactory.stub(system_role=SystemRole.student.value)
        rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_authorized_student().username):
            expected = UserFactory.stub(system_role=SystemRole.student.value)
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json', record='unauthorized')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            expected = UserFactory.stub(system_role=SystemRole.student.value)
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json', record='unauthorized')
            self.assert403(rv)

        # only system admins can create users
        with self.login('root'):
            # test duplicate username
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                username=self.data.get_authorized_student().username)
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json', record='duplicate_username')
            self.assertStatus(rv, 409)
            self.assertEqual("This username already exists. Please pick another.", rv.json['error'])

            # test duplicate student number
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                student_number=self.data.get_authorized_student().student_number)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual("This student number already exists. Please pick another.", rv.json['error'])

            # test creating student
            expected = UserFactory.stub(system_role=SystemRole.student.value)
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type="application/json", record='create_student')
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            # test creating instructor
            expected = UserFactory.stub(system_role=SystemRole.instructor.value)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            # test creating admin
            expected = UserFactory.stub(system_role=SystemRole.sys_admin.value)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

    def test_create_user_lti(self):
        url = '/api/users'
        lti_data = LTITestData()

        # test login required when LTI and oauth_create_user_link are not present
        expected = UserFactory.stub(system_role=SystemRole.student.value)
        rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
        self.assert401(rv)

        # Instructor - no context
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=None,
                roles="Instructor") as lti_response:
            self.assert200(lti_response)

            # test create instructor via lti session
            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.instructor, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)

            # verify not enrolled in any course
            self.assertEqual(len(user.user_courses), 0)

        # Instructor - with context not linked
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Instructor") as lti_response:
            self.assert200(lti_response)

            # test create instructor via lti session
            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.instructor, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)

            # verify not enrolled in any course
            self.assertEqual(len(user.user_courses), 0)

        # Instructor - with context linked
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Instructor") as lti_response:
            self.assert200(lti_response)

            lti_context = LTIContext.query.all()[-1]
            course = self.data.create_course()
            lti_context.acj_course_id = course.id
            db.session.commit()

            # test create instructor via lti session
            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.instructor, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)

            # verify enrolled in course
            self.assertEqual(len(user.user_courses), 1)
            self.assertEqual(user.user_courses[0].course_id, course.id)

        # test create student via lti session
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Student") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)

        # test create teaching assistant (student role) via lti session
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="TeachingAssistant") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)


    def test_create_user_lti_and_CAS(self):
        url = '/api/users'
        lti_data = LTITestData()
        auth_data = ThirdPartyAuthTestData()

        with self.client.session_transaction() as sess:
            sess['CAS_CREATE'] = True
            sess['CAS_UNIQUE_IDENTIFIER'] = "some_unique_identifier"
            self.assertIsNone(sess.get('LTI'))

        # test login required when LTI and oauth_create_user_link are not present (even when CAS params are present)
        expected = UserFactory.stub(system_role=SystemRole.student.value)
        rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
        self.assert401(rv)

        # test create student via lti session
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Student") as lti_response:
            self.assert200(lti_response)

            with self.client.session_transaction() as sess:
                sess['CAS_CREATE'] = True
                sess['CAS_UNIQUE_IDENTIFIER'] = "some_unique_identifier"
                self.assertTrue(sess.get('LTI'))

            expected = UserFactory.stub(system_role=None)
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNone(user.password)
            self.assertIsNone(user.username)

            third_party_user = ThirdPartyUser.query \
                .filter_by(
                    third_party_type=ThirdPartyType.cwl,
                    unique_identifier="some_unique_identifier",
                    user_id=user.id
                ) \
                .one_or_none()

            self.assertIsNotNone(third_party_user)

            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('CAS_LOGIN'))
                self.assertIsNone(sess.get('CAS_CREATE'))
                self.assertIsNone(sess.get('CAS_UNIQUE_IDENTIFIER'))
                self.assertIsNone(sess.get('oauth_create_user_link'))


    def test_edit_user(self):
        user = self.data.get_authorized_student()
        url = 'api/users/' + user.uuid
        expected = {
            'id': user.uuid,
            'username': user.username,
            'student_number': user.student_number,
            'system_role': user.system_role.value,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'displayname': user.displayname,
            'email': user.email
        }
        instructor = self.data.get_authorized_instructor()
        instructor_url = 'api/users/' + instructor.uuid
        expected_instructor = {
            'id': instructor.uuid,
            'username': instructor.username,
            'student_number': instructor.student_number,
            'system_role': instructor.system_role.value,
            'firstname': instructor.firstname,
            'lastname': instructor.lastname,
            'displayname': instructor.displayname,
            'email': instructor.email
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

        # test invalid user id
        with self.login('root'):
            rv = self.client.post('/api/users/999', data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test unmatched user's id
            invalid_url = '/api/users/' + self.data.get_unauthorized_instructor().uuid
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
            duplicate['student_number'] = self.data.get_unauthorized_student().student_number
            rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual("This student number already exists. Please pick another.", rv.json['error'])

            # test successful update by admin
            valid = expected.copy()
            valid['displayname'] = "displayzzz"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("displayzzz", rv.json['displayname'])

        # test successful update by user (as instructor)
        with self.login(self.data.get_authorized_instructor().username):
            valid = expected_instructor.copy()
            valid['displayname'] = "thebest"
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])

        # test successful update by user (as student)
        with self.login(self.data.get_authorized_student().username):
            valid = expected.copy()
            valid['displayname'] = "thebest"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])

        # test updating username, student number, usertype for system - instructor
        with self.login(instructor.username):
            # for student
            valid = expected.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.username, rv.json['username'])

            valid = expected.copy()
            valid['student_number'] = "999999999999"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.student_number, rv.json['student_number'])

            valid = expected.copy()
            valid['system_role'] = SystemRole.student.value
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.system_role.value, rv.json['system_role'])

            # for instructor
            valid = expected_instructor.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.username, rv.json['username'])

            ignored = expected_instructor.copy()
            ignored['student_number'] = "999999999999"
            rv = self.client.post(instructor_url, data=json.dumps(ignored), content_type='application/json')
            self.assert200(rv)
            self.assertIsNone(rv.json['student_number'])
            self.assertEqual(instructor.student_number, rv.json['student_number'])

            valid = expected_instructor.copy()
            valid['system_role'] = SystemRole.student.value
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.system_role.value, rv.json['system_role'])

        # test updating username, student number, usertype for system - admin
        with self.login('root'):
            # for student
            valid = expected.copy()
            valid['username'] = 'newUsername'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('newUsername', rv.json['username'])

            valid = expected.copy()
            valid['student_number'] = '99999999'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('99999999', rv.json['student_number'])

            valid = expected.copy()
            valid['system_role'] = SystemRole.student.value
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.system_role.value, rv.json['system_role'])

            # for instructor
            valid = expected_instructor.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.username, rv.json['username'])

            ignored = expected_instructor.copy()
            ignored['student_number'] = "999999999999"
            rv = self.client.post(instructor_url, data=json.dumps(ignored), content_type='application/json')
            self.assert200(rv)
            self.assertIsNone(rv.json['student_number'])
            self.assertEqual(instructor.student_number, rv.json['student_number'])

            valid = expected_instructor.copy()
            valid['system_role'] = SystemRole.student.value
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.system_role.value, rv.json['system_role'])

        # test edit user with no acj login
        auth_data = ThirdPartyAuthTestData()
        cas_user_auth = auth_data.create_cas_user_auth(SystemRole.student)
        user = cas_user_auth.user
        self.data.enrol_user(user, self.data.get_course(), CourseRole.student)

        url = 'api/users/' + user.uuid
        expected = {
            'id': user.uuid,
            'username': user.username,
            'student_number': user.student_number,
            'system_role': user.system_role.value,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'displayname': user.displayname,
            'email': user.email
        }

        # edit own profile as cas user
        with self.cas_login(cas_user_auth.unique_identifier):
            # cannot change username (must be None)
            valid = expected.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertIsNone(user.username)

        # test updating username as instructor
        with self.login(instructor.username):
            # cannot change username (must be None)
            valid = expected.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertIsNone(user.username)


    def test_get_course_list(self):
        # test login required
        url = '/api/users/courses'
        rv = self.client.get(url)
        self.assert401(rv)

        with self.login('root'):
            # test admin
            url = '/api/users/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json['objects']))

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

            # test search filter
            url = '/api/users/courses?search='+self.data.get_course().name
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

            # test search filter
            url = '/api/users/courses?search=notfounds'+self.data.get_course().name
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

        # test authorized student
        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

        # test authorized teaching assistant
        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

        # test dropped instructor
        with self.login(self.data.get_dropped_instructor().username):
            url = '/api/users/courses'
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
        url = '/api/users/{}/password'
        data = {
            'oldpassword': 'password',
            'newpassword': 'abcd1234'
        }

        # test login required
        rv = self.client.post(
            url.format(self.data.authorized_instructor.uuid),
            data=json.dumps(data), content_type='application/json')
        self.assert401(rv)

        # test student update password
        with self.login(self.data.authorized_student.username):
            # test without old password
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps({'newpassword': '123456'}),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual(
                'The old password is incorrect or you do not have permission to change password.',
                rv.json['error'])

            # test incorrect old password
            invalid_input = data.copy()
            invalid_input['oldpassword'] = 'wrong'
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(invalid_input), content_type='application/json')
            self.assert403(rv)
            self.assertEqual(
                'The old password is incorrect or you do not have permission to change password.',
                rv.json['error'])

            # test with old password
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(data),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])

        # test instructor update password
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url.format(str(999)), data=json.dumps(data), content_type='application/json')
            self.assert404(rv)

            # test instructor changes the password of a student in the course
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps(data),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])

            # test changing own password
            rv = self.client.post(
                url.format(self.data.get_authorized_instructor().uuid),
                data=json.dumps(data), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_instructor().uuid, rv.json['id'])

        # test instructor changes the password of a student not in the course
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps(data),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual(
                '<p>{} does not have edit access to {}</p>'.format(self.data.get_unauthorized_instructor().username,
                                                                   self.data.get_authorized_student().username),
                rv.json['message'])

        # test admin update password
        with self.login('root'):
            # test admin changes student password without old password
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps({'newpassword': '123456'}),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])


        # test update password of user with no acj login
        auth_data = ThirdPartyAuthTestData()
        cas_user_auth = auth_data.create_cas_user_auth(SystemRole.student)
        user = cas_user_auth.user
        self.data.enrol_user(user, self.data.get_course(), CourseRole.student)
        url = 'api/users/' + user.uuid + '/password'

        # update own password as cas user
        with self.cas_login(cas_user_auth.unique_identifier):
            # cannot change password
            rv = self.client.post(url, data=json.dumps(data), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Cannot update password. User does not use ComPAIR account login authentication method.", rv.json['error'])

    def test_get_edit_button(self):
        url = '/api/users/' + self.data.get_authorized_student().uuid + '/edit'

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

    def _verify_permissions(self, user_id, permissions):
        user = User.query.get(user_id)
        with self.app.app_context():
            # can't figure out how to get into logged in app context, so just force a login here
            login_user(user, force=True)
            admin = user.system_role == SystemRole.sys_admin
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
            'id': user.uuid,
            'display': user.fullname + ' (' + user.displayname + ') - ' + user.system_role,
            'name': user.fullname}
