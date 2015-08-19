import json

from data.fixtures.test_data import AnswerCommentsTestData
from acj.tests.test_acj import ACJTestCase


class AnswerCommentsAPITests(ACJTestCase):
    def setUp(self):
        super(AnswerCommentsAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.questions = self.data.get_questions()
        self.answers = self.data.get_answers_by_question()

    def _build_url(self, course_id, question_id, answer_id, comment_id=None):
        url = \
            '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + \
            '/answers/' + str(answer_id) + '/comments'
        if comment_id:
            url += '/' + str(comment_id)
        return url

    def test_get_all_answer_comments(self):
        url = self._build_url(self.course.id, self.questions[0].id, self.answers[self.questions[0].id][0].id)

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
        invalid_url = self._build_url(999, self.questions[0].id, self.answers[self.questions[0].id][0].id)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid question id
        invalid_url = self._build_url(self.course.id, 999, self.answers[self.questions[0].id][0].id)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid answer id
        invalid_url = self._build_url(self.course.id, self.questions[0].id, 999)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test authorized user
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(1, len(rv.json['objects']))
        self.assertEqual(
            self.data.get_answer_comments_by_question(self.questions[0])[1].content,
            rv.json['objects'][0]['content'])

    def test_create_answer_comment(self):
        url = self._build_url(self.course.id, self.questions[0].id, self.answers[self.questions[0].id][0].id)
        content = {'content': 'great answer'}

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_instructor().username)
        invalid_url = self._build_url(999, self.questions[0].id, self.answers[self.questions[0].id][0].id)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid question id
        invalid_url = self._build_url(self.course.id, 999, self.answers[self.questions[0].id][0].id)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid answer id
        invalid_url = self._build_url(self.course.id, self.questions[0].id, 999)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test empty content
        empty = content.copy()
        empty['content'] = ''
        rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
        self.assert400(rv)

        # test authorized user
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])

    def test_get_single_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)

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
        invalid_url = self._build_url(
            999, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid answer id
        invalid_url = self._build_url(self.course.id, self.questions[0].id, 999, comment.id)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid comment id
        invalid_url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, 999)
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test authorized instructor
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(comment.content, rv.json['content'])
        self.logout()

        # test author
        self.login(self.data.get_extra_student(0).username)
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(comment.content, rv.json['content'])
        self.logout()

    def test_edit_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)
        content = {'id': comment.id, 'content': 'insightful.'}

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_instructor().username)
        invalid_url = self._build_url(
            999, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid answer id
        invalid_url = self._build_url(self.course.id, self.questions[0].id, 999, comment.id)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid comment id
        invalid_url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, 999)
        rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test unmatched comment ids
        invalid = content.copy()
        invalid['id'] = self.data.get_answer_comments_by_question(self.questions[0])[1].id
        rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
        self.assert400(rv)
        self.assertEqual("Comment id does not match URL.", rv.json['error'])

        # test empty content
        empty = content.copy()
        empty['content'] = ''
        rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
        self.assert400(rv)
        self.assertEqual("The comment content is empty!", rv.json['error'])
        self.logout()

        # test authorized instructor
        self.login(self.data.get_authorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])
        self.logout()

        # test author
        self.login(self.data.get_extra_student(0).username)
        content['content'] = 'I am the author'
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])
        self.logout()

    def test_delete_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.delete(url)
        self.assert403(rv)
        self.logout()

        # test invalid comment id
        self.login(self.data.get_authorized_instructor().username)
        invalid_url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, 999)
        rv = self.client.delete(invalid_url)
        self.assert404(rv)

        # test authorized instructor
        rv = self.client.delete(url)
        self.assert200(rv)
        self.assertEqual(comment.id, rv.json['id'])
        self.logout()

        # test author
        self.login(self.data.get_extra_student(1).username)
        comment = self.data.get_answer_comments_by_question(self.questions[0])[1]
        url = self._build_url(
            self.course.id, self.questions[0].id,
            self.answers[self.questions[0].id][0].id, comment.id)
        rv = self.client.delete(url)
        self.assert200(rv)
        self.assertEqual(comment.id, rv.json['id'])
        self.logout()

    def test_get_user_answer_comments(self):
        url = \
            '/api/courses/' + str(self.course.id) + '/questions/' + str(self.questions[0].id) + \
            '/answers/' + str(self.answers[self.questions[0].id][1].id) + '/users/comments'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid course id
        self.login(self.data.get_extra_student(0).username)
        invalid_url = \
            '/api/courses/999/questions/' + str(self.questions[0].id) + \
            '/answers/' + str(self.answers[self.questions[0].id][0].id) + '/users/comments'
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid question id
        invalid_url = \
            '/api/courses/' + str(self.course.id) + '/questions/999' + \
            '/answers/' + str(self.answers[self.questions[0].id][0].id) + '/users/comments'
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test invalid answer id
        invalid_url = \
            '/api/courses/' + str(self.course.id) + '/questions/' + str(self.questions[0].id) + \
            '/answers/999/users/comments'
        rv = self.client.get(invalid_url)
        self.assert404(rv)

        # test user
        rv = self.client.get(url)
        comment1 = self.data.get_answer_comments_by_question(self.questions[0])[0]
        self.assert200(rv)
        self.assertEqual(1, len(rv.json['object']))
        self.assertEqual(comment1.content, rv.json['object'][0]['content'])
