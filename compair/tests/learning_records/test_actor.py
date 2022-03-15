# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock
import pytz
from six import text_type

from data.fixtures.test_data import SimpleAnswersTestData, ThirdPartyAuthTestData, \
    LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase
from compair.models import ThirdPartyType, SystemRole, CourseRole


from compair.core import db
from flask import current_app
from compair.learning_records import XAPIStatement, XAPIVerb, XAPIObject, \
    XAPIContext, XAPIResult, XAPI
from tincan import LRSResponse

from compair.learning_records.capture_events import on_assignment_modified

class AccountLearningRecordTests(ComPAIRLearningRecordTestCase):

    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = SimpleAnswersTestData()
        self.auth_data = ThirdPartyAuthTestData()
        self.lti_data = LTITestData()
        self.course = self.data.main_course
        self.assignment = self.data.assignments[0]

        self.user = self.data.create_user(SystemRole.instructor)
        self.data.enrol_user(self.user, self.data.get_course(), CourseRole.instructor)

        self.global_unique_identifier = 'mock_puid_è_global_unique_identifier'


    def test_actor_accounts(self):
        user = self.user

        # test without homepage set
        # (should use compair actor account)
        self.app.config['LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'] = True
        self.app.config['LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE'] = None
        expected_caliper_actor = self.get_compair_caliper_actor(user)
        expected_xapi_actor = self.get_compair_xapi_actor(user)

        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['actor'], expected_caliper_actor)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], expected_xapi_actor)

        # test with homepage set and global unique identifier not set
        # (should use compair actor account)
        self.app.config['LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE'] = "http://third.party.homepage"
        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['actor'], expected_caliper_actor)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], expected_xapi_actor)

        # test with homepage set and global unique identifier set
        user.global_unique_identifier = self.global_unique_identifier
        db.session.commit()
        expected_caliper_actor = self.get_unique_identifier_caliper_actor(
            user,
            "http://third.party.homepage/",
            self.global_unique_identifier
        )
        expected_xapi_actor = self.get_unique_identifier_xapi_actor(
            user,
            "http://third.party.homepage/",
            self.global_unique_identifier
        )
        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['actor'], expected_caliper_actor)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], expected_xapi_actor)

        # disabling LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER should skip checking global unique identifer
        self.app.config['LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'] = False
        expected_caliper_actor = self.get_compair_caliper_actor(user)
        expected_xapi_actor = self.get_compair_xapi_actor(user)
        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['actor'], expected_caliper_actor)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], expected_xapi_actor)

        # test adding third party auths & lti user links
        # NOTE: xapi doesn't really add this extra info to actor since there
        # isn't anywhere to put it
        cas_auth = self.auth_data.create_third_party_user(
            user=user, third_party_type=ThirdPartyType.cas
        )
        saml_auth = self.auth_data.create_third_party_user(
            user=user, third_party_type=ThirdPartyType.saml
        )
        lti_user = self.lti_data.create_user(
            self.lti_data.lti_consumer, SystemRole.instructor, user,
        )
        lti_user.student_number = '1234567890'
        lti_user.global_unique_identifier = self.global_unique_identifier
        lti_user.lis_person_sourcedid = 'asdfghjkl'
        db.session.commit()

        expected_caliper_actor = self.get_compair_caliper_actor(
            user, third_party_users=[cas_auth, saml_auth], lti_users=[lti_user]
        )
        expected_xapi_actor = self.get_compair_xapi_actor(
            user, third_party_users=[cas_auth, saml_auth], lti_users=[lti_user]
        )

        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        print(events[0]['actor'])
        self.assertEqual(events[0]['actor'], expected_caliper_actor)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]['actor'], expected_xapi_actor)
