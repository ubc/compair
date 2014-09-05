import json
import unittest

from flask.ext.testing import TestCase

from acj import create_app
from acj.manage.database import populate
from acj.core import db
from acj.models import PostsForQuestionsAndPostsForComments, PostsForAnswersAndPostsForComments, CoursesAndUsers
from data.fixtures.test_data import SimpleAnswersTestData, BasicTestData
from tests import test_app_settings

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

class QuestionCommentsAPITests(ACJTestCase):
	def setUp(self):
		super(QuestionCommentsAPITests, self).setUp()
		self.data = SimpleAnswersTestData()
		self.question = self.data.get_questions()[0]
		self.answer = self.data.get_answers()[0]
		self.url = '/api/courses/' + str(self.data.get_course().id) + '/questions/' + \
				str(self.question.id) + '/comments'

	def test_get_all_comments(self):
		# Test login required
		rv = self.client.get(self.url)
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		# test non-existent entry
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get('/api/courses/' + str(self.data.get_course().id) + \
			'/questions/4903409/comments')
		self.assert404(rv)
		# test data retrieved is correct
		rv = self.client.get(self.url)
		self.assert200(rv)
		actual_comments = rv.json['objects']
		expected_answers = PostsForQuestionsAndPostsForComments.query.\
			filter_by(postsforquestions_id=self.question.id).all()
		for i, expected in enumerate(expected_answers):
			actual = actual_comments[i]
			self.assertEqual(expected.postsforcomments.post.content, 				actual['postsforcomments']['post']['content'])

	def test_post_question_comments(self):
		# test login required
		expected_comment = {'content':'this is some question comment'}
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test invalid format
		self.login(self.data.get_authorized_student().username)
		invalid_comment = {'post':{'blah':'blah'}}
		rv = self.client.post(self.url, data=json.dumps(invalid_comment), content_type='application/json')
		self.assert400(rv)
		# test invalid question
		rv = self.client.post(
			'/api/courses/' + str(self.data.get_course().id) +\
			'/questions/9392402/comments',
			data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert404(rv)
		# test invalid course
		rv = self.client.post(
			'/api/courses/9334023/questions/' +\
			str(self.question.id) + '/answers',
			data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert404(rv)
		# test create successful
		rv = self.client.post(self.url,
			data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert200(rv)
		# retrieve again and verify
		comments = PostsForQuestionsAndPostsForComments.query.filter_by(
			postsforquestions_id=self.question.id).all()
		actual_comment = comments[0]
		self.assertEqual(expected_comment['content'], actual_comment.postsforcomments.post.content)

	def test_delete_question_comment(self):
		expected_comment = {'content':'this is some question comment'}
		self.logout()
		self.login(self.data.get_authorized_instructor().username)
		self.client.post(self.url,
			data=json.dumps(expected_comment),
			content_type='application/json')
		self.logout()
		self.login(self.data.get_authorized_student().username)
		commentId = PostsForQuestionsAndPostsForComments.query.filter_by(postsforquestions_id=self.question.id).all()[0].id
		# test delete unsuccessful
		self.logout()
		self.login(self.data.get_authorized_student().username)
		rv = self.client.delete(self.url + '/' + str(commentId))
		self.assert403(rv)
		self.logout()
		# test delete successful
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.delete(self.url + '/' + str(commentId))
		self.assert200(rv)
		self.assertEqual(commentId, rv.json['id'])


class AnswerCommentsAPITests(ACJTestCase):
	def setUp(self):
		super(AnswerCommentsAPITests, self).setUp()
		self.data = SimpleAnswersTestData()
		self.question = self.data.get_questions()[0]
		self.answer = self.data.get_answers()[0]
		self.url = '/api/courses/' + str(self.data.get_course().id) + \
				'/questions/' + str(self.question.id) + \
				'/answers/' + str(self.answer.id) + '/comments'

	def test_get_all_comments(self):
		# Test login required
		rv = self.client.get(self.url)
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		# test non-existent entry
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get('/api/courses/' +\
			str(self.data.get_course().id) + '/questions/' + \
			str(self.question.id) + '/answers/142154156/comments')
		self.assert404(rv)
		# test data retrieved is correct
		rv = self.client.get(self.url)
		self.assert200(rv)
		actual_comments = rv.json['objects']
		expected_comments = PostsForAnswersAndPostsForComments.query.\
			filter_by(postsforanswers_id=self.answer.id).all()
		for i, expected in enumerate(expected_comments):
			actual = actual_comments[i]
			self.assertEqual(expected.postsforcomments.post.content, actual['postsforcomments']['post']['content'])

	def test_create_comment(self):
		# test login required
		expected_comment = {'content':'this is some comment'}
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(self.url, data=json.dumps(expected_comment), content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test invalid format
		self.login(self.data.get_authorized_student().username)
		invalid_comment = {'post':{'blah':'blah'}}
		rv = self.client.post(self.url, data=json.dumps(invalid_comment), content_type='application/json')
		self.assert400(rv)
		# test invalid question
		rv = self.client.post(
			'/api/courses/' + str(self.data.get_course().id) +\
			'/questions/546465465/answers/' + str(self.answer.id)+\
			'/comments', data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert404(rv)
		# test invalid answer
		rv = self.client.post(
			'/api/courses/' + str(self.data.get_course().id) +\
			'/questions/' + str(self.question.id) + '/answers'+\
			'/4545645/comments', data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert404(rv)
		# test invalid course
		rv = self.client.post(
			'/api/courses/45545646645/questions/' + \
			str(self.question.id)+'/answers/'+str(self.answer.id)+\
			'/comments', data=json.dumps(expected_comment),
			content_type='application/json')
		self.assert404(rv)
		# test create successful
		rv = self.client.post(self.url,data=json.dumps(expected_comment),content_type='application/json')
		self.assert200(rv)
		# retrieve again and verify
		comments = PostsForAnswersAndPostsForComments.query.filter_by(postsforanswers_id=self.answer.id).all()
		actual_comment = comments[0]
		self.assertEqual(expected_comment['content'], actual_comment.postsforcomments.post.content)

	def test_delete_question_comment(self):
		expected_comment = {'content':'this is some question comment'}
		self.logout()
		self.login(self.data.get_authorized_instructor().username)
		self.client.post(self.url,
			data=json.dumps(expected_comment),
			content_type='application/json')
		self.logout()
		self.login(self.data.get_authorized_student().username)
		commentId = PostsForAnswersAndPostsForComments.query.filter_by(postsforanswers_id=self.answer.id).all()[0].id
		# test delete unsuccessful
		self.logout()
		self.login(self.data.get_authorized_student().username)
		rv = self.client.delete(self.url + '/' + str(commentId))
		self.assert403(rv)
		self.logout()
		# test delete successful
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.delete(self.url + '/' + str(commentId))
		self.assert200(rv)
		self.assertEqual(commentId, rv.json['id'])

class ClassListsAPITests(ACJTestCase):
	def setUp(self):
		super(ClassListsAPITests, self).setUp()
		self.data = BasicTestData()
		self.courseId = str(self.data.get_course().id)
		self.url = '/api/courses/' + str(self.data.get_course().id) + '/users'

	def test_get_all_students(self):
		# Test login required
		rv = self.client.get(self.url)
		self.assert401(rv)
		# test unauthorized users
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(self.url)
		self.assert403(rv)
		self.logout()
		# test non-existent entry
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get('/api/courses/5656478/users/')
		self.assert404(rv)
		# test student can't retrieve the data
		rv = self.client.get(self.url)
		self.assert403(rv)
		# test data retrieved is correct
		self.logout()
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(self.url)
		self.assert200(rv)
		actual_users = rv.json['objects']
		expected_users = CoursesAndUsers.query.\
			filter_by(courses_id=self.courseId).all()
		for i, expected in enumerate(expected_users):
			actual = actual_users[i]
			self.assertEqual(expected.user.username, actual['user']['username'])

class SessionTests(ACJTestCase):
	def test_loggedin_user_session(self):
		self.login('root', 'password')
		rv = self.client.get('/session')
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['id'], 1)

	def test_non_loggedin_user_session(self):
		rv = self.client.get('/session')
		self.assert401(rv)

if __name__ == '__main__':
	unittest.main()
