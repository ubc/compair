import json
import unittest
from flask.ext.testing import TestCase
from flask_bouncer import ensure
from flask_login import login_user, logout_user
import logging
from werkzeug.exceptions import Unauthorized
from acj import create_app, Users
from acj.manage.database import populate
from acj.core import db
from acj.models import UserTypesForSystem, UserTypesForCourse, Courses, PostsForAnswers
from data.fixtures import DefaultFixture
from tests import test_app_settings
from tests.factories import CoursesFactory, UsersFactory, CoursesAndUsersFactory, PostsFactory, PostsForQuestionsFactory, \
	PostsForAnswersFactory

# Tests Checklist
# - Unauthenticated users refused access with 401
# - Authenticated but unauthorized users refused access with 403
# - Non-existent entry errors out with 404
# - If post request, bad input format gets rejected with 400

class ACJTestCase(TestCase):

	def create_app(self):
		return create_app(settings_override=test_app_settings)

	def setUp(self):
		db.create_all()
		populate(default_data=True)

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def login(self, username, password="password"):
		payload = json.dumps(dict(
			username=username,
			password=password
		))
		rv = self.client.post('/login/login', data=payload, content_type='application/json', follow_redirects=True)
		self.assert200(rv)

		return rv

	def logout(self):
		return self.client.delete('/login/logout', follow_redirects=True)

class TestData():
	def __init__(self):
		self.course = CoursesFactory()
		db.session.commit()
		# create 2 instructors and 2 students, 1 of each will be enroled in the course
		self.unenroled_instructor = self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)
		self.unenroled_student = self.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.enroled_instructor = self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)
		self.enrol_user(self.enroled_instructor, self.course, UserTypesForCourse.TYPE_INSTRUCTOR)
		self.enroled_student = self.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.enrol_user(self.enroled_student, self.course, UserTypesForCourse.TYPE_STUDENT)
		# add 2 questions, each with 2 answers, to the course
		self.questions = []
		question = self.create_question(self.course, self.enroled_instructor)
		self.questions.append(question)
		self.create_answer(question, self.enroled_student)
		self.create_answer(question, self.enroled_student)
		question = self.create_question(self.course, self.enroled_instructor)
		self.questions.append(question)
		self.create_answer(question, self.enroled_student)
		self.create_answer(question, self.enroled_student)

	def create_answer(self, question, author):
		post = PostsFactory(courses_id = question.post.courses_id, users_id = author.id)
		db.session.commit()
		answer = PostsForAnswersFactory(postsforquestions_id=question.id, posts_id = post.id)
		db.session.commit()
		return answer

	def create_question(self, course, author):
		post = PostsFactory(courses_id = course.id, users_id = author.id)
		db.session.commit()
		question = PostsForQuestionsFactory(posts_id = post.id)
		db.session.commit()
		return question

	def create_user(self, type):
		sys_type = UserTypesForSystem.query.filter_by(name=type). \
			first()
		user = UsersFactory(usertypesforsystem_id=sys_type.id)
		db.session.commit()
		return user

	def enrol_user(self, user, course, type):
		course_type = UserTypesForCourse.query. \
			filter_by(name=type).first()
		CoursesAndUsersFactory(courses_id=course.id, users_id=user.id,
							   usertypesforcourse_id=course_type.id)
		db.session.commit()

	def get_course(self):
		return self.course
	def get_enroled_instructor(self):
		return self.enroled_instructor
	def get_unenroled_instructor(self):
		return self.unenroled_instructor
	def get_enroled_student(self):
		return self.enroled_student
	def get_unenroled_student(self):
		return self.unenroled_student
	def get_questions(self):
		return self.questions

class CoursesAPITests(ACJTestCase):
	def setUp(self):
		super(CoursesAPITests, self).setUp()
		self.data = TestData()

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
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json)
		self.logout()

		self.login(self.data.get_enroled_student().username)
		rv = self.client.get(course_api_url)
		self.assert200(rv)
		self._verify_course_info(self.data.get_course(), rv.json)
		self.logout()

		# Test unenroled user not permitted to get info
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_unenroled_student().username)
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
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.get(course_api_url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_enroled_student().username)
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
			'name':'TestCourse1',
			'description':'Test Course One Description Test'
		}
		# Test login required
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert401(rv)
		# Test unauthorized user
		self.login(self.data.get_enroled_student().username)
		rv = self.client.post('/api/courses',
							  data=json.dumps(course_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()

		# Test course creation
		self.login(self.data.get_enroled_instructor().username)
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
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.post('/api/courses',
							  data=json.dumps({'description':'d'}), content_type='application/json')
		self.assert400(rv)


class UsersAPITests(ACJTestCase):
	def test_unauthorized(self):
		rv = self.client.get('/api/users')
		self.assert401(rv)

	def test_login(self):
		rv = self.login('root', 'password')
		userid = rv.json['userid']
		self.assertEqual(userid, 1, "Logged in user's id does not match!")
		self._verify_permissions(userid, rv.json['permissions'])

	def test_users_root(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['username'], 'root')
		self.assertEqual(root['displayname'], 'root')
		self.assertNotIn('_password', root)

	def test_users_invalid_id(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/99999')
		self.assert404(rv)

	def test_users_info_unrestricted(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['displayname'], 'root')
		# personal information should be transmitted
		self.assertIn('firstname', root)
		self.assertIn('lastname', root)
		self.assertIn('fullname', root)
		self.assertIn('email', root)

	def test_users_info_restricted(self):
		user = UsersFactory(password='password', usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)
		db.session.commit()

		self.login(user.username, 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['displayname'], 'root')
		# personal information shouldn't be transmitted
		self.assertNotIn('firstname', root)
		self.assertNotIn('lastname', root)
		self.assertNotIn('fullname', root)
		self.assertNotIn('email', root)

	def test_users_list(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users')
		self.assert200(rv)
		users = rv.json
		self.assertEqual(users['num_results'], 1)
		self.assertEqual(users['objects'][0]['username'], 'root')

	def _verify_permissions(self, userid, permissions):
		user = Users.query.get(userid)
		with self.app.app_context():
			# can't figure out how to get into logged in app context, so just force a login here
			login_user(user, force=True)
			for model_name, operations in permissions.items():
				for operation, permission in operations.items():
					expected = True
					try:
						ensure(operation, model_name)
					except Unauthorized:
						expected = False
					self.assertEqual(permission, expected,
									 "Expected permission " + operation + " on " +  model_name + " to be " + str(expected))
			# undo the forced login earlier
			logout_user()


class QuestionsAPITests(ACJTestCase):
	def setUp(self):
		super(QuestionsAPITests, self).setUp()
		self.data = TestData()
		self.url = '/api/courses/' + str(self.data.get_course().id) + '/questions'

	def test_get_single_question(self):
		question_expected = self.data.get_questions()[0]
		questions_api_url = self.url + '/' + str(question_expected.id)
		# Test login required
		rv = self.client.get(questions_api_url)
		self.assert401(rv)
		# Test unauthorized user
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.get(questions_api_url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.get(questions_api_url)
		self.assert403(rv)
		# Test non-existent question
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.get(self.url + '/939023')
		self.assert404(rv)
		# Test get actual question
		rv = self.client.get(questions_api_url)
		self.assert200(rv)
		self._verify_question(question_expected, rv.json)

	def test_get_all_questions(self):
		# Test login required
		rv = self.client.get(self.url)
		self.assert401(rv)
		# Test unauthorized user
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		# Test non-existent course
		rv = self.client.get('/api/courses/390484/questions')
		self.assert404(rv)
		self.logout()
		# Test receives all questions
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.get(self.url)
		self.assert200(rv)
		for i, expected in enumerate(self.data.get_questions()):
			actual = rv.json['objects'][i]
			self._verify_question(expected, actual)

	def test_create_question(self):
		question_expected = {'title':'this is a new question\'s title',
				  'post': {'content':'this is the new question\'s content.'}}
		# Test login required
		rv = self.client.post(self.url,
							  data=json.dumps(question_expected), content_type='application/json')
		self.assert401(rv)
		# Test unauthorized user
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.post(self.url,
							  data=json.dumps(question_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.post(self.url,
							  data=json.dumps(question_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_enroled_student().username) # student post questions not implemented
		rv = self.client.post(self.url,
							  data=json.dumps(question_expected), content_type='application/json')
		self.assert403(rv)
		self.logout()
		# Test bad format
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.post(self.url,
							  data=json.dumps({'title':'blah'}), content_type='application/json')
		self.assert400(rv)
		# Test actual creation
		rv = self.client.post(self.url,
							  data=json.dumps(question_expected), content_type='application/json')
		self.assert200(rv)
		self.assertEqual(question_expected['title'], rv.json['title'],
						 "Question create did not return the same title!")
		self.assertEqual(question_expected['post']['content'], rv.json['post']['content'],
						 "Question create did not return the same content!")
		# Test getting the question again
		rv = self.client.get(self.url + '/' + str(rv.json['id']))
		self.assert200(rv)
		self.assertEqual(question_expected['title'], rv.json['title'],
						 "Question create did not save title properly!")
		self.assertEqual(question_expected['post']['content'], rv.json['post']['content'],
						 "Question create did not save content proeprly!")

	def _verify_question(self, expected, actual):
		self.assertEqual(expected.title, actual['title'])
		self.assertEqual(expected.posts_id, actual['post']['id'])
		self.assertEqual(expected.post.content, actual['post']['content'])
		self.assertEqual(expected.post.user.id, actual['post']['user']['id'])


class AnswersAPITests(ACJTestCase):
	def setUp(self):
		super(AnswersAPITests, self).setUp()
		self.data = TestData()
		self.question = self.data.get_questions()[0]
		self.url = '/api/courses/' + str(self.data.get_course().id) + '/questions/' + \
				   str(self.question.id) + '/answers'

	def test_get_all_answers(self):
		# Test login required
		rv = self.client.get(self.url)
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		# test non-existent entry
		self.login(self.data.get_enroled_student().username)
		rv = self.client.get('/api/courses/' + str(self.data.get_course().id) +
							 '/questions/4903409/answers')
		self.assert404(rv)
		# test data retrieve is correct
		rv = self.client.get(self.url)
		self.assert200(rv)
		actual_answers = rv.json['objects']
		expected_answers = PostsForAnswers.query.filter_by(postsforquestions_id=self.question.id).all()
		for i, expected in enumerate(expected_answers):
			actual = actual_answers[i]
			self.assertEqual(expected.post.content, actual['post']['content'])

	def test_create_answer(self):
		# test login required
		expected_answer = {'post': {'content':'this is some answer content'}}
		rv = self.client.post(self.url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.post(self.url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.post(self.url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test invalid format
		self.login(self.data.get_enroled_student().username)
		invalid_answer = {'post': {'blah':'blah'}}
		rv = self.client.post(self.url,
							  data=json.dumps(invalid_answer), content_type='application/json')
		self.assert400(rv)
		# test invalid question
		rv = self.client.post(
			'/api/courses/' + str(self.data.get_course().id) + '/question/9392402/answers',
			data=json.dumps(expected_answer), content_type='application/json')
		self.assert404(rv)
		# test invalid course
		rv = self.client.post(
			'/api/courses/9334023/question/'+ str(self.question.id) +'/answers',
			data=json.dumps(expected_answer), content_type='application/json')
		self.assert404(rv)
		# test create successful
		rv = self.client.post(self.url,
							  data=json.dumps(expected_answer), content_type='application/json')
		self.assert200(rv)
		# retrieve again and verify
		answers = PostsForAnswers.query.filter_by(postsforquestions_id=self.question.id).all()
		actual_answer = answers[2]
		self.assertEqual(expected_answer['post']['content'], actual_answer.post.content)


if __name__ == '__main__':
	unittest.main()
