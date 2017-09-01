import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink, ThirdPartyType
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
        user = self.data.create_user(SystemRole.instructor)
        third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.cas)

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

    def test_saml_login(self):
        auth_data = ThirdPartyAuthTestData()
        user = self.data.create_user(SystemRole.instructor)
        third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.saml)

        response_mock = mock.MagicMock()
        response_mock.get_errors.return_value = []
        response_mock.is_authenticated.return_value = True
        response_mock.get_attributes.return_value = {
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': ['Member@testshib.org', 'Staff@testshib.org'],
            'urn:oid:2.5.4.42': ['Me Myself'],
            'urn:oid:0.9.2342.19200300.100.1.1': ['myself'],
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': ['Member', 'Staff'],
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.10': [None],
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.7': ['urn:mace:dir:entitlement:common-lib-terms'],
            'urn:oid:2.5.4.4': ['And I'],
            'urn:oid:2.5.4.3': ['Me Myself And I'],
            'urn:oid:2.5.4.20': ['555-5555'],
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': ['myself@testshib.org']
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
