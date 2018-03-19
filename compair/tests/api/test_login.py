import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink
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

    def test_cas_login(self):
        auth_data = ThirdPartyAuthTestData()
        for system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
            user = self.data.create_user(system_role)
            third_party_user = auth_data.create_third_party_user(user=user)

            original_firstname = user.firstname
            original_lastname = user.lastname
            original_email = user.email
            original_student_number = user.student_number
            new_student_number = original_student_number+"123" if user.student_number else None

            response_mock = mock.MagicMock()
            response_mock.success = True
            response_mock.user =  third_party_user.unique_identifier
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

                # test overwrite enabled with no attributes
                self.app.config['CAS_ATTRIBUTE_FIRST_NAME'] = 'firstName'
                self.app.config['CAS_ATTRIBUTE_LAST_NAME'] = 'lastName'
                self.app.config['CAS_ATTRIBUTE_STUDENT_NUMBER'] = 'studentNumber'
                self.app.config['CAS_ATTRIBUTE_EMAIL'] = 'email'
                rv = self.client.get('/api/cas/auth?ticket=mock_ticket', follow_redirects=True)
                self.assert200(rv)
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertEqual(user.student_number, original_student_number)


            response_mock.attributes = {
                'firstName': 'f_name',
                'lastName': 'l_name',
                'studentNumber': new_student_number,
                'email': 'email@email.com'
            }

            with mock.patch('compair.api.login.validate_cas_ticket', return_value=response_mock):
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

                # test overwrite enabled with no attributes
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