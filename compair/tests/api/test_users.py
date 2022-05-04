# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime

from flask_bouncer import can, MANAGE, CREATE, EDIT, DELETE, READ
from flask_login import login_user, logout_user
from werkzeug.exceptions import Unauthorized

from data.fixtures import DefaultFixture, UserFactory, AssignmentFactory
from data.fixtures.test_data import BasicTestData, LTITestData, ThirdPartyAuthTestData, ComparisonTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, AnswerComment, AnswerCommentType, Comparison, \
    LTIContext, LTIUser, ThirdPartyUser, ThirdPartyType, WinningAnswer, EmailNotificationMethod
from compair.core import db


class UsersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(UsersAPITests, self).setUp()
        self.data = BasicTestData()

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
            self.assertIn('fullname_sortable', root)
            self.assertIn('email', root)

    def test_users_info_restricted(self):
        user = UserFactory(system_role=SystemRole.student)

        with self.login(user.username):
            rv = self.client.get('/api/users/' + DefaultFixture.ROOT_USER.uuid)
            self.assert200(rv)
            root = rv.json
            self.assertEqual(root['displayname'], 'root')
            # personal information shouldn't be transmitted
            self.assertNotIn('firstname', root)
            self.assertNotIn('lastname', root)
            self.assertNotIn('fullname', root)
            self.assertNotIn('fullname_sortable', root)
            self.assertNotIn('email', root)

        # impersonate as student and enquire info on admin
        with self.impersonate(DefaultFixture.ROOT_USER, user):
            rv = self.client.get('/api/users/' + DefaultFixture.ROOT_USER.uuid)
            self.assert200(rv)
            root = rv.json
            self.assertEqual(root['displayname'], 'root')
            # personal information shouldn't be transmitted
            self.assertNotIn('firstname', root)
            self.assertNotIn('lastname', root)
            self.assertNotIn('fullname', root)
            self.assertNotIn('fullname_sortable', root)
            self.assertNotIn('email', root)

        # don't show own email when being impersonated
        with self.impersonate(DefaultFixture.ROOT_USER, user):
            rv = self.client.get('/api/users/' + user.uuid)
            self.assert200(rv)
            user_info = rv.json
            self.assertEqual(user_info['displayname'], user.displayname)
            # email shouldn't be transmitted
            self.assertNotIn('email', user_info)

    def test_users_list(self):
        rv = self.client.get('/api/users')
        self.assert401(rv)

        student = self.data.authorized_student
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.authorized_instructor, student)]:
            with user_context:
                rv = self.client.get('/api/users')
                self.assert403(rv)

        with self.login('root'):
            expected = sorted(
                [user for user in self.data.users],
                key=lambda user: (user.lastname, user.firstname)
            )[:20]
            rv = self.client.get('/api/users')
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([u.uuid for u in expected], [u['id'] for u in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            rv = self.client.get('/api/users?search='+self.data.get_unauthorized_instructor().firstname)
            self.assert200(rv)
            self.assertEqual(self.data.get_unauthorized_instructor().uuid, rv.json['objects'][0]['id'])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

        with self.login(self.data.authorized_instructor.username):
            expected = sorted(
                [user for user in self.data.users],
                key=lambda user: (user.lastname, user.firstname)
            )[:20]
            rv = self.client.get('/api/users')
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([u.uuid for u in expected], [u['id'] for u in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            rv = self.client.get('/api/users?search='+self.data.get_unauthorized_instructor().firstname)
            self.assert200(rv)
            self.assertEqual(self.data.get_unauthorized_instructor().uuid, rv.json['objects'][0]['id'])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

    def test_create_user(self):
        url = '/api/users'

        # test login required
        expected = UserFactory.stub(
            system_role=SystemRole.student.value,
            email_notification_method=EmailNotificationMethod.enable.value
        )
        rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_authorized_student().username):
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assert403(rv)

        # should fail when root impersonating a student
        with self.impersonate(DefaultFixture.ROOT_USER, self.data.get_authorized_student()):
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assert403(rv)
            self.assertTrue(rv.json['disabled_by_impersonation'])

        # only system admins can create users
        with self.login('root'):
            # test duplicate username
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                username=self.data.get_authorized_student().username,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("Sorry, this username already exists and usernames must be unique in ComPAIR. Please enter another username and try saving again.", rv.json['message'])

            # test duplicate student number
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                student_number=self.data.get_authorized_student().student_number,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("Sorry, this student number already exists and student numbers must be unique in ComPAIR. Please enter another number and try saving again.", rv.json['message'])

            # test missing password
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value,
                password=None
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 400)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("A password is required. Please enter a password and try saving again.", rv.json['message'])

            # test short password
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value,
                password="123"
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 400)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("The password must be at least 4 characters long.", rv.json['message'])

            # test missing username
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value,
                username=None
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
            self.assertStatus(rv, 400)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("A username is required. Please enter a username and try saving again.", rv.json['message'])

            # test creating student
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(
                url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            # test creating instructor
            expected = UserFactory.stub(
                system_role=SystemRole.instructor.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            # test creating admin
            expected = UserFactory.stub(
                system_role=SystemRole.sys_admin.value,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            # test APP_LOGIN_ENABLED disabled
            self.app.config['APP_LOGIN_ENABLED'] = False

            # test creating student without username and password
            expected = UserFactory.stub(
                system_role=SystemRole.student.value,
                email_notification_method=EmailNotificationMethod.enable.value,
                username=None,
                password=None
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            self.app.config['APP_LOGIN_ENABLED'] = True

            # test creating student without first or last name
            for value in [None, ""]:
                expected = UserFactory.stub(
                    firstname=value,
                    lastname=value,
                    system_role=SystemRole.student.value,
                    email_notification_method=EmailNotificationMethod.enable.value
                )
                rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
                self.assert200(rv)
                self.assertIsNone(rv.json['firstname'])
                self.assertIsNone(rv.json['lastname'])

    def test_create_user_lti(self):
        url = '/api/users'
        lti_data = LTITestData()
        lti_data.get_consumer().student_number_param = 'custom_student_number'
        db.session.commit()

        # test login required when LTI and lti_create_user_link are not present
        expected = UserFactory.stub(
            system_role=SystemRole.student.value,
            email_notification_method=EmailNotificationMethod.enable.value
        )
        rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type='application/json')
        self.assert401(rv)

        # Instructor - no context
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=None,
                roles="Instructor") as lti_response:
            self.assert200(lti_response)

            # test create instructor via lti session
            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
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
            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
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
            lti_context.compair_course_id = course.id
            db.session.commit()

            # test create instructor via lti session
            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
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

        self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
        self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
        self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
        self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True

        # test create student via lti session (unblocked edit fields)
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Student", lis_person_name_given="f_student", lis_person_name_family="l_student",
                lis_person_contact_email_primary="student@email.com", custom_student_number="1234567") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)
            self.assertEqual(expected.firstname, user.firstname)
            self.assertEqual(expected.lastname, user.lastname)
            self.assertEqual(expected.email, user.email)
            self.assertEqual(expected.student_number, user.student_number)

        # test create teaching assistant (student role) via lti session (unblocked edit fields)
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="TeachingAssistant") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)

        self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
        self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
        self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
        self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False

        # test create student via lti session (blocked edit fields)
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="Student", lis_person_name_given="f_student", lis_person_name_family="l_student",
                lis_person_contact_email_primary="student@email.com", custom_student_number="1234567") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual(expected.username, user.username)
            self.assertEqual("f_student", user.firstname)
            self.assertEqual("l_student", user.lastname)
            self.assertEqual("student@email.com", user.email)
            self.assertEqual("1234567", user.student_number)

        # test create teaching assistant (student role) via lti session (blocked edit fields)
        with self.lti_launch(lti_data.get_consumer(), lti_data.generate_resource_link_id(),
                user_id=lti_data.generate_user_id(), context_id=lti_data.generate_context_id(),
                roles="TeachingAssistant", lis_person_name_given="f_ta", lis_person_name_family="l_ta",
                lis_person_contact_email_primary="ta@email.com", custom_student_number="12345678") as lti_response:
            self.assert200(lti_response)

            expected = UserFactory.stub(
                system_role=None,
                email_notification_method=EmailNotificationMethod.enable.value
            )
            rv = self.client.post(url, data=json.dumps(expected.__dict__), content_type="application/json")
            self.assert200(rv)
            self.assertEqual(expected.displayname, rv.json['displayname'])

            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(SystemRole.student, user.system_role)
            self.assertIsNotNone(user.password)
            self.assertEqual("f_ta", user.firstname)
            self.assertEqual("l_ta", user.lastname)
            self.assertEqual("ta@email.com", user.email)
            self.assertEqual("12345678", user.student_number)

    def test_edit_user(self):
        user = self.data.get_authorized_student()
        url = 'api/users/' + user.uuid
        expected = {
            'id': user.uuid,
            'username': user.username,
            'student_number': user.student_number,
            'system_role': user.system_role.value,
            'email_notification_method': user.email_notification_method.value,
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
            'email_notification_method': instructor.email_notification_method.value,
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

        # should fail during impersonation
        with self.impersonate(instructor, user):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)
            self.assertTrue(rv.json['disabled_by_impersonation'])
        with self.impersonate(DefaultFixture.ROOT_USER, user):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)
            self.assertTrue(rv.json['disabled_by_impersonation'])

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
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("Sorry, this username already exists and usernames must be unique in ComPAIR. Please enter another username and try saving again.", rv.json['message'])

            # test duplicate student number
            duplicate = expected.copy()
            duplicate['student_number'] = self.data.get_unauthorized_student().student_number
            rv = self.client.post(url, data=json.dumps(duplicate), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual("User Not Saved", rv.json['title'])
            self.assertEqual("Sorry, this student number already exists and student numbers must be unique in ComPAIR. Please enter another number and try saving again.", rv.json['message'])

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
            original_displayname = user.displayname
            original_firstname = user.firstname
            original_lastname = user.lastname
            original_student_number = user.student_number
            original_email = user.email

            valid = expected.copy()
            valid['displayname'] = "thebest"
            valid['firstname'] = "thebest"
            valid['lastname'] = "thebest"
            valid['student_number'] = "thebest"
            valid['email'] = "thebest@thebest"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(original_displayname, rv.json['displayname'])
            self.assertEqual(original_firstname, rv.json['firstname'])
            self.assertEqual(original_lastname, rv.json['lastname'])
            self.assertEqual(original_student_number, rv.json['student_number'])
            self.assertEqual(original_email, rv.json['email'])

            self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])
            self.assertEqual(original_firstname, rv.json['firstname'])
            self.assertEqual(original_lastname, rv.json['lastname'])
            self.assertEqual(original_student_number, rv.json['student_number'])
            self.assertEqual(original_email, rv.json['email'])

            self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])
            self.assertEqual("thebest", rv.json['firstname'])
            self.assertEqual("thebest", rv.json['lastname'])
            self.assertEqual(original_student_number, rv.json['student_number'])
            self.assertEqual(original_email, rv.json['email'])

            self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])
            self.assertEqual("thebest", rv.json['firstname'])
            self.assertEqual("thebest", rv.json['lastname'])
            self.assertEqual("thebest", rv.json['student_number'])
            self.assertEqual(original_email, rv.json['email'])

            self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual("thebest", rv.json['displayname'])
            self.assertEqual("thebest", rv.json['firstname'])
            self.assertEqual("thebest", rv.json['lastname'])
            self.assertEqual("thebest", rv.json['student_number'])
            self.assertEqual("thebest@thebest", rv.json['email'])

            self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False

        # test updating username, student number, first/last name, usertype for system - instructor
        with self.login(instructor.username):
            # for student

            # email and email email_notification_method not allowed by instructor
            invalid = expected.copy()
            invalid.pop('email_notification_method')
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)

            invalid = expected.copy()
            invalid.pop('email')
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)

            # email and email email_notification_method not allowed by instructor
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = True
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = False

            # for student
            expected_without_email = expected.copy()
            expected_without_email.pop('email')
            expected_without_email.pop('email_notification_method')

            valid = expected_without_email.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.username, rv.json['username'])

            valid = expected_without_email.copy()
            valid['student_number'] = "999999999999"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.student_number, rv.json['student_number'])

            valid = expected_without_email.copy()
            valid['system_role'] = SystemRole.student.value
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.system_role.value, rv.json['system_role'])

            valid = expected_without_email.copy()
            valid['firstname'] = 'thebest'
            valid['lastname'] = 'thebest'
            valid['displayname'] = 'thebest'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('thebest', rv.json['firstname'])
            self.assertEqual('thebest', rv.json['lastname'])
            self.assertEqual('thebest', rv.json['displayname'])

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
            valid['email_notification_method'] = EmailNotificationMethod.disable.value
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.email_notification_method.value, rv.json['email_notification_method'])

            for value in [None, ""]:
                valid = expected_instructor.copy()
                valid['firstname'] = value
                valid['lastname'] = value
                rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
                self.assert200(rv)
                self.assertIsNone(rv.json['firstname'])
                self.assertIsNone(rv.json['lastname'])

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

            valid = expected.copy()
            valid['email_notification_method'] = EmailNotificationMethod.disable.value
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(user.email_notification_method.value, rv.json['email_notification_method'])

            valid = expected.copy()
            valid['firstname'] = 'thebest'
            valid['lastname'] = 'thebest'
            valid['displayname'] = 'thebest'
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual('thebest', rv.json['firstname'])
            self.assertEqual('thebest', rv.json['lastname'])
            self.assertEqual('thebest', rv.json['displayname'])

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

            valid = expected_instructor.copy()
            valid['email_notification_method'] = EmailNotificationMethod.disable.value
            rv = self.client.post(instructor_url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(instructor.email_notification_method.value, rv.json['email_notification_method'])

        # test edit user with no compair login (cas)
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
            'email_notification_method': EmailNotificationMethod.enable.value,
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

        # test edit user with no compair login (saml)
        saml_user_auth = auth_data.create_saml_user_auth(SystemRole.student)
        user = saml_user_auth.user
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
            'email_notification_method': EmailNotificationMethod.enable.value,
            'email': user.email
        }

        # edit own profile as saml user
        with self.saml_login(saml_user_auth.unique_identifier):
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
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = True
            valid = expected.copy()
            valid['username'] = "wrongUsername"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertIsNone(user.username)
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = False

        # test updating username as system admin
        with self.login('root'):
            # admin can optionally change username
            valid = expected.copy()
            valid['username'] = ''
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertIsNone(user.username)

            valid = expected.copy()
            valid['username'] = "valid_username"
            rv = self.client.post(url, data=json.dumps(valid), content_type='application/json')
            self.assert200(rv)
            user = User.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(user.username, "valid_username")


    def test_get_current_user_course_list(self):
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

            # test sort order (when some courses have start_dates and other do not)
            url = '/api/users/courses'

            self.data.get_course().start_date = None
            self.data.get_course().created = datetime.datetime.now() - datetime.timedelta(days=10)

            course_2 = self.data.create_course()
            course_2.start_date = datetime.datetime.now()
            self.data.enrol_instructor(self.data.get_authorized_instructor(), course_2)

            course_3 = self.data.create_course()
            course_3.start_date = datetime.datetime.now() + datetime.timedelta(days=10)
            self.data.enrol_instructor(self.data.get_authorized_instructor(), course_3)

            courses = [course_3, course_2, self.data.get_course()]

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(3, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(courses[index].uuid, result['id'])

            # test sort order (when course with no start date has assignment)
            assignment = AssignmentFactory(
                user=self.data.get_authorized_instructor(),
                course=self.data.get_course(),
                answer_start=(datetime.datetime.now() + datetime.timedelta(days=5))
            )
            db.session.commit()

            courses = [course_3, self.data.get_course(), course_2]

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(3, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(courses[index].uuid, result['id'])

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

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            with self.impersonate(impersonator, self.data.get_authorized_student()):
                url = '/api/users/courses'
                rv = self.client.get(url)
                self.assert200(rv)
                self.assertEqual(1, len(rv.json['objects']))
                self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

    def test_get_user_lti_users_list(self):

        # setup
        lti_data = LTITestData()
        lti_consumer = lti_data.create_consumer()

        student1 = self.data.get_authorized_student()
        lti_user1 = lti_data.create_user(lti_consumer, SystemRole.student, student1)
        lti_user2 = lti_data.create_user(lti_consumer, SystemRole.student, student1)

        lti_users = [lti_user1, lti_user2]

        # sort by user_id (asc)
        lti_users.sort(key=lambda u: u.user_id)

        # test login required
        url = '/api/users/'+ student1.uuid +'/lti/users'
        rv = self.client.get(url)
        self.assert401(rv)

        # test non-admin
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/'+ student1.uuid +'/lti/users'
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/'+ student1.uuid +'/lti/users'
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/'+ student1.uuid +'/lti/users'
            rv = self.client.get(url)
            self.assert403(rv)

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                url = '/api/users/'+ impersonated.uuid +'/lti/users'
                rv = self.client.get(url)
                self.assert403(rv)

        # test admin
        with self.login('root'):
            # test invalid data
            url = '/api/users/999/lti/users'
            rv = self.client.get(url)
            self.assert404(rv)

            # test list content and sort order: by user_id (asc)
            url = '/api/users/'+ student1.uuid +'/lti/users'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(student1.uuid, rv.json['objects'][index]['compair_user_id'])
                self.assertEqual(lti_consumer.uuid, rv.json['objects'][index]['lti_consumer_id'])
                self.assertEqual(lti_users[index].user_id, rv.json['objects'][index]['lti_user_id'])

    def test_delete_user_lti_user(self):

        # setup
        lti_data = LTITestData()
        lti_consumer = lti_data.create_consumer()

        student1 = self.data.get_authorized_student()
        lti_user1 = lti_data.create_user(lti_consumer, SystemRole.student, student1)
        lti_user2 = lti_data.create_user(lti_consumer, SystemRole.student, student1)

        student2 = self.data.create_normal_user()
        lti_user1_2 = lti_data.create_user(lti_consumer, SystemRole.student, student2)

        # test login required
        url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
        rv = self.client.delete(url)
        self.assert401(rv)

        # test non-admin
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            with self.impersonate(impersonator, student1):
                url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
                rv = self.client.delete(url)
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

        # test admin
        with self.login('root'):
            # test invalid user
            url = '/api/users/999/lti/users/'+ lti_user1.uuid
            rv = self.client.delete(url)
            self.assert404(rv)

            # test invalid lti user
            url = '/api/users/'+ student1.uuid +'/lti/users/999'
            rv = self.client.delete(url)
            self.assert404(rv)

            # test valid
            url = '/api/users/'+ student1.uuid +'/lti/users/'+ lti_user1.uuid
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(rv.json['success'], True)

            lti_users = LTIUser.query \
                .filter_by(compair_user_id=student1.id) \
                .all()
            self.assertEqual(len(lti_users), 1)

    def test_get_user_third_party_users_list(self):

        # setup
        auth_data = ThirdPartyAuthTestData()

        student1 = self.data.get_authorized_student()
        third_party_user1 = auth_data.create_third_party_user(user=student1)
        third_party_user2 = auth_data.create_third_party_user(user=student1)

        third_party_users = [third_party_user1, third_party_user2]

        # sort by unique_identifier (asc)
        third_party_users.sort(key=lambda u: u.unique_identifier)

        # test login required
        url = '/api/users/'+ student1.uuid +'/third_party/users'
        rv = self.client.get(url)
        self.assert401(rv)

        # test non-admin
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users'
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users'
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users'
            rv = self.client.get(url)
            self.assert403(rv)

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                url = '/api/users/'+ impersonated.uuid +'/third_party/users'
                rv = self.client.get(url)
                self.assert403(rv)

        # test admin
        with self.login('root'):
            # test invalid data
            url = '/api/users/999/third_party/users'
            rv = self.client.get(url)
            self.assert404(rv)

            # test list length and sort order: by unique_identifier (asc)
            url = '/api/users/'+ student1.uuid +'/third_party/users'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(student1.uuid, rv.json['objects'][index]['user_id'])
                self.assertEqual(third_party_users[index].unique_identifier, rv.json['objects'][index]['unique_identifier'])

    def test_delete_user_third_party_user(self):

        # setup
        auth_data = ThirdPartyAuthTestData()

        student1 = self.data.get_authorized_student()
        third_party_user1 = auth_data.create_third_party_user(user=student1)
        third_party_user2 = auth_data.create_third_party_user(user=student1)

        student2 = self.data.create_normal_user()
        third_party_user1_2 = auth_data.create_third_party_user(user=student2)

        # test login required
        url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
        rv = self.client.delete(url)
        self.assert401(rv)

        # test non-admin
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
            rv = self.client.delete(url)
            self.assert403(rv)

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            with self.impersonate(impersonator, student1):
                url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
                rv = self.client.delete(url)
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

        # test admin
        with self.login('root'):
            # test invalid user
            url = '/api/users/999/third_party/users/'+ third_party_user1.uuid
            rv = self.client.delete(url)
            self.assert404(rv)

            # test invalid third party user
            url = '/api/users/'+ student1.uuid +'/third_party/users/999'
            rv = self.client.delete(url)
            self.assert404(rv)

            # test valid
            url = '/api/users/'+ student1.uuid +'/third_party/users/'+ third_party_user1.uuid
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(rv.json['success'], True)

            third_party_users = ThirdPartyUser.query \
                .filter_by(user_id=student1.id) \
                .all()
            self.assertEqual(len(third_party_users), 1)

    def test_get_user_course_list(self):
        # test login required
        url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses'
        rv = self.client.get(url)
        self.assert401(rv)

        with self.login('root'):
            # test invalid data
            url = '/api/users/999/courses'
            rv = self.client.get(url)
            self.assert404(rv)

            # test admin
            url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses'
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

            # test search filter
            url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses?search='+self.data.get_course().name
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(self.data.get_course().name, rv.json['objects'][0]['name'])

            # test search filter
            url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses?search=notfounds'+self.data.get_course().name
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test sort order (when some courses have start_dates and other do not)
            url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses'

            self.data.get_course().start_date = None
            self.data.get_course().created = datetime.datetime.now() - datetime.timedelta(days=10)

            course_2 = self.data.create_course()
            course_2.start_date = datetime.datetime.now()
            self.data.enrol_instructor(self.data.get_authorized_instructor(), course_2)

            course_3 = self.data.create_course()
            course_3.start_date = datetime.datetime.now() + datetime.timedelta(days=10)
            self.data.enrol_instructor(self.data.get_authorized_instructor(), course_3)

            courses = [course_3, course_2, self.data.get_course()]

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(3, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(courses[index].uuid, result['id'])

            # test sort order (when course with no start date has assignment)
            assignment = AssignmentFactory(
                user=self.data.get_authorized_instructor(),
                course=self.data.get_course(),
                answer_start=(datetime.datetime.now() + datetime.timedelta(days=5))
            )
            db.session.commit()

            courses = [course_3, self.data.get_course(), course_2]

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(3, len(rv.json['objects']))
            for index, result in enumerate(rv.json['objects']):
                self.assertEqual(courses[index].uuid, result['id'])

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/users/'+ self.data.get_authorized_instructor().uuid +'/courses'
            rv = self.client.get(url)
            self.assert403(rv)

        # test authorized student
        with self.login(self.data.get_authorized_student().username):
            url = '/api/users/'+ self.data.get_authorized_student().uuid +'/courses'
            rv = self.client.get(url)
            self.assert403(rv)

        # test authorized teaching assistant
        with self.login(self.data.get_authorized_ta().username):
            url = '/api/users/'+ self.data.get_authorized_ta().uuid +'/courses'
            rv = self.client.get(url)
            self.assert403(rv)

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                url = '/api/users/'+ impersonated.uuid +'/courses'
                rv = self.client.get(url)
                self.assert403(rv)

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

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                rv = self.client.get(url)
                self.assert200(rv)
                self.assertEqual(0, len(rv.json['courses']))

    def test_update_notification(self):
        url = '/api/users/{}/notification'
        data = {
            'email_notification_method': EmailNotificationMethod.disable.value,
        }

        # test login required
        rv = self.client.post(
            url.format(self.data.authorized_instructor.uuid),
            data=json.dumps(data), content_type='application/json')
        self.assert401(rv)

        # test student update notification settings
        with self.login(self.data.authorized_student.username):
            # test incorrect email notification method
            invalid_input = data.copy()
            invalid_input['email_notification_method'] = 'wrong'
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(invalid_input), content_type='application/json')
            self.assert400(rv)
            self.assertEqual('User Not Saved', rv.json['title'])
            self.assertEqual('Please try again with an email notification checked or unchecked.', rv.json['message'])

            # test success
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(data),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])
            self.assertEqual(self.data.get_authorized_student().email_notification_method.value, data['email_notification_method'])

        # test instructor update notification settings
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url.format("999"), data=json.dumps(data), content_type='application/json')
            self.assert404(rv)

            # test instructor changes the notification settings of a student in the course
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = True
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps(data),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])
            self.assertEqual(self.data.get_authorized_student().email_notification_method.value, data['email_notification_method'])

            # test instructor changes the notification settings of a student in the course
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = False
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps(data),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual('Notifications Not Updated', rv.json['title'])
            self.assertEqual("Sorry, your system role does not allow you to update notification settings for this user.",
                rv.json['message'])

            # test changing own notification settings
            rv = self.client.post(
                url.format(self.data.get_authorized_instructor().uuid),
                data=json.dumps(data), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_instructor().uuid, rv.json['id'])
            self.assertEqual(self.data.get_authorized_instructor().email_notification_method.value, data['email_notification_method'])

        # test admin update notification settings
        with self.login('root'):
            rv = self.client.post(url.format("999"), data=json.dumps(data), content_type='application/json')
            self.assert404(rv)

            # test admin changes student notification settings
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid),
                data=json.dumps(data), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])
            self.assertEqual(self.data.get_authorized_student().email_notification_method.value, data['email_notification_method'])

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                # test incorrect email notification method
                invalid_input = data.copy()
                invalid_input['email_notification_method'] = 'wrong'
                rv = self.client.post(
                    url.format(impersonated.uuid),
                    data=json.dumps(invalid_input), content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

                # test with correct format
                rv = self.client.post(
                    url.format(impersonated.uuid),
                    data=json.dumps(data),
                    content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

                # try to update impersonator
                rv = self.client.post(
                    url.format(impersonator.uuid),
                    data=json.dumps(data),
                    content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

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

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                # try to update impersonated
                rv = self.client.post(
                    url.format(impersonated.uuid),
                    data=json.dumps(data),
                    content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

                # try to update impersonator
                rv = self.client.post(
                    url.format(impersonator.uuid),
                    data=json.dumps(data),
                    content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

        # test student update password
        with self.login(self.data.authorized_student.username):
            # test without old password
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps({'newpassword': '123456'}),
                content_type='application/json')
            self.assert400(rv)
            self.assertEqual('Password Not Saved', rv.json['title'])
            self.assertEqual('Sorry, the old password is required. Please enter the old password and try saving again.', rv.json['message'])

            # test incorrect old password
            invalid_input = data.copy()
            invalid_input['oldpassword'] = 'wrong'
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(invalid_input), content_type='application/json')
            self.assert400(rv)
            self.assertEqual('Password Not Saved', rv.json['title'])
            self.assertEqual('Sorry, the old password is not correct. Please double-check the old password and try saving again.',
                rv.json['message'])

            # test short password
            invalid_input = data.copy()
            invalid_input['newpassword'] = '123'
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(invalid_input), content_type='application/json')
            self.assert400(rv)
            self.assertEqual('Password Not Saved', rv.json['title'])
            self.assertEqual('The new password must be at least 4 characters long.',
                rv.json['message'])

            # test with old password
            rv = self.client.post(
                url.format(self.data.authorized_student.uuid),
                data=json.dumps(data),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])

        # test instructor update password
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url.format("999"), data=json.dumps(data), content_type='application/json')
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
            self.assertEqual("Password Not Saved", rv.json['title'])
            self.assertEqual("Sorry, your system role does not allow you to update passwords for this user.",
                rv.json['message'])

        # test admin update password
        with self.login('root'):
            # test admin changes student password without old password
            rv = self.client.post(
                url.format(self.data.get_authorized_student().uuid), data=json.dumps({'newpassword': '123456'}),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(self.data.get_authorized_student().uuid, rv.json['id'])


        # test update password of user with no compair login
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
            self.assertEqual("Password Not Saved", rv.json['title'])
            self.assertEqual("Sorry, you cannot update the password since this user does not use the ComPAIR account login method.", rv.json['message'])

        saml_user_auth = auth_data.create_saml_user_auth(SystemRole.student)
        user = saml_user_auth.user
        self.data.enrol_user(user, self.data.get_course(), CourseRole.student)
        url = 'api/users/' + user.uuid + '/password'

        # update own password as saml user
        with self.saml_login(saml_user_auth.unique_identifier):
            # cannot change password
            rv = self.client.post(url, data=json.dumps(data), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Password Not Saved", rv.json['title'])
            self.assertEqual("Sorry, you cannot update the password since this user does not use the ComPAIR account login method.", rv.json['message'])

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

        # test with impersonation
        for impersonator in [DefaultFixture.ROOT_USER, self.data.get_authorized_instructor()]:
            impersonated = self.data.get_authorized_student()
            with self.impersonate(impersonator, impersonated):
                rv = self.client.get(url)
                self.assert200(rv)
                self.assertTrue(rv.json['available'])

    def _verify_permissions(self, user_id, permissions):
        operations = [MANAGE, CREATE, EDIT, DELETE, READ]

        user = User.query.get(user_id)
        with self.app.app_context():
            # can't figure out how to get into logged in app context, so just force a login here
            login_user(user, force=True)
            admin = user.system_role == SystemRole.sys_admin

            for model_name, permission_scopes in permissions.items():
                global_permissions = set(permission_scopes['global'])

                expected_operations = set()
                for operation in operations:
                    if admin or can(operation, model_name):
                        expected_operations.add(operation)

                self.assertEqual(global_permissions, expected_operations)

            # undo the forced login earlier
            logout_user()

class UsersCourseStatusAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(UsersCourseStatusAPITests, self).setUp()
        self.data = ComparisonTestData()

    def _create_enough_answers_for_assignment(self, assignment):
        course = assignment.course

        for i in range(assignment.number_of_comparisons*2):
            student = self.data.create_normal_user()
            self.data.enrol_student(student, course)
            self.data.create_answer(assignment, student)



    def _submit_all_comparisons_for_assignment(self, assignment, user_id):
        submit_count = 0

        for comparison_example in assignment.comparison_examples:
            comparison = Comparison.create_new_comparison(assignment.id, user_id, False)
            self.assertEqual(comparison.answer1_id, comparison_example.answer1_id)
            self.assertEqual(comparison.answer2_id, comparison_example.answer2_id)

            comparison.completed = True
            comparison.winner = WinningAnswer.answer1 if comparison.answer1_id < comparison.answer2_id else WinningAnswer.answer2
            for comparison_criterion in comparison.comparison_criteria:
                comparison_criterion.winner = comparison.winner
            db.session.add(comparison)

            submit_count += 1
            db.session.commit()

        for i in range(assignment.number_of_comparisons):
            comparison = Comparison.create_new_comparison(assignment.id, user_id, False)

            comparison.completed = True
            comparison.winner = WinningAnswer.answer1 if comparison.answer1_id < comparison.answer2_id else WinningAnswer.answer2
            for comparison_criterion in comparison.comparison_criteria:
                comparison_criterion.winner = comparison.winner
            db.session.add(comparison)

            submit_count += 1
            db.session.commit()

            Comparison.update_scores_1vs1(comparison)
        return submit_count

    def test_get_course_list(self):
        # test login required
        course = self.data.get_course()
        url = '/api/users/courses/status?ids='+course.uuid
        rv = self.client.get(url)
        self.assert401(rv)

        with self.login(self.data.get_authorized_student().username):
            # ids missing
            rv = self.client.get('/api/users/courses/status')
            self.assert400(rv)

            # empty ids
            rv = self.client.get('/api/users/courses/status?ids=')
            self.assert400(rv)

            # empty course doesn't exists
            rv = self.client.get('/api/users/courses/status?ids=999')
            self.assert400(rv)

            # test authorized student
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertIn(course.uuid, rv.json['statuses'])

            # test course with no assignments
            course = self.data.create_course()
            self.data.enrol_student(self.data.get_authorized_student(), course)
            self.data.enrol_instructor(self.data.get_authorized_instructor(), course)
            url = '/api/users/courses/status?ids='+course.uuid

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertIn(course.uuid, rv.json['statuses'])
            self.assertEqual(0, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 2 assignment
            self.data.create_assignment(course, self.data.get_authorized_instructor(),
                datetime.datetime.now() + datetime.timedelta(days=7), datetime.datetime.now() + datetime.timedelta(days=14))
            past_assignment = self.data.create_assignment(course, self.data.get_authorized_instructor(),
                datetime.datetime.now() - datetime.timedelta(days=28), datetime.datetime.now() - datetime.timedelta(days=21))
            past_assignment.compare_start = datetime.datetime.now() - datetime.timedelta(days=14)
            past_assignment.compare_end = datetime.datetime.now() - datetime.timedelta(days=7)
            db.session.commit()

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(0, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 3 assignment
            # - 1 in answering period
            answering_assignment = self.data.create_assignment_in_answer_period(course, self.data.get_authorized_instructor())

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(1, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 5 assignment
            # - 1 in answering period
            # - 1 in comparison_period
            # - 1 in comparison_period with self evaluation
            comparing_assignment = self.data.create_assignment_in_comparison_period(course, self.data.get_authorized_instructor())
            comparing_assignment_self_eval = self.data.create_assignment_in_comparison_period(course, self.data.get_authorized_instructor())
            comparing_assignment_self_eval.enable_self_evaluation = True
            db.session.commit()

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(3, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 5 assignment
            # - 1 in answering period (answered)
            # - 1 in comparison_period
            # - 1 in comparison_period with self evaluation
            self.data.create_answer(answering_assignment, self.data.get_authorized_student())

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(2, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 5 assignment
            # - 1 in answering period (answered)
            # - 1 in comparison_period (fully compared)
            # - 1 in comparison_period with self evaluation
            self._create_enough_answers_for_assignment(comparing_assignment)
            self._submit_all_comparisons_for_assignment(comparing_assignment, self.data.get_authorized_student().id)

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(1, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 5 assignment
            # - 1 in answering period (answered)
            # - 1 in comparison_period (fully compared)
            # - 1 in comparison_period with self evaluation (fully compared, not self-evaulated)
            self._create_enough_answers_for_assignment(comparing_assignment_self_eval)
            self._submit_all_comparisons_for_assignment(comparing_assignment_self_eval, self.data.get_authorized_student().id)

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(1, rv.json['statuses'][course.uuid]['incomplete_assignments'])

            # test course with 5 assignment
            # - 1 in answering period (answered)
            # - 1 in comparison_period (fully compared)
            # - 1 in comparison_period with self evaluation (fully compared and self-evaulated)
            answer = self.data.create_answer(comparing_assignment_self_eval, self.data.get_authorized_student())
            answer_comment = AnswerComment(
                user_id=self.data.get_authorized_student().id,
                answer_id=answer.id,
                comment_type=AnswerCommentType.self_evaluation,
                draft=False
            )
            db.session.add(answer_comment)
            db.session.commit()

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['statuses']))
            self.assertEqual(0, rv.json['statuses'][course.uuid]['incomplete_assignments'])
