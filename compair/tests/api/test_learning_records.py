# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from compair.tests.test_compair import ComPAIRAPITestCase
from compair.api import register_learning_record_api_blueprints
from compair.models import XAPILog

class LearningRecordsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LearningRecordsAPITests, self).setUp()

    def test_create_xapi_statement(self):
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