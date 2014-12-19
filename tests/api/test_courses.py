import json
from data.fixtures.test_data import BasicTestData
from tests.test_acj import ACJTestCase


class CoursesAPITests(ACJTestCase):
	def setUp(self):
		super(CoursesAPITests, self).setUp()
		self.data = BasicTestData()

	def _verify_course_info(self, course_expected, course_actual):
		self.assertEqual(course_expected.name, course_actual['name'],
						 "Expected course name does not match actual.")
		self.assertEqual(course_expected.id, course_actual['id'],
						 "Expected course id does not match actual.")
		self.assertTrue(course_expected.criteriaandcourses, "Course is missing a criteria")

	def test_get_single_course(self):
		course_api_url = '/api/courses/' + str(self.data.get_course().id)

		# Test login required
		rv = self.client.get(course_api_url)
		self.assert401(rv)

		# Test root get course
		self.login('root')
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json)
		self.logout()

		# Test enroled users get course info
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json)
		self.logout()

		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json)
		self.logout()

		# Test unenroled user not permitted to get info
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		# Test get invalid course
		self.login("root")
		rv = self.client.get('/api/courses/38940450')
		self.assert404(rv)

	def test_get_all_courses(self):
		course_api_url = '/api/courses'

		# Test login required
		rv = self.client.get(course_api_url)
		self.assert401(rv)

		# Test only root can get a list of all courses
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		self.login("root")
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json['objects'][0])
		self.logout()

	def test_create_course(self):
		course_expected = {
			'name':'ExpectedCourse1',
			'description':'Test Course One Description Test'
		}
		# Test login required
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert401(rv)
		# Test unauthorized user
		self.login(self.data.get_authorized_student().username)
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# Test course creation
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert200(rv)
		# Verify return
		course_actual = rv.json
		self.assertEqual(course_expected['name'], course_actual['name'])
		self.assertEqual(course_expected['description'], course_actual['description'])

		# Verify you can get the course again
		rv = self.client.get('/api/courses/' + str(course_actual['id']))
		self.assert200(rv)
		course_actual = rv.json
		self.assertEqual(course_expected['name'], course_actual['name'])
		self.assertEqual(course_expected['description'], course_actual['description'])

		# Create the same course again, should fail
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert400(rv)

		# Test bad data format
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post('/api/courses',
							  data=json.dumps({'description':'d'}), content_type='application/json')
		self.assert400(rv)

	def test_edit_course(self):
		expected = {
			'id': self.data.get_course().id,
			'name': 'ExpectedCourse',
			'description': 'Test Description'
		}
		url = '/api/courses/' + str(self.data.get_course().id)

		# test login required
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert403(rv)

		# test unmatched course id
		rv = self.client.post('/api/courses/' + str(self.data.get_secondary_course().id),
					data=json.dumps(expected), content_type='application/json')
		self.assert400(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post('/api/courses/999', data=json.dumps(expected), content_type='application/json')
		self.assert404(rv)

		# test authorized user
		rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected['id'], rv.json['id'])
		self.assertEqual(expected['name'], rv.json['name'])
		self.assertEqual(expected['description'], rv.json['description'])
		self.logout()

	def test_course_name(self):
		url = '/api/courses/' + str(self.data.get_course().id) + '/name'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)

		self.login(self.data.get_authorized_instructor().username)
		# test invalid course id
		invalid_url = '/api/courses/999/name'
		rv = self.client.get(invalid_url)
		self.assert404(rv)

		# test successful query
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(self.data.get_course().name, rv.json['course_name'])
