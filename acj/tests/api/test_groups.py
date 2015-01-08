from data.fixtures.test_data import GroupsTestData

from acj.tests.test_acj import ACJTestCase

import io


class GroupsAPITests(ACJTestCase):
	def setUp(self):
		super(GroupsAPITests, self).setUp()
		self.data = GroupsTestData()

	def test_get_active_groups(self):
		url = '/api/courses/'+str(self.data.get_course().id)+'/groups'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		invalid_url = '/api/courses/999/groups'
		rv = self.client.get(invalid_url)
		self.assert404(rv)

		# test successful query
		rv = self.client.get(url)
		self.assert200(rv)
		actual = rv.json['groups']
		self.assertEqual(len(actual), 1)
		self.assertEqual(actual[0]['id'], self.data.get_active_group().id)
		self.assertEqual(actual[0]['name'], self.data.get_active_group().name)

		self.logout()

		# test TA
		self.login(self.data.get_authorized_ta().username)
		self.assert200(rv)
		actual = rv.json['groups']
		self.assertEqual(len(actual), 1)
		self.assertEqual(actual[0]['id'], self.data.get_active_group().id)
		self.assertEqual(actual[0]['name'], self.data.get_active_group().name)

		self.logout()

	def test_get_group_members(self):
		course_id = self.data.get_course().id
		group_id = self.data.get_active_group().id
		url = '/api/courses/'+str(course_id)+'/groups/'+str(group_id)

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/groups/'+str(group_id))
		self.assert404(rv)

		# test invalid group id
		rv = self.client.get('/api/courses/'+str(course_id)+'/groups/999')
		self.assert404(rv)

		# test authorized instructor
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(1, len(rv.json['students']))
		self.assertEqual(self.data.get_active_member().users_id, rv.json['students'][0]['user']['id'])
		self.logout()

		# test authorized teaching assistant
		self.login(self.data.get_authorized_ta().username)
		rv = self.client.get(url)
		self.assert200(rv)
		self.assertEqual(1, len(rv.json['students']))
		self.assertEqual(self.data.get_active_member().users_id, rv.json['students'][0]['user']['id'])
		self.logout()

	def test_group_enrolment(self):
		# frequently used objects
		course = self.data.get_course()
		group = self.data.get_active_group()

		# test login required
		url = self._create_group_user_url(course, self.data.get_authorized_student(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		url = self._create_group_user_url(course, self.data.get_authorized_student(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_authorized_instructor().username)
		# test user that is already in group
		url = self._create_group_user_url(course, self.data.get_authorized_student(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert200(rv)
		self.assertEqual(rv.json['groups_name'], group.name)

		# test user that has never been in the group
		url = self._create_group_user_url(course, self.data.get_authorized_instructor(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert200(rv)
		self.assertEqual(rv.json['groups_name'], group.name)

		# test user that has left the group
		url = self._create_group_user_url(course, self.data.get_authorized_ta(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert200(rv)
		self.assertEqual(rv.json['groups_name'], group.name)

		# test user that is not enroled in the course anymore - eg. DROPPED
		url = self._create_group_user_url(course, self.data.get_dropped_instructor(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test user that has never been in the course
		url = self._create_group_user_url(course, self.data.get_unauthorized_student(), group)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test inactive group
		url = self._create_group_user_url(course, self.data.get_authorized_student(), self.data.get_inactive_group())
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test group that is in another course
		url = self._create_group_user_url(course, self.data.get_authorized_student(), self.data.get_unauthorized_group())
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test invalid course id
		url = '/api/courses/999/users/'+str(self.data.get_authorized_student().id)+'/groups/'+str(group.id)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test invalid user id
		url = '/api/courses/'+str(course.id)+'/users/999/groups/'+str(group.id)
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		# test invalid group id
		url = '/api/courses/'+str(course.id)+'/users/'+str(self.data.get_authorized_student().id)+'/groups/999'
		rv = self.client.post(url, data={}, content_type='application/json')
		self.assert404(rv)

		self.logout()

	def test_group_unenrolment(self):
		course = self.data.get_course()

		# test login required
		url = self._create_group_user_url(course, self.data.get_authorized_student())
		rv = self.client.delete(url)
		self.assert401(rv)

		# test unauthorzied user
		self.login(self.data.get_unauthorized_instructor().username)
		url = self._create_group_user_url(course, self.data.get_authorized_student())
		rv = self.client.delete(url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_authorized_instructor().username)
		# test user in course
		url = self._create_group_user_url(course, self.data.get_authorized_student())
		rv = self.client.delete(url)
		self.assert200(rv)
		self.assertEqual(rv.json['user_id'], self.data.get_authorized_student().id)
		self.assertEqual(rv.json['course_id'], course.id)

		# test user not in course
		url = self._create_group_user_url(course, self.data.get_unauthorized_student())
		rv = self.client.delete(url)
		self.assert404(rv)

		# test invalid course id
		url = '/api/courses/999/users/'+str(self.data.get_authorized_student().id)+'/groups'
		rv = self.client.delete(url)
		self.assert404(rv)

		# test invalid user id
		url = '/api/courses/'+str(course.id)+'/users/999/groups'
		rv = self.client.delete(url)
		self.assert404(rv)

		self.logout()

	def test_import_groups(self):
		url = '/api/courses/' + str(self.data.get_course().id) + '/groups'

		content = self.data.get_authorized_student().username + "," + self.data.get_active_group().name
		encoded_content = content.encode()
		filename = "groups.csv"

		# test login required
		file = io.BytesIO(encoded_content)
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert401(rv)
		file.close()

		# test unauthorized user
		file = io.BytesIO(encoded_content)
		self.login(self.data.get_authorized_student().username)
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		file = io.BytesIO(encoded_content)
		self.login(self.data.get_authorized_ta().username)
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		file = io.BytesIO(encoded_content)
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert403(rv)
		file.close()
		self.logout()

		self.login(self.data.get_authorized_instructor().username)
		# test invalid course id
		invalid_url = '/api/courses/999/groups'
		file = io.BytesIO(encoded_content)
		rv = self.client.post(invalid_url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert404(rv)
		file.close()

		# test invalid file type
		invalid_file = "groups.png"
		file = io.BytesIO(encoded_content)
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, invalid_file)))
		self.assert400(rv)
		file.close()

		# test invalid user identifier
		file = io.BytesIO(encoded_content)
		rv = self.client.post(url, data=dict(userIdentifier="lastname", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(0, rv.json['success'])
		self.assertEqual({}, rv.json['invalids'][0]['member'])
		self.assertEqual("A valid user identifier is not given.", rv.json['invalids'][0]['message'])
		file.close()

		# test missing user identifier
		file = io.BytesIO(encoded_content)
		rv = self.client.post(url, data=dict(file=(file, filename)))
		self.assert400(rv)
		file.close()

		# test duplicate users in file
		duplicate = "".join([content, "\n", content])
		file = io.BytesIO(duplicate.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(1, len(rv.json['invalids']))
		invalid = rv.json['invalids'][0]
		member = ['["', self.data.get_authorized_student().username,'", "',
			self.data.get_active_group().name,'"]']
		self.assertEqual("".join(member), invalid['member'])
		self.assertEqual("This user already exists in the file.", invalid['message'])
		file.close()

		# test missing username
		missing_username = "," + self.data.get_active_group().name
		file = io.BytesIO(missing_username.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(1, len(rv.json['invalids']))
		invalid = rv.json['invalids'][0]
		member = ['["", "', self.data.get_active_group().name, '"]']
		self.assertEqual("".join(member), invalid['member'])
		self.assertEqual("No user with this username exists.", invalid['message'])
		file.close()

		# test missing group name
		missing_group = self.data.get_authorized_student().username + ","
		file = io.BytesIO(missing_group.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(0, rv.json['success'])
		self.assertEqual(1, len(rv.json['invalids']))
		invalid = rv.json['invalids'][0]
		member = ['["', self.data.get_authorized_student().username, '", ""]']
		self.assertEqual("".join(member), invalid['member'])
		self.assertEqual("The group name is invalid.", invalid['message'])
		file.close()

		# test invalid user
		invalid_user = "username9999," + self.data.get_active_group().name
		file = io.BytesIO(invalid_user.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(1, len(rv.json['invalids']))
		invalid = rv.json['invalids'][0]
		member = ['["username9999", "', self.data.get_active_group().name, '"]']
		self.assertEqual("".join(member), invalid['member'])
		self.assertEqual("No user with this username exists.", invalid['message'])
		file.close()

		# test successful import with username
		with_username = self.data.get_authorized_student().username + "," + self.data.get_active_group().name
		file = io.BytesIO(with_username.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()

		# test successful import with student number
		with_studentno = self.data.get_authorized_student().student_no + "," + self.data.get_active_group().name
		file = io.BytesIO(with_studentno.encode())
		rv = self.client.post(url, data=dict(userIdentifier="student_no", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()

		# test import user not in course
		unauthorized_student = self.data.get_unauthorized_student().username + "," + self.data.get_active_group().name
		file = io.BytesIO(unauthorized_student.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(1, len(rv.json['invalids']))
		invalid = rv.json['invalids'][0]
		member = ['["', self.data.get_unauthorized_student().username, '", "',
				self.data.get_active_group().name, '"]']
		self.assertEqual("".join(member), invalid['member'])
		self.assertEqual("The user is not enroled in the course", invalid['message'])
		file.close()

		# test adding to inactive group
		inactive_group = self.data.get_authorized_student().username + "," + self.data.get_inactive_group().name
		file = io.BytesIO(inactive_group.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()

		# test adding inactive group member
		inactive_member = self.data.get_inactive_member().user.username + "," + self.data.get_active_group().name
		file = io.BytesIO(inactive_member.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()

		# test placing instructor in group
		add_instructor = self.data.get_authorized_instructor().username + "," + self.data.get_active_group().name
		file = io.BytesIO(add_instructor.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()

		# test placing TA in group
		add_ta = self.data.get_authorized_ta().username + "," + self.data.get_active_group().name
		file = io.BytesIO(add_ta.encode())
		rv = self.client.post(url, data=dict(userIdentifier="username", file=(file, filename)))
		self.assert200(rv)
		self.assertEqual(1, rv.json['success'])
		self.assertEqual(0, len(rv.json['invalids']))
		file.close()


	def _create_group_user_url(self, course, user, group=None):
		url = '/api/courses/'+str(course.id)+'/users/'+str(user.id)+'/groups'
		if group:
			url = url+'/'+str(group.id)
		return url