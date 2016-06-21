import datetime
import json

from data.fixtures.test_data import SimpleAssignmentTestData
from acj.models import Assignment
from acj.tests.test_acj import ACJAPITestCase


class AssignmentAPITests(ACJAPITestCase):
    def setUp(self):
        super(AssignmentAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.url = '/api/courses/' + str(self.data.get_course().id) + '/assignments'

    def test_get_single_assignment(self):
        assignment_expected = self.data.get_assignments()[0]
        assignment_api_url = self.url + '/' + str(assignment_expected.id)
        # Test login required
        rv = self.client.get(assignment_api_url)
        self.assert401(rv)
        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(assignment_api_url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(assignment_api_url)
            self.assert403(rv)

        # Test non-existent assignment
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self.url + '/939023')
            self.assert404(rv)
            # Test get actual assignment
            rv = self.client.get(assignment_api_url)
            self.assert200(rv)
            self._verify_assignment(assignment_expected, rv.json)

    def test_get_all_assignments(self):
        # Test login required
        rv = self.client.get(self.url)
        self.assert401(rv)
        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(self.url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(self.url)
            self.assert403(rv)
            # Test non-existent course
            rv = self.client.get('/api/courses/390484/assignments')
            self.assert404(rv)

        # Test receives all assignments
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self.url)
            for i, expected in enumerate(reversed(self.data.get_assignments())):
                actual = rv.json['objects'][i]
                self._verify_assignment(expected, actual)

    def test_create_assignment(self):
        now = datetime.datetime.utcnow()
        assignment_expected = {
            'name': 'this is a new assignment\'s name',
            'description': 'this is the new assignment\'s description.',
            'answer_start': now.isoformat() + 'Z',
            'answer_end': (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            'number_of_comparisons': 3,
            'students_can_reply': False,
            'enable_self_evaluation': False,
            'criteria': [
                { 'id': self.data.get_default_criterion().id }
            ]
        }
        # Test login required
        rv = self.client.post(
            self.url,
            data=json.dumps(assignment_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):  # student post assignments not implemented
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # Test bad format
            rv = self.client.post(
                self.url,
                data=json.dumps({'name': 'blah'}),
                content_type='application/json')
            self.assert400(rv)
            # Test zero criteria
            bad_criteria = assignment_expected.copy()
            bad_criteria['criteria'] = []
            rv = self.client.post(
                self.url,
                data=json.dumps(bad_criteria),
                content_type='application/json')
            self.assert403(rv)
            # Test actual creation
            rv = self.client.post(
                self.url,
                data=json.dumps(assignment_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                assignment_expected['name'], rv.json['name'],
                "assignment create did not return the same name!")
            self.assertEqual(
                assignment_expected['description'], rv.json['description'],
                "assignment create did not return the same description!")
            # Test getting the assignment again
            rv = self.client.get(self.url + '/' + str(rv.json['id']))
            self.assert200(rv)
            self.assertEqual(
                assignment_expected['name'], rv.json['name'],
                "assignment create did not save name properly!")
            self.assertEqual(
                assignment_expected['description'], rv.json['description'],
                "assignment create did not save description properly!")

    def test_edit_assignment(self):
        assignment = self.data.get_assignments()[0]
        url = self.url + '/' + str(assignment.id)
        expected = {
            'id': assignment.id,
            'name': 'This is the new name.',
            'description': 'new_description',
            'answer_start': assignment.answer_start.isoformat() + 'Z',
            'answer_end': assignment.answer_end.isoformat() + 'Z',
            'number_of_comparisons': assignment.number_of_comparisons,
            'students_can_reply': assignment.students_can_reply,
            'enable_self_evaluation': assignment.enable_self_evaluation,
            'criteria': [
                { 'id': self.data.get_default_criterion().id }
            ]
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)


        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/assignments/' + str(assignment.id)
            rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self.url + '/999'
            rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # Test zero criteria
            bad_criteria = expected.copy()
            bad_criteria['criteria'] = []
            rv = self.client.post(url, data=json.dumps(bad_criteria), content_type='application/json')
            self.assert403(rv)

            # test edit by author
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

            # test edit by author add & remove criteria
            new_criterion = self.data.create_criterion(self.data.get_authorized_instructor())
            add_criteria = expected.copy()
            add_criteria['criteria'] = [{ 'id': new_criterion.id }]
            rv = self.client.post(url, data=json.dumps(add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

        with self.login(self.data.get_authorized_ta().username):
            # test edit by user who can manage posts (TA)
            ta_expected = {
                'id': assignment.id,
                'name': 'Another name',
                'description': 'new_description',
                'answer_start': assignment.answer_start.isoformat() + 'Z',
                'answer_end': assignment.answer_end.isoformat() + 'Z',
                'number_of_comparisons': assignment.number_of_comparisons,
                'students_can_reply': assignment.students_can_reply,
                'enable_self_evaluation': assignment.enable_self_evaluation,
                'criteria': [
                    { 'id': self.data.get_default_criterion().id }
                ]
            }
            rv = self.client.post(url, data=json.dumps(ta_expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(ta_expected['name'], rv.json['name'])
            self.assertEqual(ta_expected['description'], rv.json['description'])

            # test edit by TA add & remove criteria
            ta_new_criterion = self.data.create_criterion(self.data.get_authorized_ta())
            ta_add_criteria = ta_expected.copy()
            ta_add_criteria['criteria'] = [{ 'id': ta_new_criterion.id }]
            rv = self.client.post(url, data=json.dumps(ta_add_criteria), content_type='application/json')
            self.assert200(rv)
            self._verify_assignment(assignment, rv.json)

    def test_delete_assignment(self):
        # Test deleting the assignment
        assignment_id = Assignment.query.first().id
        expected_ret = {'id': assignment_id}
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.delete(self.url + '/' + str(assignment_id))
            self.assert403(rv)
            self.assertEqual(
                '<p>' + self.data.get_authorized_student().username + ' does not have delete access to assignment 1</p>',
                rv.json['message'])

        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(self.url + '/' + str(assignment_id))
            self.assert200(rv)
            self.assertEqual(expected_ret['id'], rv.json['id'], "assignment " + str(rv.json['id']) + " deleted successfully")

    def _verify_assignment(self, expected, actual):
        self.assertEqual(expected.name, actual['name'])
        self.assertEqual(expected.description, actual['description'])
        self.assertEqual(expected.user_id, actual['user_id'])
