# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from data.fixtures import AssignmentFactory

from compair.core import db
from compair.api.util import get_model_changes
from compair.tests.test_compair import ComPAIRTestCase


class DbUtilTests(ComPAIRTestCase):
    def test_get_model_changes(self):
        assignment = AssignmentFactory()

        db.session.commit()

        self.assertEqual(get_model_changes(assignment), None, 'shoul return None on no change model')

        oldname = assignment.name
        assignment.name = 'new name'

        self.assertDictEqual(
            get_model_changes(assignment), {
                'name': {'before': oldname, 'after': 'new name'}
            },
            'should find the change when attribute changes')

        olddescription = assignment.description
        assignment.description = "new description"

        self.assertDictEqual(
            get_model_changes(assignment), {
                'name': {'before': oldname, 'after': 'new name'},
                'description': {'before': olddescription, 'after': 'new description'}
            },
            'should find the change when attribute changes')
