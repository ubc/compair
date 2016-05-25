import json
import six

from data.fixtures.test_data import AnswerCommentsTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.api.answer_comment import api, AnswerCommentListAPI, AnswerCommentAPI


class AnswerCommentListAPITests(ACJAPITestCase):
    """ Tests for answer comment list API """
    resource = AnswerCommentListAPI
    api = api

    def setUp(self):
        super(AnswerCommentListAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.assignments = self.data.get_assignments()
        self.answers = self.data.get_answers_by_assignment()

    def test_get_all_answer_comments(self):
        url = self.get_url(
            course_id=self.course.id, assignment_id=self.assignments[0].id,
            answer_id=self.answers[self.assignments[0].id][0].id)

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
                course_id=self.course.id, assignment_id=self.assignments[0].id, answer_id=999)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test authorized user
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(
                self.data.get_answer_comments_by_assignment(self.assignments[0])[1].content, rv.json[0]['content'])
            self.assertIn(
                self.data.get_answer_comments_by_assignment(self.assignments[0])[1].user_fullname,
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
            self.data.get_extra_student(0), self.answers[self.assignments[0].id][0], self_eval=True)

        base_params = {
            'course_id': self.course.id,
            'assignment_id': self.assignments[0].id,
        }

        with self.login(self.data.get_authorized_instructor().username):
            # no answer ids
            rv = self.client.get(self.get_url(**base_params))
            self.assert404(rv)

            params = dict(base_params, answer_ids=self.answers[self.assignments[0].id][0].id)
            extra_student2_answer_comment_id = self.data.get_answer_comments_by_assignment(self.assignments[0])[1].id
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))

            rv = self.client.get(self.get_url(self_eval='false', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(extra_student2_answer_comment_id, rv.json[0]['id'])

            rv = self.client.get(self.get_url(self_eval='only', **params))
            self.assert200(rv)
            # self.assertEqual(1, rv.json['total'])
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.id, rv.json[0]['id'])

            ids = [extra_student2_answer_comment_id, comment.id]
            rv = self.client.get(self.get_url(ids=','.join(str(x) for x in ids), **base_params))
            self.assert200(rv)
            # self.assertEqual(2, rv.json['total'])
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(self, ids, [c['id'] for c in rv.json])

            answer_ids = [str(answer.id) for answer in self.answers[self.assignments[0].id]]
            params = dict(base_params, answer_ids=','.join(answer_ids))
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))

            rv = self.client.get(self.get_url(self_eval='false', **params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            self.assertNotIn(comment.id, (c['id'] for c in rv.json))

            rv = self.client.get(self.get_url(self_eval='only', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.id, rv.json[0]['id'])

            answer_ids = [str(answer.id) for answer in self.answers[self.assignments[0].id]]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(1).id)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))

            # test assignment_id filter
            rv = self.client.get(self.get_url(**base_params) + '?assignment_id=' + str(self.assignments[0].id))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))
            six.assertCountEqual(
                self,
                [comment.id] + [c.id for c in self.data.answer_comments_by_assignment[self.assignments[0].id]],
                [c['id'] for c in rv.json])

            rv = self.client.get(self.get_url(**base_params) + '?assignment_id=' + str(self.assignments[1].id))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(
                self,
                [c.id for c in self.data.answer_comments_by_assignment[self.assignments[1].id]],
                [c['id'] for c in rv.json])

            # test user_ids filter
            user_ids = ','.join([str(self.data.get_extra_student(0).id)])
            rv = self.client.get(
                self.get_url(user_ids=user_ids, **base_params) + '&assignment_id=' + str(self.assignments[0].id))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(
                self,
                [comment.id, self.data.answer_comments_by_assignment[self.assignments[0].id][0].id],
                [c['id'] for c in rv.json])

        with self.login(self.data.get_extra_student(1).username):
            answer_ids = [str(answer.id) for answer in self.answers[self.assignments[0].id]]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(1).id)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))

            # answer is not from the student but comment is
            answer_ids = [str(self.answers[self.assignments[0].id][1].id)]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(0).id)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(self.data.get_extra_student(0).id, rv.json[0]['user_id'])

    def test_create_answer_comment(self):
        url = self.get_url(
            course_id=self.course.id, assignment_id=self.assignments[0].id,
            answer_id=self.answers[self.assignments[0].id][0].id)
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
                course_id=999, assignment_id=self.assignments[0].id, answer_id=self.answers[self.assignments[0].id][0].id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=999, answer_id=self.answers[self.assignments[0].id][0].id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id, answer_id=999)
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


class AnswerCommentAPITests(ACJAPITestCase):
    """ Tests for answer comment API """
    resource = AnswerCommentAPI
    api = api

    def setUp(self):
        super(AnswerCommentAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.assignments = self.data.get_assignments()
        self.answers = self.data.get_answers_by_assignment()

    def test_get_single_answer_comment(self):
        comment = self.data.get_answer_comments_by_assignment(self.assignments[0])[0]
        url = self.get_url(
            course_id=self.course.id, assignment_id=self.assignments[0].id,
            answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)

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
                course_id=999, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id, answer_id=999, answer_comment_id=comment.id)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=999)
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
        comment = self.data.get_answer_comments_by_assignment(self.assignments[0])[0]
        url = self.get_url(
            course_id=self.course.id, assignment_id=self.assignments[0].id,
            answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)
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
                course_id=999, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id, answer_id=999, answer_comment_id=comment.id)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=999)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test unmatched comment ids
            invalid = content.copy()
            invalid['id'] = self.data.get_answer_comments_by_assignment(self.assignments[0])[1].id
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
        comment = self.data.get_answer_comments_by_assignment(self.assignments[0])[0]
        url = self.get_url(
            course_id=self.course.id, assignment_id=self.assignments[0].id,
            answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)

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
                course_id=self.course.id, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=999)
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])

        # test author
        with self.login(self.data.get_extra_student(1).username):
            comment = self.data.get_answer_comments_by_assignment(self.assignments[0])[1]
            url = self.get_url(
                course_id=self.course.id, assignment_id=self.assignments[0].id,
                answer_id=self.answers[self.assignments[0].id][0].id, answer_comment_id=comment.id)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])
