# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock

from compair.tests.test_compair import ComPAIRAPITestCase


class HealthzAPITests(ComPAIRAPITestCase):
    def test_healthz_returns_200_when_db_is_up(self):
        rv = self.client.get('/api/healthz')
        self.assert200(rv)
        data = rv.json
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['checks']['db'], 'ok')

    def test_healthz_returns_503_when_db_is_down(self):
        from compair.core import db
        with mock.patch.object(db.session, 'execute', side_effect=Exception('DB unavailable')):
            rv = self.client.get('/api/healthz')
            self.assertEqual(rv.status_code, 503)
            data = rv.json
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['checks']['db'], 'error')

    def test_healthz_requires_no_authentication(self):
        # endpoint must be reachable without logging in
        rv = self.client.get('/api/healthz')
        self.assert200(rv)
