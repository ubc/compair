from data.fixtures.test_data import GroupsTestData
from tests.test_acj import ACJTestCase

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

	def _create_group_user_url(self, course, user, group=None):
		url = '/api/courses/'+str(course.id)+'/users/'+str(user.id)+'/groups'
		if group:
			url = url+'/'+str(group.id)
		return url