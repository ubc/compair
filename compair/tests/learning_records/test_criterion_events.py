# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask import current_app

from compair.learning_records.capture_events import on_criterion_create, \
    on_criterion_update

class CriterionLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student
        self.setup_session_data(self.user)
        self.criterion = self.data.create_criterion(self.user)

        self.expected_caliper_criterion = {
            'dateCreated': self.criterion.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.criterion.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': "https://localhost:8888/app/criterion/"+self.criterion.uuid,
            'name': self.criterion.name,
            'description': self.criterion.description,
            'type': 'DigitalResource'
        }

        self.expected_xapi_criterion = {
            'id': "https://localhost:8888/app/criterion/"+self.criterion.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.criterion.name},
                'description': {'en-US': self.criterion.description}
            },
            'objectType': 'Activity'
        }

    def test_on_criterion_create(self):
        on_criterion_create.send(
            current_app._get_current_object(),
            event_name=on_criterion_create.name,
            user=self.user,
            criterion=self.criterion
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Created',
            'profile': 'ResourceManagementProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': self.expected_caliper_criterion,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'ResourceManagementEvent'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)


        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/author',
                'display': {'en-US': 'authored'}
            },
            "object": self.expected_xapi_criterion,
            "context": {
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            }
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)


    def test_on_criterion_update(self):
        on_criterion_update.send(
            current_app._get_current_object(),
            event_name=on_criterion_update.name,
            user=self.user,
            criterion=self.criterion
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Modified',
            'profile': 'ResourceManagementProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': self.expected_caliper_criterion,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'ResourceManagementEvent'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)


        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/update',
                'display': {'en-US': 'updated'}
            },
            "object": self.expected_xapi_criterion,
            "context": {
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            }
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)
