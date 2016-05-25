from data.fixtures import AssignmentFactory

from acj.core import db
from acj.api.util import get_model_changes
from acj.tests.test_acj import ACJTestCase


class DbUtilTests(ACJTestCase):
    def test_get_model_changes(self):
        assignment = AssignmentFactory()

        db.session.commit()

        self.assertEqual(get_model_changes(assignment), None, 'should return None on no change model')

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
