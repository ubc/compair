# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock
import six

from data.fixtures import DefaultFixture
from data.fixtures.test_data import SimpleAssignmentTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink, ThirdPartyType, ThirdPartyUser
from compair.core import db

class LoginAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LoginAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()

    def test_app_login(self):
        params = {
            'username': 'root',
            'password': 'password'
        }
        # test app login disabled
        self.app.config['APP_LOGIN_ENABLED'] = False
        rv = self.client.post('/api/login', data=json.dumps(params), content_type='application/json', follow_redirects=True)
        self.assert403(rv)

        # test app login enabled
        self.app.config['APP_LOGIN_ENABLED'] = True
        rv = self.client.post('/api/login', data=json.dumps(params), content_type='application/json', follow_redirects=True)
        self.assert200(rv)

    def test_logout(self):
        with self.login('root'):
            url = '/api/logout'
            rv = self.client.delete(url)
            self.assert200(rv)

        # can't logout during impersonation
        with self.impersonate(DefaultFixture.ROOT_USER, self.data.get_authorized_student()):
            url = '/api/logout'
            rv = self.client.delete(url)
            self.assert403(rv)
            self.assertTrue(rv.json['disabled_by_impersonation'])

    def test_cas_login(self):
        auth_data = ThirdPartyAuthTestData()

        # test login new user
        for system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
            unique_identifier = system_role.value + "_no_attributes"
            response_mock = mock.MagicMock()
            response_mock.success = True
            response_mock.user = unique_identifier
            response_mock.attributes = None

            self.app.config['CAS_ATTRIBUTE_FIRST_NAME'] = None
            self.app.config['CAS_ATTRIBUTE_LAST_NAME'] = None
            self.app.config['CAS_ATTRIBUTE_STUDENT_NUMBER'] = None
            self.app.config['CAS_ATTRIBUTE_EMAIL'] = None
            self.app.config['CAS_ATTRIBUTE_USER_ROLE'] = None
            self.app.config['CAS_INSTRUCTOR_ROLE_VALUES'] = {}
            self.app.config['CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = None

            with mock.patch('compair.api.login.validate_cas_ticket', return_value=response_mock):
                # test cas login disabled
                self.app.config['CAS_LOGIN_ENABLED'] = False
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert403(rv)

                # test cas login enabled with unsuccessful login
                self.app.config['CAS_LOGIN_ENABLED'] = True
                response_mock.success = False
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)

                # check session
                with self.client.session_transaction() as sess:
                    # check that user is logged in
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_TYPE'), 'CAS')
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_MSG'), 'Login Failed. CAS ticket was invalid.')

                # test cas login enabled with unsuccessful login
                response_mock.success = True
                response_mock.user = None
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)

                # check session
                with self.client.session_transaction() as sess:
                    # check that user is logged in
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_TYPE'), 'CAS')
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_MSG'), 'Login Failed. Expecting CAS username to be set.')

                # test cas login enabled with successful login
                response_mock.user = unique_identifier
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertIsNone(third_party_user.user.firstname)
                self.assertIsNone(third_party_user.user.lastname)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                self.assertIsNone(third_party_user.user.email)
                self.assertIsNone(third_party_user.user.student_number)
                self.assertIsNone(third_party_user.user.global_unique_identifier)

                with self.client.session_transaction() as sess:
                    self.assertEqual(sess.get('_user_id'), str(third_party_user.user.id))

                # unused attributes
                unique_identifier = system_role.value + "_with_unused_attributes"
                response_mock.user = unique_identifier
                response_mock.attributes = {
                    'firstName': 'f_name',
                    'lastName': 'l_name',
                    'studentNumber': "student1" if system_role == SystemRole.student else None,
                    'email': 'email@email.com',
                    'system_role_field': system_role.value,
                    'puid': system_role.value+"_puid",
                }

                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertIsNone(third_party_user.user.firstname)
                self.assertIsNone(third_party_user.user.lastname)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                self.assertIsNone(third_party_user.user.email)
                self.assertIsNone(third_party_user.user.student_number)
                self.assertIsNone(third_party_user.user.global_unique_identifier)

                # used attributes and no valid instructor values
                self.app.config['CAS_ATTRIBUTE_FIRST_NAME'] = 'firstName'
                self.app.config['CAS_ATTRIBUTE_LAST_NAME'] = 'lastName'
                self.app.config['CAS_ATTRIBUTE_STUDENT_NUMBER'] = 'studentNumber'
                self.app.config['CAS_ATTRIBUTE_EMAIL'] = 'email'
                self.app.config['CAS_ATTRIBUTE_USER_ROLE'] = 'system_role_field'
                self.app.config['CAS_INSTRUCTOR_ROLE_VALUES'] = {}
                self.app.config['CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = 'puid'
                unique_identifier = system_role.value + "_with_used_attributes"
                response_mock.user = unique_identifier

                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas) \
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertEqual(third_party_user.user.firstname, 'f_name')
                self.assertEqual(third_party_user.user.lastname, 'l_name')
                self.assertEqual(third_party_user.user.email, 'email@email.com')
                self.assertEqual(third_party_user.user.global_unique_identifier, system_role.value+"_puid")
                if system_role == SystemRole.student:
                    self.assertEqual(third_party_user.user.student_number, 'student1')
                else:
                    self.assertIsNone(third_party_user.user.student_number)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")

                # used attributes and valid instructor values
                unique_identifier = system_role.value + "_with_used_attributes2"
                response_mock.user = unique_identifier
                if system_role == SystemRole.student:
                    response_mock.attributes['studentNumber'] = "student2"
                response_mock.attributes['puid'] = system_role.value+"_puid2"
                self.app.config['CAS_INSTRUCTOR_ROLE_VALUES'] = {SystemRole.sys_admin.value, SystemRole.instructor.value}

                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.firstname, 'f_name')
                self.assertEqual(third_party_user.user.lastname, 'l_name')
                self.assertEqual(third_party_user.user.email, 'email@email.com')
                self.assertEqual(third_party_user.user.global_unique_identifier, system_role.value+"_puid2")
                if system_role == SystemRole.student:
                    self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                    six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                    self.assertEqual(third_party_user.user.student_number, 'student2')
                else:
                    self.assertEqual(third_party_user.user.system_role, SystemRole.instructor)
                    self.assertEqual(third_party_user.user.displayname, "f_name l_name")
                    self.assertIsNone(third_party_user.user.student_number)

        # test login existing user
        for system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
            self.app.config['CAS_ATTRIBUTE_FIRST_NAME'] = None
            self.app.config['CAS_ATTRIBUTE_LAST_NAME'] = None
            self.app.config['CAS_ATTRIBUTE_STUDENT_NUMBER'] = None
            self.app.config['CAS_ATTRIBUTE_EMAIL'] = None
            self.app.config['CAS_ATTRIBUTE_USER_ROLE'] = None
            self.app.config['CAS_INSTRUCTOR_ROLE_VALUES'] = {}
            self.app.config['CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = None

            user = self.data.create_user(system_role)
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.cas)

            original_firstname = user.firstname
            original_lastname = user.lastname
            original_email = user.email
            original_student_number = user.student_number
            new_student_number = original_student_number+"123" if user.student_number else None

            response_mock = mock.MagicMock()
            response_mock.success = True
            response_mock.user = third_party_user.unique_identifier
            response_mock.attributes = None

            with mock.patch('compair.api.login.validate_cas_ticket', return_value=response_mock):
                # test cas login disabled
                self.app.config['CAS_LOGIN_ENABLED'] = False
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert403(rv)

                # test cas login enabled
                self.app.config['CAS_LOGIN_ENABLED'] = True
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)

                # test overwrite disabled with no attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with no attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with no attributes
                self.app.config['CAS_ATTRIBUTE_FIRST_NAME'] = 'firstName'
                self.app.config['CAS_ATTRIBUTE_LAST_NAME'] = 'lastName'
                self.app.config['CAS_ATTRIBUTE_STUDENT_NUMBER'] = 'studentNumber'
                self.app.config['CAS_ATTRIBUTE_EMAIL'] = 'email'
                self.app.config['CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = 'puid'
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                response_mock.attributes = {
                    'firstName': 'f_name',
                    'lastName': 'l_name',
                    'studentNumber': new_student_number,
                    'email': 'email@email.com',
                    'puid': 'should_be_ignored_since_already_linked'
                }

                # test overwrite disabled with attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)

                if system_role == SystemRole.student:
                    self.assertEqual(user.firstname, 'f_name')
                    self.assertEqual(user.lastname, 'l_name')
                    self.assertEqual(user.email, 'email@email.com')
                    self.assertEqual(user.student_number, new_student_number)
                else:
                    self.assertEqual(user.firstname, original_firstname)
                    self.assertEqual(user.lastname, original_lastname)
                    self.assertEqual(user.email, original_email)
                    self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

            self.app.config['CAS_ATTRIBUTE_USER_ROLE'] = 'system_role_field'
            self.app.config['CAS_INSTRUCTOR_ROLE_VALUES'] = {SystemRole.instructor.value}
            # test automatic upgrading of system role for existing accounts
            for third_party_system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
                user = self.data.create_user(system_role)
                third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.cas)
                db.session.commit()

                response_mock.user = third_party_user.unique_identifier
                response_mock.attributes = {
                    'system_role_field': third_party_system_role.value
                }

                with mock.patch('compair.api.login.validate_cas_ticket', return_value=response_mock):
                    rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                    self.assert200(rv)

                    # compair user system role will upgrade
                    if system_role == SystemRole.student:
                        # cannot upgrade to admin
                        if third_party_system_role == SystemRole.instructor:
                            self.assertEqual(user.system_role, SystemRole.instructor)
                        else:
                            self.assertEqual(user.system_role, SystemRole.student)
                    elif system_role == SystemRole.instructor:
                        # cannot upgrade to admin and shouldn't downgrade to student
                        self.assertEqual(user.system_role, SystemRole.instructor)
                    elif system_role == SystemRole.sys_admin:
                        # shouldn't downgrade
                        self.assertEqual(user.system_role, SystemRole.sys_admin)

    def test_saml_login(self):
        auth_data = ThirdPartyAuthTestData()

        # test login new user
        for system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
            unique_identifier = system_role.value + "_no_attributes"
            response_mock = mock.MagicMock()
            response_mock.__errors = []
            response_mock.is_authenticated.return_value = True
            response_mock.get_attributes.return_value = {
                'urn:oid:0.9.2342.19200300.100.1.1': [unique_identifier]
            }
            response_mock.get_nameid.return_value = "saml_mock_nameid"
            response_mock.get_session_index.return_value = "saml_session_index"

            self.app.config['SAML_ATTRIBUTE_FIRST_NAME'] = None
            self.app.config['SAML_ATTRIBUTE_LAST_NAME'] = None
            self.app.config['SAML_ATTRIBUTE_STUDENT_NUMBER'] = None
            self.app.config['SAML_ATTRIBUTE_EMAIL'] = None
            self.app.config['SAML_ATTRIBUTE_USER_ROLE'] = None
            self.app.config['SAML_INSTRUCTOR_ROLE_VALUES'] = {}
            self.app.config['SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = None

            with mock.patch('compair.api.login.get_saml_auth_response', return_value=response_mock):
                # test saml login disabled
                self.app.config['SAML_LOGIN_ENABLED'] = False
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert403(rv)

                # test saml login enabled with unsuccessful login
                self.app.config['SAML_LOGIN_ENABLED'] = True
                response_mock.is_authenticated.return_value = False
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)

                # check session
                with self.client.session_transaction() as sess:
                    # check that user is logged in
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_TYPE'), 'SAML')
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_MSG'), 'Login Failed.')

                # test saml login enabled with unsuccessful login
                response_mock.is_authenticated.return_value = True
                response_mock.__errors = ['error1', 'error2']
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)

                # check session
                with self.client.session_transaction() as sess:
                    # check that user is logged in
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_TYPE'), 'SAML')
                    self.assertEqual(sess.get('THIRD_PARTY_AUTH_ERROR_MSG'), 'Login Failed.')

                # test saml login enabled with successful login
                response_mock.__errors = []
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertIsNone(third_party_user.user.firstname)
                self.assertIsNone(third_party_user.user.lastname)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                self.assertIsNone(third_party_user.user.email)
                self.assertIsNone(third_party_user.user.student_number)
                self.assertIsNone(third_party_user.user.global_unique_identifier)

                with self.client.session_transaction() as sess:
                    self.assertEqual(sess.get('_user_id'), str(third_party_user.user.id))

                # unused attributes
                unique_identifier = system_role.value + "_with_unused_attributes"
                response_mock.get_attributes.return_value = {
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': ['Member@testshib.org', 'Staff@testshib.org'],
                    'urn:oid:2.5.4.42': ['f_name'],
                    'urn:oid:0.9.2342.19200300.100.1.1': [unique_identifier],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': ['Member'],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.10': [None],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': [system_role.value],
                    'urn:oid:2.5.4.4': ['l_name'],
                    'urn:oid:2.5.4.3': ['Me Myself And I'],
                    'urn:oid:2.5.4.20': ['555-5555'],
                    'urn:oid:2.16.840.1.113730.3.1.3': ["student1"] if system_role == SystemRole.student else [],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': ['email@email.com']
                }

                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertIsNone(third_party_user.user.firstname)
                self.assertIsNone(third_party_user.user.lastname)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                self.assertIsNone(third_party_user.user.email)
                self.assertIsNone(third_party_user.user.student_number)
                self.assertIsNone(third_party_user.user.global_unique_identifier)

                # used attributes and no valid instructor values
                self.app.config['SAML_ATTRIBUTE_FIRST_NAME'] = 'urn:oid:2.5.4.42'
                self.app.config['SAML_ATTRIBUTE_LAST_NAME'] = 'urn:oid:2.5.4.4'
                self.app.config['SAML_ATTRIBUTE_STUDENT_NUMBER'] = 'urn:oid:2.16.840.1.113730.3.1.3'
                self.app.config['SAML_ATTRIBUTE_EMAIL'] = 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6'
                self.app.config['SAML_ATTRIBUTE_USER_ROLE'] = 'urn:oid:1.3.6.1.4.1.5923.1.1.1.7'
                self.app.config['SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = 'puid'
                self.app.config['SAML_INSTRUCTOR_ROLE_VALUES'] = {}
                unique_identifier = system_role.value + "_with_used_attributes"
                response_mock.get_attributes.return_value = {
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': ['Member@testshib.org', 'Staff@testshib.org'],
                    'urn:oid:2.5.4.42': ['f_name'],
                    'urn:oid:0.9.2342.19200300.100.1.1': [unique_identifier],
                    'puid': [system_role.value+"_puid"],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': ['Member'],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.10': [None],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': [system_role.value],
                    'urn:oid:2.5.4.4': ['l_name'],
                    'urn:oid:2.5.4.3': ['Me Myself And I'],
                    'urn:oid:2.5.4.20': ['555-5555'],
                    'urn:oid:2.16.840.1.113730.3.1.3': ["student1"] if system_role == SystemRole.student else [],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': ['email@email.com'],
                }

                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml) \
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                self.assertEqual(third_party_user.user.firstname, 'f_name')
                self.assertEqual(third_party_user.user.lastname, 'l_name')
                self.assertEqual(third_party_user.user.email, 'email@email.com')
                self.assertEqual(third_party_user.user.global_unique_identifier, system_role.value+"_puid")
                if system_role == SystemRole.student:
                    self.assertEqual(third_party_user.user.student_number, 'student1')
                else:
                    self.assertIsNone(third_party_user.user.student_number)
                six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")

                # used attributes and valid instructor values
                unique_identifier = system_role.value + "_with_used_attributes2"
                response_mock.get_attributes.return_value = {
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': ['Member@testshib.org', 'Staff@testshib.org'],
                    'urn:oid:2.5.4.42': ['f_name'],
                    'urn:oid:0.9.2342.19200300.100.1.1': [unique_identifier],
                    'puid': [system_role.value+"_puid2"],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': ['Member'],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.10': [None],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': [system_role.value],
                    'urn:oid:2.5.4.4': ['l_name'],
                    'urn:oid:2.5.4.3': ['Me Myself And I'],
                    'urn:oid:2.5.4.20': ['555-5555'],
                    'urn:oid:2.16.840.1.113730.3.1.3': ["student2"] if system_role == SystemRole.student else [],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': ['email@email.com']
                }
                self.app.config['SAML_INSTRUCTOR_ROLE_VALUES'] = {SystemRole.sys_admin.value, SystemRole.instructor.value}

                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml)\
                    .one()

                self.assertIsNotNone(third_party_user)
                self.assertIsNotNone(third_party_user.user)
                self.assertEqual(third_party_user.user.firstname, 'f_name')
                self.assertEqual(third_party_user.user.lastname, 'l_name')
                self.assertEqual(third_party_user.user.email, 'email@email.com')
                self.assertEqual(third_party_user.user.global_unique_identifier, system_role.value+"_puid2")
                if system_role == SystemRole.student:
                    self.assertEqual(third_party_user.user.system_role, SystemRole.student)
                    six.assertRegex(self, third_party_user.user.displayname, r"^Student_\d{8}")
                    self.assertEqual(third_party_user.user.student_number, 'student2')
                else:
                    self.assertEqual(third_party_user.user.system_role, SystemRole.instructor)
                    self.assertEqual(third_party_user.user.displayname, "f_name l_name")
                    self.assertIsNone(third_party_user.user.student_number)

        # test login existing user
        for system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
            self.app.config['SAML_ATTRIBUTE_FIRST_NAME'] = None
            self.app.config['SAML_ATTRIBUTE_LAST_NAME'] = None
            self.app.config['SAML_ATTRIBUTE_STUDENT_NUMBER'] = None
            self.app.config['SAML_ATTRIBUTE_EMAIL'] = None
            self.app.config['SAML_ATTRIBUTE_USER_ROLE'] = None
            self.app.config['SAML_INSTRUCTOR_ROLE_VALUES'] = {}
            self.app.config['SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = None

            user = self.data.create_user(system_role)
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.saml)

            original_firstname = user.firstname
            original_lastname = user.lastname
            original_email = user.email
            original_student_number = user.student_number
            new_student_number = original_student_number+"123" if user.student_number else None

            response_mock = mock.MagicMock()
            response_mock.__errors = []
            response_mock.is_authenticated.return_value = True
            response_mock.get_attributes.return_value = {
                'urn:oid:0.9.2342.19200300.100.1.1': [third_party_user.unique_identifier]
            }
            response_mock.get_nameid.return_value = "saml_mock_nameid"
            response_mock.get_session_index.return_value = "saml_session_index"

            with mock.patch('compair.api.login.get_saml_auth_response', return_value=response_mock):
                # test saml login disabled
                self.app.config['SAML_LOGIN_ENABLED'] = False
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert403(rv)

                # test saml login enabled
                self.app.config['SAML_LOGIN_ENABLED'] = True
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)

                # test overwrite disabled with no attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with no attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with no attributes
                self.app.config['SAML_ATTRIBUTE_FIRST_NAME'] = 'urn:oid:2.5.4.42'
                self.app.config['SAML_ATTRIBUTE_LAST_NAME'] = 'urn:oid:2.5.4.4'
                self.app.config['SAML_ATTRIBUTE_STUDENT_NUMBER'] = 'urn:oid:2.16.840.1.113730.3.1.3'
                self.app.config['SAML_ATTRIBUTE_EMAIL'] = 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6'
                self.app.config['SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD'] = 'puid'
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                response_mock.get_attributes.return_value = {
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': ['Member@testshib.org', 'Staff@testshib.org'],
                    'urn:oid:2.5.4.42': ['f_name'],
                    'urn:oid:0.9.2342.19200300.100.1.1': [third_party_user.unique_identifier],
                    'puid': ["should_be_ignored_since_already_linked"],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': ['Member', 'Staff'],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.10': [None],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': ['urn:mace:dir:entitlement:common-lib-terms'],
                    'urn:oid:2.5.4.4': ['l_name'],
                    'urn:oid:2.5.4.3': ['Me Myself And I'],
                    'urn:oid:2.5.4.20': ['555-5555'],
                    'urn:oid:2.16.840.1.113730.3.1.3': [new_student_number],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': ['email@email.com']
                }

                # test overwrite disabled with attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

                # test overwrite enabled with attributes
                self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
                self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False
                rv = self.client.post('/api/saml/auth', follow_redirects=True)
                self.assert200(rv)

                if system_role == SystemRole.student:
                    self.assertEqual(user.firstname, 'f_name')
                    self.assertEqual(user.lastname, 'l_name')
                    self.assertEqual(user.email, 'email@email.com')
                    self.assertEqual(user.student_number, new_student_number)
                else:
                    self.assertEqual(user.firstname, original_firstname)
                    self.assertEqual(user.lastname, original_lastname)
                    self.assertEqual(user.email, original_email)
                    self.assertEqual(user.student_number, original_student_number)
                self.assertIsNone(user.global_unique_identifier)

            self.app.config['SAML_ATTRIBUTE_USER_ROLE'] = 'urn:oid:1.3.6.1.4.1.5923.1.1.1.7'
            self.app.config['SAML_INSTRUCTOR_ROLE_VALUES'] = {SystemRole.instructor.value}
            # test automatic upgrading of system role for existing accounts
            for third_party_system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
                user = self.data.create_user(system_role)
                third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.saml)
                db.session.commit()

                response_mock.get_attributes.return_value = {
                    'urn:oid:0.9.2342.19200300.100.1.1': [third_party_user.unique_identifier],
                    'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': [third_party_system_role.value]
                }

                with mock.patch('compair.api.login.get_saml_auth_response', return_value=response_mock):
                    rv = self.client.post('/api/saml/auth', follow_redirects=True)
                    self.assert200(rv)

                    # compair user system role will upgrade
                    if system_role == SystemRole.student:
                        # cannot upgrade to admin
                        if third_party_system_role == SystemRole.instructor:
                            self.assertEqual(user.system_role, SystemRole.instructor)
                        else:
                            self.assertEqual(user.system_role, SystemRole.student)
                    elif system_role == SystemRole.instructor:
                        # cannot upgrade to admin and shouldn't downgrade to student
                        self.assertEqual(user.system_role, SystemRole.instructor)
                    elif system_role == SystemRole.sys_admin:
                        # shouldn't downgrade
                        self.assertEqual(user.system_role, SystemRole.sys_admin)

    def test_saml_metadata(self):
        # test saml login enabled
        self.app.config['SAML_LOGIN_ENABLED'] = True
        self.app.config['SAML_EXPOSE_METADATA_ENDPOINT'] = True
        rv = self.client.get('/api/saml/metadata', headers={'Accept': 'text/xml'})
        self.assert200(rv)

        # test saml login disabled
        self.app.config['SAML_LOGIN_ENABLED'] = False
        self.app.config['SAML_EXPOSE_METADATA_ENDPOINT'] = True
        rv = self.client.get('/api/saml/metadata', headers={'Accept': 'text/xml'})
        self.assert404(rv)

        # test saml metadata disabled
        self.app.config['SAML_LOGIN_ENABLED'] = True
        self.app.config['SAML_EXPOSE_METADATA_ENDPOINT'] = False
        rv = self.client.get('/api/saml/metadata', headers={'Accept': 'text/xml'})
        self.assert404(rv)
