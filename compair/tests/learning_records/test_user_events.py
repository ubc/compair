# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask import current_app

from compair.learning_records.capture_events import on_user_modified

class UserLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student
        self.setup_session_data(self.user)

    def test_on_user_modified(self):
        # no changes provided
        on_user_modified.send(
            current_app._get_current_object(),
            event_name=on_user_modified.name,
            user=self.user
        )

        expected_caliper_event = {
            'action': 'Modified',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': self.get_compair_caliper_actor(self.user),
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_verb = {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        }

        expected_xapi_context = {
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
            }
        }

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_xapi_verb,
            "object": self.get_compair_xapi_actor(self.user),
            "context": expected_xapi_context
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

        # test with changes
        changes = {
            'some_string': 'some_value',
            'some_number': 42,
            'some_dict': {
                'some_string': 'some_value',
                'some_number': 42
            }
        }
        on_user_modified.send(
            current_app._get_current_object(),
            event_name=on_user_modified.name,
            user=self.user,
            data={'changes': changes}
        )


        expected_caliper_event['extensions'] = {
            "changes": changes
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_statement['result'] = {
            'extensions': {'http://xapi.learninganalytics.ubc.ca/extension/changes': changes}
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)
