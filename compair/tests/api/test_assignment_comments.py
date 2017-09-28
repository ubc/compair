import json

from data.fixtures.test_data import AssignmentCommentsTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import mail


class AssignmentCommentsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AssignmentCommentsAPITests, self).setUp()
        self.data = AssignmentCommentsTestData()
        self.course = self.data.get_course()
        self.assignment1 = self.data.get_assignments()[0]
        self.assignment2 = self.data.get_assignments()[1]

    def _build_url(self, course_uuid, assignment_uuid, comment_uuid=None):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/comments'
        if comment_uuid:
            url += '/' + comment_uuid
        return url

    def test_get_all_assignment_comment(self):
        url = self._build_url(self.course.uuid, self.assignment2.uuid)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self._build_url("999", self.assignment2.uuid))
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.get(self._build_url(self.course.uuid, "999"))
            self.assert404(rv)

            # test authorized user
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            comment = self.data.get_instructor_assignment_comment()
            self.assertEqual(comment.uuid, rv.json['objects'][0]['id'])
            self.assertEqual(comment.content, rv.json['objects'][0]['content'])

    def test_create_assignment_comment(self):
        url = self._build_url(self.course.uuid, self.assignment1.uuid)
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
                self._build_url("999", self.assignment1.uuid),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.course.uuid, "999"),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test empty content
            empty = {'content': ''}
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)

            # test authorized student
            with mail.record_messages() as outbox:
                rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(content['content'], rv.json['content'])

                self.assertEqual(len(outbox), 1)
                self.assertEqual(outbox[0].subject, "New Help Comment in "+self.data.get_course().name)
                self.assertEqual(outbox[0].recipients, [self.data.get_authorized_instructor().email])

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            with mail.record_messages() as outbox:
                rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(content['content'], rv.json['content'])

                self.assertEqual(len(outbox), 0)

        # test authorized teaching assistant
        with self.login(self.data.get_authorized_ta().username):
            with mail.record_messages() as outbox:
                rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(content['content'], rv.json['content'])

                self.assertEqual(len(outbox), 0)

    def test_get_single_assignment_comment(self):
        comment = self.data.get_student_assignment_comment()
        url = self._build_url(self.course.uuid, self.assignment2.uuid, comment.uuid)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(self._build_url("999", self.assignment2.uuid, comment.uuid))
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.get(self._build_url(self.course.uuid, "999", comment.uuid))
            self.assert404(rv)

            # test invalid comment id
            rv = self.client.get(self._build_url(self.course.uuid, self.assignment2.uuid, "999"))
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
        url = self._build_url(self.course.uuid, self.assignment2.uuid, comment.uuid)
        content = {
            'id': comment.uuid,
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
            invalid['id'] = self.data.get_instructor_assignment_comment().uuid
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Help Comment Not Saved", rv.json['title'])
            self.assertEqual("The comment's ID does not match the URL, which is required in order to save the comment.",
                rv.json['message'])

            # test invalid course id
            rv = self.client.post(
                self._build_url("999", self.assignment2.uuid, comment.uuid),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.course.uuid, "999", comment.uuid),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test invalid comment id
            rv = self.client.post(
                self._build_url(self.course.uuid, self.assignment2.uuid, "999"),
                data=json.dumps(content),
                content_type='application/json')
            self.assert404(rv)

            # test empty content
            empty = content.copy()
            empty['content'] = ''
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Help Comment Not Saved", rv.json['title'])
            self.assertEqual("Please provide content in the text editor and try saving again.", rv.json['message'])

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
        url = self._build_url(self.course.uuid, self.assignment2.uuid, comment.uuid)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid comment id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(self._build_url(self.course.uuid, self.assignment2.uuid, "999"))
            self.assert404(rv)

            # test author
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.uuid, rv.json['id'])

            # test authorized instructor
            comment = self.data.get_student_assignment_comment()
            url = self._build_url(self.course.uuid, self.assignment1.uuid, comment.uuid)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.uuid, rv.json['id'])
