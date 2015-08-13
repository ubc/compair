import datetime
import json

from data.fixtures.test_data import SimpleQuestionsTestData
from acj.models import PostsForQuestions
from acj.tests.test_acj import ACJTestCase


class QuestionsAPITests(ACJTestCase):
    def setUp(self):
        super(QuestionsAPITests, self).setUp()
        self.data = SimpleQuestionsTestData()
        self.url = '/api/courses/' + str(self.data.get_course().id) + '/questions'

    def test_get_single_question(self):
        question_expected = self.data.get_questions()[0]
        questions_api_url = self.url + '/' + str(question_expected.id)
        # Test login required
        rv = self.client.get(questions_api_url)
        self.assert401(rv)
        # Test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.get(questions_api_url)
        self.assert403(rv)
        self.logout()
        self.login(self.data.get_unauthorized_student().username)
        rv = self.client.get(questions_api_url)
        self.assert403(rv)
        # Test non-existent question
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.get(self.url + '/939023')
        self.assert404(rv)
        # Test get actual question
        rv = self.client.get(questions_api_url)
        self.assert200(rv)
        self._verify_question(question_expected, rv.json['question'])

    def test_get_all_questions(self):
        # Test login required
        rv = self.client.get(self.url)
        self.assert401(rv)
        # Test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.get(self.url)
        self.assert403(rv)
        self.logout()
        self.login(self.data.get_unauthorized_student().username)
        rv = self.client.get(self.url)
        self.assert403(rv)
        # Test non-existent course
        rv = self.client.get('/api/courses/390484/questions')
        self.assert404(rv)
        self.logout()
        # Test receives all questions
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.get(self.url)
        self.assert200(rv)
        for i, expected in enumerate(self.data.get_questions()):
            actual = rv.json['questions'][i]
            self._verify_question(expected, actual)

    def test_create_question(self):
        now = datetime.datetime.utcnow()
        question_expected = {
            'title': 'this is a new question\'s title',
            'post': {'content': 'this is the new question\'s content.'},
            'answer_start': now.isoformat() + 'Z',
            'answer_end': (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            'num_judgement_req': 3}
        # Test login required
        rv = self.client.post(
            self.url,
            data=json.dumps(question_expected),
            content_type='application/json')
        self.assert401(rv)
        # Test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(
            self.url,
            data=json.dumps(question_expected),
            content_type='application/json')
        self.assert403(rv)
        self.logout()
        self.login(self.data.get_unauthorized_student().username)
        rv = self.client.post(
            self.url,
            data=json.dumps(question_expected),
            content_type='application/json')
        self.assert403(rv)
        self.logout()
        self.login(self.data.get_authorized_student().username)  # student post questions not implemented
        rv = self.client.post(
            self.url,
            data=json.dumps(question_expected),
            content_type='application/json')
        self.assert403(rv)
        self.logout()
        # Test bad format
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.post(
            self.url,
            data=json.dumps({'title': 'blah'}),
            content_type='application/json')
        self.assert400(rv)
        # Test actual creation
        rv = self.client.post(
            self.url,
            data=json.dumps(question_expected),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(
            question_expected['title'], rv.json['title'],
            "Question create did not return the same title!")
        self.assertEqual(
            question_expected['post']['content'], rv.json['post']['content'],
            "Question create did not return the same content!")
        # Test getting the question again
        rv = self.client.get(self.url + '/' + str(rv.json['id']))
        self.assert200(rv)
        self.assertEqual(
            question_expected['title'], rv.json['question']['title'],
            "Question create did not save title properly!")
        self.assertEqual(
            question_expected['post']['content'], rv.json['question']['post']['content'],
            "Question create did not save content properly!")

    def test_edit_question(self):
        question = self.data.get_questions()[0]
        url = self.url + '/' + str(question.id)
        expected = {
            'id': question.id,
            'title': 'This is the new title.',
            'post': {'content': 'new_content'},
            'answer_start': question.answer_start.isoformat() + 'Z',
            'answer_end': question.answer_end.isoformat() + 'Z',
            'num_judgement_req': question.num_judgement_req
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_instructor().username)
        invalid_url = '/api/courses/999/questions/' + str(question.id)
        rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
        self.assert404(rv)

        # test invalid question id
        invalid_url = self.url + '/999'
        rv = self.client.post(invalid_url, data=json.dumps(expected), content_type='application/json')
        self.assert404(rv)

        # test edit by author
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert200(rv)
        self._verify_question(question, rv.json)
        self.logout()

        # test edit by user who can manage posts (TA)
        self.login(self.data.get_authorized_ta().username)
        ta_expected = {
            'id': question.id,
            'title': 'Another Title',
            'post': {'content': 'new_content'},
            'answer_start': question.answer_start.isoformat() + 'Z',
            'answer_end': question.answer_end.isoformat() + 'Z',
            'num_judgement_req': question.num_judgement_req
        }
        rv = self.client.post(url, data=json.dumps(ta_expected), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(ta_expected['title'], rv.json['title'])
        self.assertEqual(ta_expected['post']['content'], rv.json['post']['content'])

    def test_delete_question(self):
        # Test deleting the question
        ques_id = PostsForQuestions.query.first().id
        self.logout()
        expected_ret = {'id': ques_id}
        self.login(self.data.get_authorized_student().username)
        rv = self.client.delete(self.url + '/' + str(ques_id))
        self.assert403(rv)
        self.assertEqual(
            'Forbidden', rv.json['message'],
            "User does not have the authorization to delete the question.")
        self.logout()
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.delete(self.url + '/' + str(ques_id))
        self.assert200(rv)
        self.assertEqual(expected_ret['id'], rv.json['id'], "Question " + str(rv.json['id']) + " deleted successfully")

    def _verify_question(self, expected, actual):
        self.assertEqual(expected.title, actual['title'])
        self.assertEqual(expected.posts_id, actual['post']['id'])
        self.assertEqual(expected.post.content, actual['post']['content'])
        self.assertEqual(expected.post.user.id, actual['post']['user']['id'])
