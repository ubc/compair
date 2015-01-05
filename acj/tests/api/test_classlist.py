import json, io

from data.fixtures.test_data import BasicTestData

from acj.tests.test_acj import ACJTestCase
from acj.models import UserTypesForCourse

class ClassListAPITest(ACJTestCase):
	def setUp(self):
		super(ClassListAPITest, self).setUp()
		self.data = BasicTestData()
		self.url = "/api/courses/"+str(self.data.get_course().id)+"/users"

	def test_get_classlist(self):
		# test login required
		rv = self.client.get(self.url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/users')
		self.assert404(rv)

		# test authorized user
		expected = [self.data.get_authorized_instructor().id, self.data.get_authorized_ta().id,\
					self.data.get_authorized_student().id]
		rv = self.client.get(self.url)
		self.assert200(rv)
		self.assertEqual(len(expected), len(rv.json['objects']))
		for key in range(0, len(expected)):
			self.assertEqual(self.data.get_course().id, rv.json['objects'][key]['course']['id'])
			self.assertEqual(expected[key], rv.json['objects'][key]['user']['id'])

	def test_get_instructor_labels(self):
		url = self.url + "/instructors/labels"

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test dropped instructor - unauthorized
		self.login(self.data.get_dropped_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test unauthorized instructor
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/users/instructors/labels')
		self.assert404(rv)

		# test success
		rv = self.client.get(url)
		self.assert200(rv)
		labels = rv.json['instructors']
		expected = {
			str(self.data.get_authorized_ta().id): 'Teaching Assistant',
			str(self.data.get_authorized_instructor().id): 'Instructor'
		}
		self.assertEqual(labels, expected)
		self.logout()

	def test_get_instructors_course(self):
		url = self.url + "/instructors"

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test dropped instructor - unauthorized
		self.login(self.data.get_dropped_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test unauthorized instructor
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/users/instructors')
		self.assert404(rv)

		# test success
		rv = self.client.get(url)
		self.assert200(rv)
		instructors = rv.json['instructors']
		expected = {str(self.data.get_authorized_instructor().id): self.data.get_authorized_instructor().fullname}
		self.assertEqual(instructors, expected)
		self.logout()

	def test_get_students_course(self):
		url = self.url + "/students"

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test dropped instructor - unauthorized
		self.login(self.data.get_dropped_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test unauthorized instructor
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/users/students')
		self.assert404(rv)

		# test success - instructor
		rv = self.client.get(url)
		self.assert200(rv)
		students = rv.json['students']
		expected = {
			'id': self.data.get_authorized_student().id,
			'name': self.data.get_authorized_student().fullname
		}
		self.assertEqual(students[0]['user']['id'], expected['id'])
		self.assertEqual(students[0]['user']['name'], expected['name'])
		self.logout()

		self.login(self.data.get_authorized_ta().username)
		rv = self.client.get(url)
		self.assert200(rv)
		students = rv.json['students']
		expected = {
			'id': self.data.get_authorized_student().id,
			'name': self.data.get_authorized_student().fullname
		}
		self.assertEqual(students[0]['user']['id'], expected['id'])
		self.assertEqual(students[0]['user']['name'], expected['name'])
		self.logout()

		# test success - student
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(url)
		self.assert200(rv)
		students = rv.json['students']
		expected = {
			'id': self.data.get_authorized_student().id,
			'name': self.data.get_authorized_student().displayname
		}
		self.assertEqual(students[0]['user']['id'], expected['id'])
		self.assertEqual(students[0]['user']['name'], expected['name'])
		self.logout()

	def test_enrol_instructor(self):
		url = self._create_enrol_url(self.url, self.data.get_dropped_instructor().id)
		instructor_role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).first().id
		role = {} # defaults to Instructor

		# test login required
		rv = self.client.post(url,
			data=json.dumps(role), content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(url,
			data=json.dumps(role), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		invalid_url = '/api/courses/999/users/instructors/' + str(self.data.get_dropped_instructor().id) + '/enrol'
		rv = self.client.post(invalid_url,
			data=json.dumps(role), content_type='application/json')
		self.assert404(rv)

		# test invalid user id
		invalid_url = self._create_enrol_url(self.url, 999)
		rv = self.client.post(invalid_url,
			data=json.dumps(role), content_type='application/json')
		self.assert404(rv)

		# test enrolling dropped instructor
		expected = {
			'user': {
				'id': self.data.get_dropped_instructor().id,
				'fullname': self.data.get_dropped_instructor().fullname
			},
			'usertypesforcourse': {
				'id': instructor_role_id,
				'name': UserTypesForCourse.TYPE_INSTRUCTOR
			}
		}
		rv = self.client.post(url,
			data=json.dumps(role), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected, rv.json)

		# test enrolling new instructor
		url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().id)
		expected = {
			'user': {
				'id': self.data.get_unauthorized_instructor().id,
				'fullname': self.data.get_unauthorized_instructor().fullname
			},
			'usertypesforcourse': {
				'id': instructor_role_id,
				'name': UserTypesForCourse.TYPE_INSTRUCTOR
			}
		}
		rv = self.client.post(url,
			data=json.dumps(role), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected, rv.json)

		# test enrolling a different role - eg. Student
		ta_role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_TA).first().id
		role = {'usertypesforcourse_id': str(ta_role_id)}
		expected = {
			'user': {
				'id': self.data.get_unauthorized_instructor().id,
				'fullname': self.data.get_unauthorized_instructor().fullname
			},
			'usertypesforcourse': {
				'id': ta_role_id,
				'name': UserTypesForCourse.TYPE_TA
			}
		}
		rv = self.client.post(url,
			data=json.dumps(role), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected, rv.json)
		self.logout()

	def test_unenrol_instructor(self):
		url = self._create_enrol_url(self.url, self.data.get_authorized_instructor().id)
		dropped_role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

		# test login required
		rv = self.client.delete(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.delete(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		invalid_url = '/api/courses/999/users/instructors/' + str(self.data.get_authorized_instructor().id) + '/enrol'
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.delete(invalid_url)
		self.assert404(rv)

		# test invalid user id
		invalid_url = self._create_enrol_url(self.url, 999)
		rv = self.client.delete(invalid_url)
		self.assert404(rv)

		# test existing user not in existing course
		invalid_url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().id)
		rv = self.client.delete(invalid_url)
		self.assert404(rv)

		# test success
		expected = {
			'user': {
				'id': self.data.get_authorized_instructor().id,
				'fullname': self.data.get_authorized_instructor().fullname
			},
			'usertypesforcourse': {
				'id': dropped_role_id,
				'name': UserTypesForCourse.TYPE_DROPPED
			}
		}
		rv = self.client.delete(url)
		self.assert200(rv)
		self.assertEqual(expected, rv.json)


	def test_import_classlist(self):
		url = '/api/courses/' + str(self.data.get_course().id) + '/users'
		auth_student = self.data.get_authorized_student()

		# test login required
		file = io.BytesIO(auth_student.username.encode())
		filename = "classlist.csv"
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		self.login(self.data.get_authorized_student().username)
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		self.login(self.data.get_authorized_ta().username)
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		self.login(self.data.get_authorized_instructor().username)
		# test invalid course id
		invalid_url = '/api/courses/999/users'
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(invalid_url, data=dict(file=(file, filename)))
		file.close()
		self.assert404(rv)

		# test invalid file type
		invalid_filetype = "classlist.png"
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(url, data=dict(file=(file, invalid_filetype)))
		file.close()
		self.assert400(rv)

		# test no username provided
		content = "".join([",\n", auth_student.username, ",", auth_student.student_no])
		file = io.BytesIO(content.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(1, len(result['invalids']))
		self.assertEqual(None, result['invalids'][0]['user']['username'])
		self.assertEqual('The username is required.', result['invalids'][0]['message'])
		file.close()

		# test duplicate usernames in file
		content = "".join([auth_student.username, "\n", auth_student.username])
		file = io.BytesIO(content.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(1, len(result['invalids']))
		self.assertEqual(auth_student.username, result['invalids'][0]['user']['username'])
		self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
		file.close()

		# test duplicate student number in system
		content = "".join(['username1,', auth_student.student_no, "\n", auth_student.username])
		file = io.BytesIO(content.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(1, len(result['invalids']))
		self.assertEqual("username1", result['invalids'][0]['user']['username'])
		self.assertEqual('This student number already exists in the system.', result['invalids'][0]['message'])
		file.close()

		# test duplicate student number in file
		content = "".join([auth_student.username, ",", auth_student.student_no, "\n",
						   "username1,", auth_student.student_no])
		file = io.BytesIO(content.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(1, len(result['invalids']))
		self.assertEqual("username1", result['invalids'][0]['user']['username'])
		self.assertEqual('This student number already exists in the file.', result['invalids'][0]['message'])
		file.close()

		# test existing display
		content = "username1,,,,," + auth_student.displayname
		file = io.BytesIO(content.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(0, len(result['invalids']))
		file.close()

		# test authorized instructor - new user
		file = io.BytesIO(b'username2')
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert200(rv)
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(0, len(result['invalids']))
		file.close()

		# test authorized instructor - existing user
		file = io.BytesIO(auth_student.username.encode())
		rv = self.client.post(url, data=dict(file=(file, filename)))
		result = rv.json
		self.assertEqual(1, result['success'])
		self.assertEqual(0, len(result['invalids']))
		file.close()

		# test authorized instructor - dropped user
		file = io.BytesIO()

	def _create_enrol_url(self, url, user_id):
		return url + '/' + str(user_id) + '/enrol'