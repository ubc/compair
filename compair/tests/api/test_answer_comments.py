import json
import six
import mock

from compair import db
from data.fixtures.test_data import AnswerCommentsTestData, LTITestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.api.answer_comment import api, AnswerCommentListAPI, AnswerCommentAPI
from compair.models import AnswerCommentType, AnswerComment, \
    CourseGrade, AssignmentGrade

class AnswerCommentListAPITests(ComPAIRAPITestCase):
    """ Tests for answer comment list API """
    resource = AnswerCommentListAPI
    api = api

    def setUp(self):
        super(AnswerCommentListAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.assignments = self.data.get_assignments()
        self.answers = self.data.get_answers_by_assignment()
        self.assignment = self.assignments[0]
        self.assignment.enable_self_evaluation = True
        db.session.commit()
        self.assignment.calculate_grades()
        self.lti_data = LTITestData()

    def test_get_all_answer_comments(self):
        url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid)

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
                course_uuid=self.course.id, assignment_uuid=self.assignment.uuid, answer_uuid="999")
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test authorized user
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(
                self.data.get_non_draft_answer_comments_by_assignment(self.assignment)[1].content, rv.json[0]['content'])
            self.assertIn(
                self.data.get_non_draft_answer_comments_by_assignment(self.assignment)[1].user_fullname,
                rv.json[0]['user']['fullname'])

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
            self.data.get_extra_student(0),
            self.answers[self.assignment.id][0],
            comment_type=AnswerCommentType.self_evaluation
        )
        draft_comment = AnswerCommentsTestData.create_answer_comment(
            self.data.get_extra_student(0),
            self.answers[self.assignment.id][0],
            comment_type=AnswerCommentType.evaluation,
            draft=True
        )

        base_params = {
            'course_uuid': self.course.uuid,
            'assignment_uuid': self.assignment.uuid,
        }

        with self.login(self.data.get_authorized_instructor().username):
            # no answer ids
            rv = self.client.get(self.get_url(**base_params))
            self.assert404(rv)

            params = dict(base_params, answer_ids=self.answers[self.assignment.id][0].uuid)
            extra_student2_answer_comment_uuid = self.data.get_answer_comments_by_assignment(self.assignment)[1].uuid
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))

            rv = self.client.get(self.get_url(self_evaluation='false', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(extra_student2_answer_comment_uuid, rv.json[0]['id'])

            rv = self.client.get(self.get_url(self_evaluation='only', **params))
            self.assert200(rv)
            # self.assertEqual(1, rv.json['total'])
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.uuid, rv.json[0]['id'])

            ids = [extra_student2_answer_comment_uuid, comment.uuid]
            rv = self.client.get(self.get_url(ids=','.join(str(x) for x in ids), **base_params))
            self.assert200(rv)
            # self.assertEqual(2, rv.json['total'])
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(self, ids, [c['id'] for c in rv.json])

            answer_ids = [answer.uuid for answer in self.answers[self.assignment.id]]
            params = dict(base_params, answer_ids=','.join(answer_ids))
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))

            rv = self.client.get(self.get_url(self_evaluation='false', **params))
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            self.assertNotIn(comment.uuid, (c['id'] for c in rv.json))

            rv = self.client.get(self.get_url(self_evaluation='only', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(comment.uuid, rv.json[0]['id'])

            answer_ids = [answer.uuid for answer in self.answers[self.assignment.id]]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(1).uuid)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))

            # test assignment_id filter
            rv = self.client.get(self.get_url(**base_params) + '?assignment_id=' + self.assignment.uuid)
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))
            six.assertCountEqual(
                self,
                [comment.uuid] + [c.uuid for c in self.data.get_non_draft_answer_comments_by_assignment(self.assignment)],
                [c['id'] for c in rv.json])

            rv = self.client.get(self.get_url(**base_params) + '?assignment_id=' + self.assignments[1].uuid)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(
                self,
                [c.uuid for c in self.data.get_non_draft_answer_comments_by_assignment(self.assignments[1])],
                [c['id'] for c in rv.json])

            # test user_ids filter
            user_ids = ','.join([self.data.get_extra_student(0).uuid])
            rv = self.client.get(
                self.get_url(user_ids=user_ids, **base_params) + '&assignment_id=' + self.assignment.uuid)
            self.assert200(rv)
            self.assertEqual(2, len(rv.json))
            six.assertCountEqual(
                self,
                [comment.uuid, self.data.answer_comments_by_assignment[self.assignment.id][0].uuid],
                [c['id'] for c in rv.json])

        with self.login(self.data.get_extra_student(1).username):
            answer_ids = [answer.uuid for answer in self.answers[self.assignment.id]]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(1).uuid)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))

            # answer is not from the student but comment is
            answer_ids = [self.answers[self.assignment.id][1].uuid]
            params = dict(base_params, answer_ids=','.join(answer_ids), user_ids=self.data.get_extra_student(0).uuid)
            rv = self.client.get(self.get_url(**params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(self.data.get_extra_student(0).uuid, rv.json[0]['user_id'])

        # test drafts
        with self.login(self.data.get_extra_student(0).username):
            params = dict(base_params, user_ids=self.data.get_extra_student(0).uuid)
            rv = self.client.get(self.get_url(draft='only', **params))
            self.assert200(rv)
            self.assertEqual(1, len(rv.json))
            self.assertEqual(draft_comment.uuid, rv.json[0]['id'])

            rv = self.client.get(self.get_url(draft='false', **params))
            self.assert200(rv)
            self.assertEqual(3, len(rv.json))

            rv = self.client.get(self.get_url(draft='true', **params))
            self.assert200(rv)
            self.assertEqual(4, len(rv.json))
            self.assertEqual(draft_comment.uuid, rv.json[0]['id'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_create_answer_comment(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid)
        content = {
            'comment_type': AnswerCommentType.private.value,
            'content': 'great answer'
        }

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
                course_uuid="999", assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid="999",
                answer_uuid=self.answers[self.assignment.id][0].uuid)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid, answer_uuid="999")
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test empty content
            empty = content.copy()
            empty['content'] = ''
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)

            # test empty comment type
            empty = content.copy()
            empty['comment_type'] = ''
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)

            # test authorized user
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])
            self.assertFalse(rv.json['draft'])

            # test authorized user draft
            draft_content = content.copy()
            draft_content['draft'] = True
            rv = self.client.post(url, data=json.dumps(draft_content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])
            self.assertTrue(rv.json['draft'])

            # test authorized user draft - empty content
            empty = draft_content.copy()
            empty['content'] = None
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(empty['content'], rv.json['content'])
            self.assertTrue(rv.json['draft'])

        with self.login(self.data.get_authorized_student().username):
            lti_consumer = self.lti_data.lti_consumer
            (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                self.data.get_authorized_student(), self.course, self.assignment)

            course_grade = CourseGrade.get_user_course_grade(self.course, self.data.get_authorized_student()).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, self.data.get_authorized_student()).grade

            content = {
                'comment_type': AnswerCommentType.self_evaluation.value,
                'content': 'great answer'
            }

            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)

            # grades should increase
            new_course_grade = CourseGrade.get_user_course_grade(self.course, self.data.get_authorized_student())
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, self.data.get_authorized_student())
            self.assertGreater(new_course_grade.grade, course_grade)
            self.assertGreater(new_assignment_grade.grade, assignment_grade)

            mocked_update_assignment_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id)]
            )
            mocked_update_assignment_grades_run.reset_mock()

            mocked_update_course_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id)]
            )
            mocked_update_assignment_grades_run.reset_mock()


class AnswerCommentAPITests(ComPAIRAPITestCase):
    """ Tests for answer comment API """
    resource = AnswerCommentAPI
    api = api

    def setUp(self):
        super(AnswerCommentAPITests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.course = self.data.get_course()
        self.assignments = self.data.get_assignments()
        self.answers = self.data.get_answers_by_assignment()
        self.assignment = self.assignments[0]
        self.assignment.enable_self_evaluation = True
        db.session.commit()
        self.assignment.calculate_grades()
        self.lti_data = LTITestData()

    def test_get_single_answer_comment(self):
        comment = self.data.get_answer_comments_by_assignment(self.assignment)[0]
        url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid)
        draft_comment = self.data.get_answer_comments_by_assignment(self.assignment)[2]
        draft_url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=draft_comment.uuid)

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test unauthorized user student fetching draft of another student
        with self.login(self.data.get_extra_student(0).username):
            rv = self.client.get(draft_url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = self.get_url(
                course_uuid="999", assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid="999", answer_comment_uuid=comment.uuid)
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid="999")
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

            # test draft
            rv = self.client.get(draft_url)
            self.assert200(rv)
            self.assertEqual(draft_comment.content, rv.json['content'])
            self.assertTrue(rv.json['draft'])

        # test author
        with self.login(self.data.get_extra_student(0).username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(comment.content, rv.json['content'])

        # test draft author
        with self.login(self.data.get_extra_student(1).username):
            rv = self.client.get(draft_url)
            self.assert200(rv)
            self.assertEqual(draft_comment.content, rv.json['content'])
            self.assertTrue(rv.json['draft'])


    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_edit_answer_comment(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        comment = self.data.get_answer_comments_by_assignment(self.assignment)[0]
        url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid
        )

        content = {
            'id': comment.uuid,
            'content': 'insightful.',
            'comment_type': AnswerCommentType.private.value
        }
        draft_comment = self.data.get_answer_comments_by_assignment(self.assignment)[2]
        draft_url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=draft_comment.uuid)
        draft_content = {
            'id': draft_comment.uuid,
            'content': 'insightful.',
            'comment_type': AnswerCommentType.private.value,
            'draft': True
        }

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
                course_uuid="999", assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid="999", answer_comment_uuid=comment.uuid)
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test invalid comment id
            invalid_url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid="999")
            rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
            self.assert404(rv)

            # test unmatched comment ids
            invalid = content.copy()
            invalid['id'] = self.data.get_answer_comments_by_assignment(self.assignment)[1].uuid
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("Comment id does not match URL.", rv.json['error'])

            # test empty content
            empty = content.copy()
            empty['content'] = ''
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)
            self.assertEqual("The comment content is empty!", rv.json['error'])

            # test empty comment_type
            empty = content.copy()
            empty['comment_type'] = ''
            rv = self.client.post(url, data=json.dumps(empty), content_type='application/json')
            self.assert400(rv)

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
            self.assertFalse(rv.json['draft'])

            # ignored setting draft to True when draft is already False
            content['draft'] = True
            rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])
            self.assertFalse(rv.json['draft'])

        # test draft author
        with self.login(self.data.get_extra_student(1).username):
            draft_content['content'] = 'I am the author'
            rv = self.client.post(draft_url, data=json.dumps(draft_content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(draft_content['content'], rv.json['content'])
            self.assertTrue(rv.json['draft'])

            # can change draft to False when draft is True
            draft_content['draft'] = False
            rv = self.client.post(draft_url, data=json.dumps(draft_content), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['draft'])

        answer = self.answers[self.assignment.id][0]
        self_evaluation = self.data.create_answer_comment(
            answer.user, answer, comment_type=AnswerCommentType.self_evaluation, draft=True)
        self_evaluation_url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=answer.uuid, answer_comment_uuid=self_evaluation.uuid)

        with self.login(answer.user.username):
            lti_consumer = self.lti_data.lti_consumer
            (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                answer.user, self.course, self.assignment)

            course_grade = CourseGrade.get_user_course_grade(self.course, answer.user).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, answer.user).grade
            content = {
                'id': self_evaluation.uuid,
                'content': 'insightful.',
                'comment_type': AnswerCommentType.self_evaluation.value,
                'draft': True
            }

            rv = self.client.post(self_evaluation_url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(content['content'], rv.json['content'])
            self.assertTrue(rv.json['draft'])

            # grades should not change
            new_course_grade = CourseGrade.get_user_course_grade(self.course, answer.user).grade
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, answer.user).grade
            self.assertEqual(new_course_grade, course_grade)
            self.assertEqual(new_assignment_grade, assignment_grade)

            # can change draft to False when draft is True
            content['draft'] = False
            rv = self.client.post(self_evaluation_url, data=json.dumps(content), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['draft'])

            # grades should increase
            new_course_grade = CourseGrade.get_user_course_grade(self.course, answer.user)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, answer.user)
            self.assertGreater(new_course_grade.grade, course_grade)
            self.assertGreater(new_assignment_grade.grade, assignment_grade)

            mocked_update_assignment_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id)]
            )
            mocked_update_assignment_grades_run.reset_mock()

            mocked_update_course_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id)]
            )
            mocked_update_course_grades_run.reset_mock()


    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_delete_answer_comment(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        comment = self.data.get_answer_comments_by_assignment(self.assignment)[0]
        url = self.get_url(
            course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
            answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid)

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
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid="999")
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.uuid, rv.json['id'])

        # test author
        with self.login(self.data.get_extra_student(1).username):
            comment = self.data.get_answer_comments_by_assignment(self.assignment)[1]
            url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid=self.answers[self.assignment.id][0].uuid, answer_comment_uuid=comment.uuid)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(comment.uuid, rv.json['id'])

        # test delete self-evaulation
        answer = self.answers[self.assignment.id][0]
        self_evaluation = self.data.create_answer_comment(answer.user, answer, comment_type=AnswerCommentType.self_evaluation)
        self.assignment.calculate_grade(answer.user)
        self.course.calculate_grade(answer.user)

        lti_consumer = self.lti_data.lti_consumer
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            answer.user, self.course, self.assignment)

        with self.login(self.data.get_authorized_instructor().username):
            course_grade = CourseGrade.get_user_course_grade(self.course, answer.user).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, answer.user).grade

            url = self.get_url(
                course_uuid=self.course.uuid, assignment_uuid=self.assignment.uuid,
                answer_uuid=answer.uuid, answer_comment_uuid=self_evaluation.uuid)
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(self_evaluation.uuid, rv.json['id'])

            # grades should decrease
            new_course_grade = CourseGrade.get_user_course_grade(self.course, answer.user)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.assignment, answer.user)
            self.assertLess(new_course_grade.grade, course_grade)
            self.assertLess(new_assignment_grade.grade, assignment_grade)

            mocked_update_assignment_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id)]
            )
            mocked_update_assignment_grades_run.reset_mock()

            mocked_update_course_grades_run.assert_called_once_with(
                lti_consumer.id,
                [(lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id)]
            )
            mocked_update_course_grades_run.reset_mock()
