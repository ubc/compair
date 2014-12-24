import json

from data.fixtures.test_data import QuestionCommentsTestData

from acj.tests.test_acj import ACJTestCase


class QuestionCommentsAPITests(ACJTestCase):
    def setUp(self):
        super(QuestionCommentsAPITests, self).setUp()
        self.data = QuestionCommentsTestData()
        self.course = self.data.get_course()
        self.question1 = self.data.get_questions()[0]
        self.question2 = self.data.get_questions()[1]

    def _build_url(self, course_id, question_id, comment_id = None):
        url = '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/comments'
        if comment_id:
            url += '/' + str(comment_id)
        return url

    def test_get_all_question_comment(self):
        url = self._build_url(self.course.id, self.question2.id)

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
        rv = self.client.get(self._build_url(999, self.question2.id))
        self.assert404(rv)

        # test invalid question id
        rv = self.client.get(self._build_url(self.course.id, 999))
        self.assert404(rv)

        # test authorized user
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(1, len(rv.json['objects']))
        comment = self.data.get_instructor_ques_comment()
        self.assertEqual(comment.postsforcomments_id, rv.json['objects'][0]['postsforcomments']['id'])
        self.assertEqual(comment.postsforcomments.post.content, rv.json['objects'][0]['content'])

    def test_create_question_comment(self):
        url = self._build_url(self.course.id, self.question1.id)
        content = {
            'content': 'This is some text.'
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test invalid course id
        self.login(self.data.get_authorized_student().username)
        rv = self.client.post(self._build_url(999, self.question1.id), data=json.dumps(content),
                    content_type='application/json')
        self.assert404(rv)

        # test invalid question id
        rv = self.client.post(self._build_url(self.course.id, 999), data=json.dumps(content),
                    content_type='application/json')
        self.assert404(rv)

        # test empty content
        empty = {'content': ''}
        rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
        self.assert400(rv)

        # test authorized user
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])

    def test_get_single_question_comment(self):
        comment = self.data.get_student_ques_comment()
        url = self._build_url(self.course.id, self.question2.id, comment.id)

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
        rv = self.client.get(self._build_url(999, self.question2.id, comment.id))
        self.assert404(rv)

        # test invalid question id
        rv = self.client.get(self._build_url(self.course.id, 999, comment.id))
        self.assert404(rv)

        # test invalid comment id
        rv = self.client.get(self._build_url(self.course.id, self.question2.id, 999))
        self.assert404(rv)

        # test authorized instructor
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(comment.content, rv.json['content'])
        self.logout()

        # test authorized TA
        self.login(self.data.get_authorized_ta().username)
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(comment.content, rv.json['content'])
        self.logout()

        # test authorized author
        self.login(self.data.get_authorized_student().username)
        rv = self.client.get(url)
        self.assert200(rv)
        self.assertEqual(comment.content, rv.json['content'])

    def test_edit_question_comment(self):
        comment = self.data.get_student_ques_comment()
        url = self._build_url(self.course.id, self.question2.id, comment.id)
        content = {
            'id': comment.id,
            'content': 'new comment'
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        self.login(self.data.get_unauthorized_instructor().username)
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert403(rv)
        self.logout()

        # test unmatched comment id
        self.login(self.data.get_authorized_instructor().username)
        invalid = content.copy()
        invalid['id'] = self.data.get_instructor_ques_comment().id
        rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
        self.assert400(rv)
        self.assertEqual("Comment id does not match URL.", rv.json['error'])

        # test invalid course id
        rv = self.client.post(self._build_url(999, self.question2.id, comment.id),
                    data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid question id
        rv = self.client.post(self._build_url(self.course.id, 999, comment.id),
                    data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test invalid comment id
        rv = self.client.post(self._build_url(self.course.id, self.question2.id, 999),
                    data=json.dumps(content), content_type='application/json')
        self.assert404(rv)

        # test empty content
        empty = content.copy()
        empty['content'] = ''
        rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
        self.assert400(rv)
        self.assertEqual("The comment content is empty!", rv.json['error'])

        # test authorized instructor
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])
        self.logout()

        # test author
        self.login(self.data.get_authorized_student().username)
        content['content'] = 'great question'
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert200(rv)
        self.assertEqual(content['content'], rv.json['content'])
        self.logout()

    def test_delete_question_comment(self):
        comment = self.data.get_instructor_ques_comment()
        url = self._build_url(self.course.id, self.question2.id, comment.id)

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
        rv = self.client.delete(self._build_url(self.course.id, self.question2.id, 999))
        self.assert404(rv)

        # test author
        rv = self.client.delete(url)
        self.assert200(rv)
        self.assertEqual(comment.id, rv.json['id'])

        # test authorized instructor
        comment = self.data.get_student_ques_comment()
        url = self._build_url(self.course.id, self.question1.id, comment.id)
        rv = self.client.delete(url)
        self.assert200(rv)
        self.assertEqual(comment.id, rv.json['id'])