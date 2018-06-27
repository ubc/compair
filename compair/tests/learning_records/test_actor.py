# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock
import pytz
from six import text_type

from data.fixtures.test_data import SimpleAnswersTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase
from compair.models import ThirdPartyType, SystemRole, CourseRole


from compair.core import db
from flask_login import current_app
from compair.learning_records import XAPIStatement, XAPIVerb, XAPIObject, \
    XAPIContext, XAPIResult, XAPI
from tincan import LRSResponse

from compair.learning_records.capture_events import on_assignment_modified

class AccountLearningRecordTests(ComPAIRLearningRecordTestCase):

    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
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
            self.app.config['LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'] = True
            self.app.config['LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE'] = None
            expected_actor = self.get_compair_xapi_actor(user)

            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_xapi_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # test with homepage set and global unique identifier not set
            # (should use compair actor account)
            self.app.config['LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE'] = "http://third.party.homepage"
            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_xapi_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)
            expected_actor = self.get_compair_xapi_actor(user)

            # test with homepage set and global unique identifier set
            # (should use cas/saml actor account with overridden value used for name)
            user.global_unique_identifier = 'mock_puid_è_'+third_party_auth.third_party_type.value
            db.session.commit()
            expected_actor = self.get_unique_identifier_xapi_actor(
                user,
                "http://third.party.homepage/",
                'mock_puid_è_'+third_party_auth.third_party_type.value
            )
            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_xapi_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)

            # disabling LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER should skip checking global unique identifer
            self.app.config['LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'] = False
            expected_actor = self.get_compair_xapi_actor(user)
            on_assignment_modified.send(
                current_app._get_current_object(),
                event_name=on_assignment_modified.name,
                user=user,
                assignment=self.assignment
            )
            statements = self.get_and_clear_xapi_statement_log()
            self.assertEqual(len(statements), 1)
            self.assertEqual(statements[0]['actor'], expected_actor)