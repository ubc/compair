import json
import mock
from six import text_type

from data.fixtures.test_data import SimpleAnswersTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRXAPITestCase
from compair.models import ThirdPartyType, SystemRole, CourseRole


from compair.core import db
from flask_login import current_app
from compair.xapi import XAPIStatement, XAPIVerb, XAPIObject, \
    XAPIContext, XAPIResult, XAPI
from tincan import LRSResponse

from compair.xapi.capture_events import on_assignment_modified

class AccountXAPITests(ComPAIRXAPITestCase):

    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = SimpleAnswersTestData()
        self.auth_data = ThirdPartyAuthTestData()
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]

        self.cas_user_auth = self.auth_data.create_cas_user_auth(SystemRole.instructor)
        self.cas_user = self.cas_user_auth.user
        self.data.enrol_user(self.cas_user, self.data.get_course(), CourseRole.instructor)

        self.saml_user_auth = self.auth_data.create_saml_user_auth(SystemRole.instructor)
        self.saml_user = self.saml_user_auth.user
        self.data.enrol_user(self.saml_user, self.data.get_course(), CourseRole.instructor)

    def test_actor_accounts(self):
        for user, third_party_auth in [(self.cas_user, self.cas_user_auth), (self.saml_user, self.saml_user_auth)]:

            # test without homepage set
            # (should use compair actor account)
            self.app.config['LRS_ACTOR_ACCOUNT_USE_THIRD_PARTY'] = True
            self.app.config['LRS_ACTOR_ACCOUNT_THIRD_PARTY_HOMEPAGE'] = None
            self.app.config['LRS_ACTOR_ACCOUNT_SAML_IDENTIFIER'] = None
            self.app.config['LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER'] = None
            expected_actor = self.get_compair_actor(user)

            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # test with homepage set
            # (should use cas/saml actor account with unique_identifier)
            self.app.config['LRS_ACTOR_ACCOUNT_THIRD_PARTY_HOMEPAGE'] = "http://third.party.homepage"
            expected_actor = self.get_third_party_actor(
                user,
                "http://third.party.homepage",
                third_party_auth.unique_identifier
            )

            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # test with homepage set and identifer override set with no value found
            # (should use compair actor account)
            if third_party_auth.third_party_type == ThirdPartyType.saml:
                self.app.config['LRS_ACTOR_ACCOUNT_SAML_IDENTIFIER'] = 'puid'
            elif third_party_auth.third_party_type == ThirdPartyType.cas:
                self.app.config['LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER'] = 'puid'
            expected_actor = self.get_compair_actor(user)

            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # test with homepage set and identifer override set
            # (should use cas/saml actor account with overridden value used for name)
            if third_party_auth.third_party_type == ThirdPartyType.saml:
                third_party_auth.params = {
                    'puid': ['mock_puid']
                }
            elif third_party_auth.third_party_type == ThirdPartyType.cas:
                third_party_auth.params = {
                    'puid': 'mock_puid'
                }
            db.session.commit()

            expected_actor = self.get_third_party_actor(
                user,
                "http://third.party.homepage",
                "mock_puid"
            )

            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # disabling LRS_ACTOR_ACCOUNT_USE_THIRD_PARTY should skip checking third party accounts
            self.app.config['LRS_ACTOR_ACCOUNT_USE_THIRD_PARTY'] = False

            expected_actor = self.get_compair_actor(user)
            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)