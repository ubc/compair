import json
from data.fixtures.test_data import CriteriaTestData
from tests.test_acj import ACJTestCase

class CriteriaAPITests(ACJTestCase):
	def setUp(self):
		super(CriteriaAPITests, self).setUp()
		self.data = CriteriaTestData()

	def _verify_criteria(self, criteria_expected, criteria_actual):
		self.assertEqual(criteria_expected.name, criteria_actual['criterion']['name'], \
			'Expected criterion name does not match actual.')
		self.assertEqual(criteria_expected.description, criteria_actual['criterion']['description'], \
			'Expected criterion description does not match actual')

	def test_get_all_criteria_course(self):
		course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria'

		# Test get criteria attached to course
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(course_criteria_api_url)
		self.assert200(rv)
		criteria_expected = self.data.get_default_criteria()
		criteria_actual = rv.json['objects'][0]
		self._verify_criteria(criteria_expected, criteria_actual)
		self.logout()

		# Test login required
		rv = self.client.get(course_criteria_api_url)
		self.assert401(rv)

		# Test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/criteria')
		self.assert404(rv)
		self.logout()

	def test_create_criteria(self):
		course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria'
		criteria_expected = {
			'name': 'Which is more accurate?',
			'description': 'Please answer honestly.'
		}

		# Test login required
		rv = self.client.post(course_criteria_api_url, \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert401(rv)

		#Test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post('/api/courses/999/criteria', \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert404(rv)

		# Test successful criteria creation
		rv = self.client.post(course_criteria_api_url, \
			data=json.dumps(criteria_expected), content_type='application/json')
		self.assert200(rv)
		criteria_actual = rv.json['criterion']['criterion']
		self.assertEqual(criteria_expected['name'], criteria_actual['name'])
		self.assertEqual(criteria_expected['description'], criteria_actual['description'])
		self.logout()

		# Test fail criteria creation - unauthorized
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(course_criteria_api_url, \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

	def test_get_criteria(self):
		criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)

		# Test login required
		rv = self.client.get(criteria_api_url)
		self.assert401(rv)

		# Test author access
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(criteria_api_url)
		self.assert200(rv)
		self._verify_criteria(self.data.get_criteria(), rv.json)
		self.logout()

		# Test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(criteria_api_url)
		self.assert403(rv)
		self.logout()

		# Test admin access
		self.login('root')
		rv = self.client.get(criteria_api_url)
		self.assert200(rv)
		self._verify_criteria(self.data.get_criteria(), rv.json)

		# Test invalid criteria id
		rv = self.client.get('/api/criteria/999')
		self.assert404(rv)
		self.logout()

	def test_edit_criteria(self):
		criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)
		criteria_expected = {
			'id': self.data.get_criteria().id,
			'name': 'Which is more correct?',
			'description': 'Please answer more honestly.'
		}

		# Test login required
		rv = self.client.post(criteria_api_url, \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert401(rv)

		# Test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(criteria_api_url, \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# Test invalid criteria id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post('/api/criteria/999', \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert404(rv)

		# Test author access
		rv = self.client.post(criteria_api_url, \
				data=json.dumps(criteria_expected), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(criteria_expected['name'], rv.json['criterion']['name'])
		self.assertEqual(criteria_expected['description'], rv.json['criterion']['description'])
		self.logout()

		# Test admin access
		admin_criteria_expected = self.data.get_criteria()
		admin_criteria_expected = {
			'id': self.data.get_criteria().id,
			'name': 'Which one uses the correct formula?',
			'description': 'Hint: Law of Physics.'
		}
		self.login('root')
		rv = self.client.post(criteria_api_url, \
				data=json.dumps(admin_criteria_expected), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(admin_criteria_expected['name'], rv.json['criterion']['name'])
		self.assertEqual(admin_criteria_expected['description'], rv.json['criterion']['description'])
		self.logout()