import json

from data.fixtures.test_data import AssignmentCommentsTestData
from acj.tests.test_acj import ACJAPITestCase


class AssignmentCommentsAPITests(ACJAPITestCase):
    def setUp(self):
        super(AssignmentCommentsAPITests, self).setUp()
        self.data = AssignmentCommentsTestData()
        self.course = self.data.get_course()
        self.assignment1 = self.data.get_assignments()[0]
        self.assignment2 = self.data.get_assignments()[1]

    def _build_url(self, course_id, assignment_id, comment_id=None):
        url = '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/comments'
        if comment_id:
            url += '/' + str(comment_id)
        return url

    def test_get_all_assignment_comment(self):
        url = self._build_url(self.course.id, self.assignment2.id)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self._build_url(999, self.assignment2.id))
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.get(self._build_url(self.course.id, 999))
            self.assert404(rv)

            # test authorized user
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            comment = self.data.get_instructor_assignment_comment()
            self.assertEqual(comment.id, rv.json['objects'][0]['id'])
            self.assertEqual(comment.content, rv.json['objects'][0]['content'])

    def test_create_assignment_comment(self):
        url = self._build_url(self.course.id, self.assignment1.id)
        content = {
            'content': 'This is some text.'
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(
                self._build_url(999, self.assignment1.id),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.course.id, 999),
                data=json.dumps(content),
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

    def test_get_single_assignment_comment(self):
        comment = self.data.get_student_assignment_comment()
        url = self._build_url(self.course.id, self.assignment2.id, comment.id)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self._build_url(999, self.assignment2.id, comment.id))
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.get(self._build_url(self.course.id, 999, comment.id))
            self.assert404(rv)

            # test invalid comment id
            rv = self.client.get(self._build_url(self.course.id, self.assignment2.id, 999))
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

        # test authorized TA
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

        # test authorized author
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

    def test_edit_assignment_comment(self):
        comment = self.data.get_student_assignment_comment()
        url = self._build_url(self.course.id, self.assignment2.id, comment.id)
        content = {
            'id': comment.id,
            'content': 'new comment'
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert403(rv)

        # test unmatched comment id
        with self.login(self.data.get_authorized_instructor().username):
            invalid = content.copy()
            invalid['id'] = self.data.get_instructor_assignment_comment().id
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Comment id does not match URL.", rv.json['error'])

            # test invalid course id
            rv = self.client.post(
                self._build_url(999, self.assignment2.id, comment.id),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.course.id, 999, comment.id),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid comment id
            rv = self.client.post(
                self._build_url(self.course.id, self.assignment2.id, 999),
                data=json.dumps(content),
                content_type='application/json')
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

        # test author
        with self.login(self.data.get_authorized_student().username):
            content['content'] = 'great assignment'
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])

    def test_delete_assignment_comment(self):
        comment = self.data.get_instructor_assignment_comment()
        url = self._build_url(self.course.id, self.assignment2.id, comment.id)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid comment id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(self._build_url(self.course.id, self.assignment2.id, 999))
            self.assert404(rv)

            # test author
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])

            # test authorized instructor
            comment = self.data.get_student_assignment_comment()
            url = self._build_url(self.course.id, self.assignment1.id, comment.id)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.id, rv.json['id'])
