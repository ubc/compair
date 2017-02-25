import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink
from compair.core import db
from oauthlib.common import generate_token, generate_nonce, generate_timestamp

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
        user = self.data.create_user(SystemRole.instructor)
        third_party_user = auth_data.create_third_party_user(user=user)

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
