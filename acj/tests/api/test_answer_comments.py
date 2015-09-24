import json

from data.fixtures.test_data import AnswerCommentsTestData
from acj.tests.test_acj import ACJTestCase
from acj.comment import apiA, apiU, AnswerCommentListAPI, AnswerCommentAPI, UserAnswerCommentIdAPI


class AnswerCommentListAPITests(ACJTestCase):
    """ Tests for answer comment list API """
    api = apiA
    resource = AnswerCommentListAPI

    def setUp(self):
        super(AnswerCommentListAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.questions = self.data.get_questions()
        self.answers = self.data.get_answers_by_question()

    def test_get_all_answer_comments(self):
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][0].id)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id, answer_id=999)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test authorized user
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(
                self.data.get_answer_comments_by_question(self.questions[0])[1].content, rv.json[0]['content'])
            self.assertIn(
                self.data.get_answer_comments_by_question(self.questions[0])[1].user_fullname,
                rv.json[0]['user_fullname'])

        # test non-owner student of answer access comments
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json))

        # test owner student of answer access comments
        with self.login(self.data.get_extra_student(0).username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertNotIn('user_fullname', rv.json[0])

    def test_get_list_query_params(self):
        comment = AnswerCommentsTestData.create_answer_comment(
            self.data.get_extra_student(0), self.course, self.answers[self.questions[0].id][0], selfeval=True)

        base_params = {
            'course_id': self.course.id,
            'question_id': self.questions[0].id,
        }

        with self.login(self.data.get_authorized_instructor().username):
            # no answer ids
            rv = self.client.get(self.get_url(**base_params))
            self.assert404(rv)

            params = dict(base_params, answer_id=self.answers[self.questions[0].id][0].id)
            extra_student2_comment_id = self.data.get_answer_comments_by_question(self.questions[0])[1].id
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))

            rv = self.client.get(self.get_url(selfeval='false', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(extra_student2_comment_id, rv.json[0]['id'])

            rv = self.client.get(self.get_url(selfeval='only', **params))
            self.assert200(rv)
            # self.assertEqual(1, rv.json['total'])
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.id, rv.json[0]['id'])

            ids = [extra_student2_comment_id, comment.id]
            rv = self.client.get(self.get_url(ids=','.join(str(x) for x in ids), **base_params))
            self.assert200(rv)
            # self.assertEqual(2, rv.json['total'])
            self.assertEqual(2, len(rv.json))
            self.assertItemsEqual(ids, [c['id'] for c in rv.json])

            answer_ids = [str(answer.id) for answer in self.answers[self.questions[0].id]]
            params = dict(base_params, answer_ids=','.join(answer_ids))
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))

            rv = self.client.get(self.get_url(selfeval='false', **params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            self.assertNotIn(comment.id, (c['id'] for c in rv.json))

            rv = self.client.get(self.get_url(selfeval='only', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.id, rv.json[0]['id'])

            # test question_id filter
            rv = self.client.get(self.get_url(**base_params) + '?question_id=' + str(self.questions[0].id))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))
            self.assertItemsEqual(
                [comment.id] + [c.id for c in self.data.answer_comments_by_question[self.questions[0].id]],
                [c['id'] for c in rv.json])

            rv = self.client.get(self.get_url(**base_params) + '?question_id=' + str(self.questions[1].id))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            self.assertItemsEqual(
                [c.id for c in self.data.answer_comments_by_question[self.questions[1].id]],
                [c['id'] for c in rv.json])

            # test user_ids filter
            user_ids = ','.join([str(self.data.get_extra_student(0).id)])
            rv = self.client.get(
                self.get_url(user_ids=user_ids, **base_params) + '&question_id=' + str(self.questions[0].id))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            self.assertItemsEqual(
                [comment.id, self.data.answer_comments_by_question[self.questions[0].id][0].id],
                [c['id'] for c in rv.json])

    def test_create_answer_comment(self):
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][0].id)
        content = {'content': 'great answer'}

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = self.get_url(
                course_id=999, question_id=self.questions[0].id, answer_id=self.answers[self.questions[0].id][0].id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid question id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=999, answer_id=self.answers[self.questions[0].id][0].id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id, answer_id=999)
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


class AnswerCommentAPITests(ACJTestCase):
    """ Tests for answer comment API """
    api = apiA
    resource = AnswerCommentAPI

    def setUp(self):
        super(AnswerCommentAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.questions = self.data.get_questions()
        self.answers = self.data.get_answers_by_question()

    def test_get_single_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = self.get_url(
                course_id=999, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id, answer_id=999, comment_id=comment.id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=999)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

        # test author
        with self.login(self.data.get_extra_student(0).username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

    def test_edit_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)
        content = {'id': comment.id, 'content': 'insightful.'}

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = self.get_url(
                course_id=999, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id, answer_id=999, comment_id=comment.id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=999)
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

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])

        # test author
        with self.login(self.data.get_extra_student(0).username):
            content['content'] = 'I am the author'
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])

    def test_delete_answer_comment(self):
        comment = self.data.get_answer_comments_by_question(self.questions[0])[0]
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid comment id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=999)
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])

        # test author
        with self.login(self.data.get_extra_student(1).username):
            comment = self.data.get_answer_comments_by_question(self.questions[0])[1]
            url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id, comment_id=comment.id)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])


class UserAnswerCommentAPITests(ACJTestCase):
    """ Tests for user answer comment API """
    api = apiU
    resource = UserAnswerCommentIdAPI

    def setUp(self):
        super(UserAnswerCommentAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.questions = self.data.get_questions()
        self.answers = self.data.get_answers_by_question()

    def test_get_user_answer_comments(self):
        url = self.get_url(
            course_id=self.course.id, question_id=self.questions[0].id,
            answer_id=self.answers[self.questions[0].id][1].id)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid course id
        with self.login(self.data.get_extra_student(0).username):
            invalid_url = self.get_url(
                course_id=999, question_id=self.questions[0].id,
                answer_id=self.answers[self.questions[0].id][0].id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid question id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=999,
                answer_id=self.answers[self.questions[0].id][0].id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, question_id=self.questions[0].id,
                answer_id=999)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test user
            rv = self.client.get(url)
            comment1 = self.data.get_answer_comments_by_question(self.questions[0])[0]
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['object']))
            self.assertEqual(comment1.content, rv.json['object'][0]['content'])
