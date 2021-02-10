# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from compair.tests.test_compair import ComPAIRAPITestCase
from compair.api import register_learning_record_api_blueprints
from compair.models import XAPILog, CaliperLog

class LearningRecordsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LearningRecordsAPITests, self).setUp()

    def test_create_xapi_statement(self):
        self.app.config['LRS_XAPI_STATEMENT_ENDPOINT'] = 'local'
        url = '/api/learning_records/xapi/statements'

        statement = {
            "object": {
                "definition": {
                    "type": "http://activitystrea.ms/schema/1.0/service",
                    "name": {"en-US": "ComPAIR"}
                },
                "id": "https://archive.org/services/purl/compair/ctlt/",
                "objectType": "Activity"
            },
            "verb": {
                "id": "https://brindlewaye.com/xAPITerms/verbs/loggedin/",
                "display": {"en-US": "logged in"}
            }
        }

        # test XAPI_ENABLED needs to be set
        self.app.config['XAPI_ENABLED'] = False
        rv = self.client.post(url, data=json.dumps(statement), content_type='application/json')
        self.assert404(rv)

        # need to re-register api blueprints since we're changing XAPI_ENABLED
        self.app.config['XAPI_ENABLED'] = True
        self.app = register_learning_record_api_blueprints(self.app)

        # test login required
        rv = self.client.post(url, data=json.dumps(statement), content_type='application/json')
        self.assert401(rv)

        with self.login("root"):
            # test object required
            statement_invalid = statement.copy()
            del statement_invalid['object']
            rv = self.client.post(url, data=json.dumps(statement_invalid), content_type='application/json')
            self.assert400(rv)

            # test verb required
            statement_invalid = statement.copy()
            del statement_invalid['verb']
            rv = self.client.post(url, data=json.dumps(statement_invalid), content_type='application/json')
            self.assert400(rv)

            # test valid statement
            rv = self.client.post(url, data=json.dumps(statement), content_type='application/json')
            self.assert200(rv)

            statements = XAPILog.query.all()
            self.assertEqual(len(statements), 1)

            # test send another statement
            rv = self.client.post(url, data=json.dumps(statement), content_type='application/json')
            self.assert200(rv)

            statements = XAPILog.query.all()
            self.assertEqual(len(statements), 2)

    def test_create_caliper_event(self):
        self.app.config['LRS_CALIPER_HOST'] = 'local'
        url = '/api/learning_records/caliper/events'

        event = {
            'action': 'LoggedIn',
            'profile': 'SessionProfile',
            'object': {
                "id": 'https://localhost:8888',
                "type": "SoftwareApplication",
                "name": "ComPAIR",
                "description": "The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.",
                "version": self.app.config.get("COMPAIR_VERSION")
            },
            'type': 'SessionEvent'
        }

        # test CALIPER_ENABLED needs to be set
        self.app.config['CALIPER_ENABLED'] = False
        rv = self.client.post(url, data=json.dumps(event), content_type='application/json')
        self.assert404(rv)

        # need to re-register api blueprints since we're changing CALIPER_ENABLED
        self.app.config['CALIPER_ENABLED'] = True
        self.app = register_learning_record_api_blueprints(self.app)

        # test login required
        rv = self.client.post(url, data=json.dumps(event), content_type='application/json')
        self.assert401(rv)

        with self.login("root"):
            # test object required
            event_invalid = event.copy()
            del event_invalid['object']
            rv = self.client.post(url, data=json.dumps(event_invalid), content_type='application/json')
            self.assert400(rv)

            # test action required
            event_invalid = event.copy()
            del event_invalid['action']
            rv = self.client.post(url, data=json.dumps(event_invalid), content_type='application/json')
            self.assert400(rv)

            # test type required
            event_invalid = event.copy()
            del event_invalid['type']
            rv = self.client.post(url, data=json.dumps(event_invalid), content_type='application/json')
            self.assert400(rv)

            # test valid event
            rv = self.client.post(url, data=json.dumps(event), content_type='application/json')
            self.assert200(rv)

            events = CaliperLog.query.all()
            self.assertEqual(len(events), 1)

            # test send another event
            rv = self.client.post(url, data=json.dumps(event), content_type='application/json')
            self.assert200(rv)

            events = CaliperLog.query.all()
            self.assertEqual(len(events), 2)