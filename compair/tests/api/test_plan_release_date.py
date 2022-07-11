# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from compair.tests.test_compair import ComPAIRAPITestCase

class PlanReleaseDateAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(PlanReleaseDateAPITests, self).setUp()

    def test_assignment_enddate(self):
        url = '/app/#/assignment/search/enddate'
        with self.login('root'):
            # test default entry
            rv = self.client.get(url)
            self.assert200(rv)

            # test data retrieve is correct
            rv = self.client.get(url+'?compare_end=2021-01-05')
            self.assert200(rv)


