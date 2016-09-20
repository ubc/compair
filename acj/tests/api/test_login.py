import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, ThirdPartyAuthTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink
from acj.core import db
from oauthlib.common import generate_token, generate_nonce, generate_timestamp

class LoginAPITests(ACJAPITestCase):
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
        user = self.data.create_user(SystemRole.instructor)
        third_party_user = auth_data.create_third_party_user(user=user)

        with mock.patch('flask_cas.CAS.username', new_callable=mock.PropertyMock) as mocked_cas_username:
            # test cas login disabled
            self.app.config['CAS_LOGIN_ENABLED'] = False
            mocked_cas_username.return_value = third_party_user.unique_identifier
            rv = self.client.get('/api/auth/cas', data={}, content_type='application/json', follow_redirects=True)
            self.assert403(rv)

            # test cas login enabled
            self.app.config['CAS_LOGIN_ENABLED'] = True
            mocked_cas_username.return_value = third_party_user.unique_identifier
            rv = self.client.get('/api/auth/cas', data={}, content_type='application/json', follow_redirects=True)
            self.assert200(rv)
