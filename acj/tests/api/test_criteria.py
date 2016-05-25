import json

from data.fixtures.test_data import CriteriaTestData
from acj.tests.test_acj import ACJAPITestCase


class CriteriaAPITests(ACJAPITestCase):
    def setUp(self):
        super(CriteriaAPITests, self).setUp()
        self.data = CriteriaTestData()

    def _verify_critera(self, criteria_expected, criteria_actual):
        self.assertEqual(
            criteria_expected.name, criteria_actual['name'],
            'Expected criterion name does not match actual.')
        self.assertEqual(
            criteria_expected.description, criteria_actual['description'],
            'Expected criterion description does not match actual')

    def _build_assignment_criteria_url(self, course_id, assignment_id, criteria_id = None):
        if criteria_id == None:
            return '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/criteria'
        else:
            return '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/criteria/' + str(criteria_id)

    def test_create_criteria(self):  
        criteria_api_url = '/api/criteria'
              
        criteria_expected = {
            'name': 'Which is more accurate?',
            'description': 'Please answer honestly.'
        }

        # Test login required
        rv = self.client.post(
            criteria_api_url,
            data=json.dumps(criteria_expected),
            content_type='application/json')
        self.assert401(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # Test successful criteria creation
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            criteria_actual = rv.json
            self.assertEqual(criteria_expected['name'], criteria_actual['name'])
            self.assertEqual(criteria_expected['description'], criteria_actual['description'])

        # Test fail criteria creation - student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert403(rv)

    def test_get_criteria(self):
        criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)

        # Test login required
        rv = self.client.get(criteria_api_url)
        self.assert401(rv)

        # Test author access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            self._verify_critera(self.data.get_criteria(), rv.json)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert403(rv)

        # Test admin access
        with self.login('root'):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            self._verify_critera(self.data.get_criteria(), rv.json)

            # Test invalid criteria id
            rv = self.client.get('/api/criteria/999')
            self.assert404(rv)

    def test_edit_criteria(self):
        criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)
        criteria_expected = {
            'id': self.data.get_criteria().id,
            'name': 'Which is more correct?',
            'description': 'Please answer more honestly.'
        }

        # Test login required
        rv = self.client.post(
            criteria_api_url,
            data=json.dumps(criteria_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert403(rv)

        # Test invalid criteria id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/criteria/999',
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert404(rv)

            # Test author access
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(criteria_expected['name'], rv.json['name'])
            self.assertEqual(criteria_expected['description'], rv.json['description'])

        # Test admin access
        # admin_criteria_expected = self.data.get_criteria()
        admin_criteria_expected = {
            'id': self.data.get_criteria().id,
            'name': 'Which one uses the correct formula?',
            'description': 'Hint: Law of Physics.'
        }
        with self.login('root'):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(admin_criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(admin_criteria_expected['name'], rv.json['name'])
            self.assertEqual(admin_criteria_expected['description'], rv.json['description'])


    def test_get_available_criteria(self):
        criteria_api_url = '/api/criteria'

        # Test login required
        rv = self.client.get(criteria_api_url)
        self.assert401(rv)

        # Test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # one public + two authored
            self.assertEqual(len(rv.json['objects']), 3)
            self._verify_critera(self.data.get_default_criteria(), rv.json['objects'][0])
            self._verify_critera(self.data.get_criteria(), rv.json['objects'][1])

        # Test unauthorized instructor
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # one public + one authored
            self.assertEqual(len(rv.json['objects']), 2)
            self._verify_critera(self.data.get_default_criteria(), rv.json['objects'][0])
            self._verify_critera(self.data.get_secondary_criteria(), rv.json['objects'][1])

        # Test admin
        with self.login('root'):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # return all
            self.assertEqual(len(rv.json['objects']), 4)
            self._verify_critera(self.data.get_default_criteria(), rv.json['objects'][0])
            self._verify_critera(self.data.get_criteria(), rv.json['objects'][1])
            self._verify_critera(self.data.get_secondary_criteria(), rv.json['objects'][2])