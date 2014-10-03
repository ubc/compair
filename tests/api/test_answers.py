import json
from acj.models import UserTypesForSystem, UserTypesForCourse, PostsForAnswers, Posts
from data.fixtures.test_data import SimpleAnswersTestData
from tests.test_acj import ACJTestCase


class AnswersAPITests(ACJTestCase):
	def setUp(self):
		super(AnswersAPITests, self).setUp()
		self.data = SimpleAnswersTestData()
		self.question = self.data.get_questions()[1]
		self.base_url = self._build_url(self.data.get_course().id, self.question.id)

	def _build_url(self, course_id, question_id, tail=""):
		url = '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/answers' + \
			  tail
		return url

	def test_get_all_answers(self):
		# Test login required
		rv = self.client.get(self.base_url)
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.base_url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(self.base_url)
		self.assert403(rv)
		self.logout()
		# test non-existent entry
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(self._build_url(self.data.get_course().id, 4903409))
		self.assert404(rv)
		# test data retrieve is correct
		rv = self.client.get(self.base_url)
		self.assert200(rv)
		actual_answers = rv.json['objects']
		expected_answers = PostsForAnswers.query.filter_by(postsforquestions_id=self.question.id).all()
		for i, expected in enumerate(expected_answers):
			actual = actual_answers[i]
			self.assertEqual(expected.post.content, actual['post']['content'])

	def test_create_answer(self):
		# test login required
		expected_answer = {'post': {'content':'this is some answer content'}}
		rv = self.client.post(self.base_url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(self.base_url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test invalid format
		self.login(self.data.get_authorized_student().username)
		invalid_answer = {'post': {'blah':'blah'}}
		rv = self.client.post(self.base_url,
							  data=json.dumps(invalid_answer), content_type='application/json')
		self.assert400(rv)
		# test invalid question
		rv = self.client.post(
			self._build_url(self.data.get_course().id, 9392402),
			data=json.dumps(expected_answer), content_type='application/json')
		self.assert404(rv)
		# test invalid course
		rv = self.client.post(
			self._build_url(9392402, self.question.id),
			data=json.dumps(expected_answer), content_type='application/json')
		self.assert404(rv)
		# test create successful
		self.logout()
		self.login(self.data.get_authorized_instructor().username)

		rv = self.client.post(self.base_url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert200(rv)
		# retrieve again and verify
		answers = PostsForAnswers.query.filter_by(postsforquestions_id=self.question.id).all()
		actual_answer = answers[2]
		self.assertEqual(expected_answer['post']['content'], actual_answer.post.content)

	def test_delete_answer(self):
		self.logout()
		self.login(self.data.get_authorized_instructor().username)
		expected_answer = {'post': {'content':'this is some answer content'}}
		rv = self.client.post(self.base_url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert200(rv)
		self.logout()
		self.login(self.data.get_authorized_student().username)
		answerId = PostsForAnswers.query.filter_by(postsforquestions_id=self.question.id).all()[2].id
		# test delete unsuccessful
		self.logout()
		self.login(self.data.get_authorized_student().username)
		rv = self.client.delete(self.base_url + '/' + str(answerId))
		self.assert403(rv)
		self.logout()
		# test delete successful
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.delete(self.base_url + '/' + str(answerId))
		self.assert200(rv)
		self.assertEqual(answerId, rv.json['id'])
		

	def test_flag_answer(self):
		answer = self.question.answers[0]
		flag_url = self.base_url + "/" + str(answer.id) + "/flagged"
		# test login required
		expected_flag_on = {'flagged': True}
		expected_flag_off = {'flagged': False}
		rv = self.client.post(flag_url,
			data=json.dumps(expected_flag_on), content_type='application/json')
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_on),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test flagging
		self.login(self.data.get_authorized_student().username)
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_on),
							  content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected_flag_on['flagged'], rv.json['flagged'],
						 "Expected answer to be flagged.")
		# test unflagging
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_off),
							  content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected_flag_off['flagged'], rv.json['flagged'],
						 "Expected answer to be flagged.")
		# test prevent unflagging by other students
		self.login(self.data.get_authorized_student().username)
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_on),
							  content_type='application/json')
		self.assert200(rv)
		self.logout()
		## create another student
		other_student = self.data.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.data.enrol_user(other_student, self.data.get_course(), UserTypesForCourse.TYPE_STUDENT)
		## try to unflag answer as other student, should fail
		self.login(other_student.username)
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_off),
							  content_type='application/json')
		self.assert400(rv)
		self.logout()
		# test allow unflagging by instructor
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post(flag_url, data=json.dumps(expected_flag_off),
							  content_type='application/json')
		self.assert200(rv)
		self.assertEqual(expected_flag_off['flagged'], rv.json['flagged'],
						 "Expected answer to be flagged.")

	def test_get_question_answered(self):
		count_url = self.base_url + '/count'

		# test login required
		rv = self.client.get(count_url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(count_url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get('/api/courses/999/questions/1/answers/count')
		self.assert404(rv)

		# test invalid question id
		rv = self.client.get('/api/courses/1/questions/999/answers/count')
		self.assert404(rv)

		# test successful query - no answers
		rv = self.client.get(count_url)
		self.assert200(rv)
		self.assertEqual(0, rv.json['answered'])
		self.logout()

		# test successful query - answered
		self.login(self.data.get_extra_student1().username)
		rv = self.client.get(count_url)
		self.assert200(rv)
		self.assertEqual(1, rv.json['answered'])
		self.logout()

	def test_get_answered_count(self):
		answered_url = '/api/courses/' + str(self.data.get_course().id) + '/answers/answered'

		# test login required
		rv = self.client.get(answered_url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(answered_url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get('/api/courses/999/answered')
		self.assert404(rv)

		# test successful query - have not answered any questions in the course
		rv = self.client.get(answered_url)
		self.assert200(rv)
		self.assertEqual(0, len(rv.json['answered']))
		self.logout()

		# test successful query - have submitted one answer per question
		self.login(self.data.get_extra_student1().username)
		rv = self.client.get(answered_url)
		self.assert200(rv)
		expected = {str(question.id): 1 for question in self.data.get_questions()}
		self.assertEqual(expected, rv.json['answered'])
		self.logout()

	def test_get_answer_count(self):
		count_url = '/api/courses/' + str(self.data.get_course().id) + '/answers/count'

		# test login required
		rv = self.client.get(count_url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(count_url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get('/api/courses/999/answers/count')
		self.assert404(rv)

		# test successful query
		rv = self.client.get(count_url)
		self.assert200(rv)
		expected = {str(question.id): 2 for question in self.data.get_questions()}
		self.assertEqual(expected, rv.json['count'])
		self.logout()