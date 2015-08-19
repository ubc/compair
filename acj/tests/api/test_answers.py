import json

from data.fixtures.test_data import SimpleAnswersTestData
from acj.models import UserTypesForSystem, UserTypesForCourse, PostsForAnswers
from acj.tests.test_acj import ACJTestCase


class AnswersAPITests(ACJTestCase):
    def setUp(self):
        super(AnswersAPITests, self).setUp()
        self.data = SimpleAnswersTestData(30)
        self.question = self.data.get_questions()[1]
        self.base_url = self._build_url(self.data.get_course().id, self.question.id)

    def _build_url(self, course_id, question_id, tail=""):
        url = \
            '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/answers' + \
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
        expected_answers = PostsForAnswers.query.filter_by(questions_id=self.question.id).paginate(1, 20)
        for i, expected in enumerate(expected_answers.items):
            actual = actual_answers[i]
            self.assertEqual(expected.post.content, actual['content'])
        self.assertEqual(1, rv.json['page'])
        self.assertEqual(2, rv.json['pages'])
        self.assertEqual(20, rv.json['per_page'])
        self.assertEqual(expected_answers.total, rv.json['total'])

    def test_create_answer(self):
        # test login required
        expected_answer = {'content': 'this is some answer content'}
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert401(response)
        # test unauthorized users
        self.login(self.data.get_unauthorized_student().username)
        response = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
        self.assert403(response)
        self.logout()
        self.login(self.data.get_unauthorized_instructor().username)
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert403(response)
        self.logout()
        # test invalid format
        self.login(self.data.get_authorized_student().username)
        invalid_answer = {'post': {'blah': 'blah'}}
        response = self.client.post(
            self.base_url,
            data=json.dumps(invalid_answer),
            content_type='application/json')
        self.assert400(response)
        # test invalid question
        response = self.client.post(
            self._build_url(self.data.get_course().id, 9392402),
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert404(response)
        # test invalid course
        response = self.client.post(
            self._build_url(9392402, self.question.id),
            data=json.dumps(expected_answer), content_type='application/json')
        self.assert404(response)
        # test create successful
        self.logout()
        self.login(self.data.get_authorized_instructor().username)

        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert200(response)
        # retrieve again and verify
        rv = json.loads(response.data.decode('utf-8'))
        actual_answer = PostsForAnswers.query.get(rv['id'])
        self.assertEqual(expected_answer['content'], actual_answer.post.content)

        # test instructor could submit multiple answers for his/her own
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert200(response)
        rv = json.loads(response.data.decode('utf-8'))
        actual_answer = PostsForAnswers.query.get(rv['id'])
        self.assertEqual(expected_answer['content'], actual_answer.post.content)

        # test instructor could submit on behave of a student
        expected_answer.update({'user': self.data.get_authorized_student().id})
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert200(response)
        rv = json.loads(response.data.decode('utf-8'))
        actual_answer = PostsForAnswers.query.get(rv['id'])
        self.assertEqual(expected_answer['content'], actual_answer.post.content)

        # test instructor can not submit additional answers for a student
        expected_answer.update({'user': self.data.get_authorized_student().id})
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert400(response)
        rv = json.loads(response.data.decode('utf-8'))
        self.assertEqual({"error": "An answer has already been submitted."}, rv)

        self.logout()

    def test_get_answer(self):
        question_id = self.data.get_questions()[0].id
        answer = self.data.get_answers_by_question()[question_id][0]

        # test login required
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_student().username)
        rv = self.client.get(self._build_url(999, question_id, '/' + str(answer.id)))
        self.assert404(rv)

        # test invalid answer id
        rv = self.client.get(self._build_url(self.data.get_course().id, question_id, '/' + str(999)))
        self.assert404(rv)

        # test authorized student
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert200(rv)
        self.assertEqual(question_id, rv.json['questions_id'])
        self.assertEqual(answer.post.users_id, rv.json['user_id'])
        self.assertEqual(answer.post.content, rv.json['content'])
        self.logout()

        # test authorized teaching assistant
        self.login(self.data.get_authorized_ta().username)
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert200(rv)
        self.assertEqual(question_id, rv.json['questions_id'])
        self.assertEqual(answer.post.users_id, rv.json['user_id'])
        self.assertEqual(answer.post.content, rv.json['content'])
        self.logout()

        # test authorized instructor
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert200(rv)
        self.assertEqual(question_id, rv.json['questions_id'])
        self.assertEqual(answer.post.users_id, rv.json['user_id'])
        self.assertEqual(answer.post.content, rv.json['content'])
        self.logout()

    def test_edit_answer(self):
        question_id = self.data.get_questions()[0].id
        answer = self.data.get_answers_by_question()[question_id][0]
        expected = {'id': str(answer.id), 'content': 'This is an edit'}

        # test login required
        rv = self.client.post(
            self.base_url + '/' + str(answer.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_extra_student(1).username)
        rv = self.client.post(
            self.base_url + '/' + str(answer.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.post(
            self._build_url(999, question_id, '/' + str(answer.id)),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert404(rv)

        # test invalid question id
        rv = self.client.post(
            self._build_url(self.data.get_course().id, 999, '/' + str(answer.id)),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert404(rv)

        # test invalid answer id
        rv = self.client.post(
            self.base_url + '/999',
            data=json.dumps(expected),
            content_type='application/json')
        self.assert404(rv)
        self.logout()

        # test unmatched answer id
        self.login(self.data.get_extra_student(1).username)
        rv = self.client.post(
            self.base_url + '/' + str(self.data.get_answers_by_question()[question_id][1].id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert400(rv)
        self.logout()

        # test edit by author
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.post(
            self.base_url + '/' + str(answer.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(answer.id, rv.json['id'])
        self.assertEqual('This is an edit', rv.json['content'])
        self.logout()

        # test edit by user that can manage posts
        expected['content'] = 'This is another edit'
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.post(
            self.base_url + '/' + str(answer.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(answer.id, rv.json['id'])
        self.assertEqual('This is another edit', rv.json['content'])
        self.logout()

    def test_delete_answer(self):
        question_id = self.data.get_questions()[0].id
        answer_id = self.data.get_answers_by_question()[question_id][0].id

        # test login required
        rv = self.client.delete(self.base_url + '/' + str(answer_id))
        self.assert401(rv)

        # test unauthorized users
        self.login(self.data.get_extra_student(1).username)
        rv = self.client.delete(self.base_url + '/' + str(answer_id))
        self.assert403(rv)
        self.logout()

        # test invalid answer id
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.delete(self.base_url + '/999')
        self.assert404(rv)

        # test deletion by author
        rv = self.client.delete(self.base_url + '/' + str(answer_id))
        self.assert200(rv)
        self.assertEqual(answer_id, rv.json['id'])
        self.logout()

        # test deletion by user that can manage posts
        self.login(self.data.get_authorized_instructor().username)
        answer_id2 = self.data.get_answers_by_question()[question_id][1].id
        rv = self.client.delete(self.base_url + '/' + str(answer_id2))
        self.assert200(rv)
        self.assertEqual(answer_id2, rv.json['id'])
        self.logout()

    def test_get_user_answers(self):
        question_id = self.data.get_questions()[0].id
        answer = self.data.get_answers_by_question()[question_id][0]
        url = self._build_url(self.data.get_course().id, question_id, '/user')

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid course
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.get(self._build_url(999, question_id, '/user'))
        self.assert404(rv)

        # test invalid question
        rv = self.client.get(self._build_url(self.data.get_course().id, 999, '/user'))
        self.assert404(rv)

        # test successful queries
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(1, len(rv.json['answer']))
        self.assertEqual(answer.id, rv.json['answer'][0]['id'])
        self.assertEqual(answer.post.content, rv.json['answer'][0]['content'])
        self.logout()

        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(0, len(rv.json['answer']))
        self.logout()

    def test_flag_answer(self):
        answer = self.question.answers[0]
        flag_url = self.base_url + "/" + str(answer.id) + "/flagged"
        # test login required
        expected_flag_on = {'flagged': True}
        expected_flag_off = {'flagged': False}
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert401(rv)
        # test unauthorized users
        self.login(self.data.get_unauthorized_student().username)
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert403(rv)
        self.logout()
        # test flagging
        self.login(self.data.get_authorized_student().username)
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(
            expected_flag_on['flagged'],
            rv.json['flagged'],
            "Expected answer to be flagged.")
        # test unflagging
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_off),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(
            expected_flag_off['flagged'],
            rv.json['flagged'],
            "Expected answer to be flagged.")
        # test prevent unflagging by other students
        self.login(self.data.get_authorized_student().username)
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert200(rv)
        self.logout()
        # create another student
        other_student = self.data.create_user(UserTypesForSystem.TYPE_NORMAL)
        self.data.enrol_user(other_student, self.data.get_course(), UserTypesForCourse.TYPE_STUDENT)
        # try to unflag answer as other student, should fail
        self.login(other_student.username)
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_off),
            content_type='application/json')
        self.assert400(rv)
        self.logout()
        # test allow unflagging by instructor
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_off),
            content_type='application/json')
        self.assert200(rv)
        self.assertEqual(
            expected_flag_off['flagged'],
            rv.json['flagged'],
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
        self.login(self.data.get_extra_student(0).username)
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
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.get(answered_url)
        self.assert200(rv)
        expected = {str(question.id): 1 for question in self.data.get_questions()}
        self.assertEqual(expected, rv.json['answered'])
        self.logout()

    def test_get_answers_view(self):
        view_url = \
            '/api/courses/' + str(self.data.get_course().id) + '/questions/' + \
            str(self.data.get_questions()[0].id) + '/answers/view'

        # test login required
        rv = self.client.get(view_url)
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.get(view_url)
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.get('/api/courses/999/questions/' + str(self.data.get_questions()[0].id) + '/answers/view')
        self.assert404(rv)

        # test invalid question id
        rv = self.client.get('/api/courses/' + str(self.data.get_course().id) + '/questions/999/answers/view')
        self.assert404(rv)

        # test successful query
        rv = self.client.get(view_url)
        self.assert200(rv)
        expected = self.data.get_answers_by_question()[self.data.get_questions()[0].id]

        self.assertEqual(30, len(rv.json['answers']))
        for i, exp in enumerate(expected):
            actual = rv.json['answers'][str(exp.id)]
            self.assertEqual(exp.id, actual['id'])
            self.assertEqual(exp.post.content, actual['content'])
            self.assertFalse(actual['file'])

        self.logout()

        # test successful query - student
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.get(view_url)
        self.assert200(rv)

        actual = rv.json['answers']
        question_id = self.data.get_questions()[0].id
        expected = self.data.get_answers_by_question()[question_id][0]

        self.assertEqual(1, len(actual))
        self.assertTrue(str(expected.id) in actual)
        answer = actual[str(expected.id)]
        self.assertEqual(expected.id, answer['id'])
        self.assertEqual(expected.post.content, answer['content'])
        self.assertFalse(answer['file'])
        self.assertFalse('scores' in answer)

        self.logout()
