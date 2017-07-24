import json
import datetime
import mock

from compair import db
from data.fixtures import AnswerFactory
from data.fixtures.test_data import TestFixture, LTITestData
from compair.models import Answer, CourseGrade, AssignmentGrade, \
    CourseRole, SystemRole
from compair.tests.test_compair import ComPAIRAPITestCase, ComPAIRAPIDemoTestCase


class AnswersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AnswersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=2, with_draft_student=True)
        self.base_url = self._build_url(self.fixtures.course.uuid, self.fixtures.assignment.uuid)
        self.lti_data = LTITestData()

    def _build_url(self, course_uuid, assignment_uuid, tail=""):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/answers' + tail
        return url

    def test_get_all_answers(self):
        # add some answers to top answers
        top_answers = self.fixtures.answers[:5]
        for answer in top_answers:
            answer.top_answer = True
        db.session.commit()

        # Test login required
        rv = self.client.get(self.base_url)
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            # test non-existent entry
            rv = self.client.get(self._build_url(self.fixtures.course.uuid, "4903409"))
            self.assert404(rv)

            # test data retrieve is correct
            self.fixtures.assignment.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
            db.session.add(self.fixtures.assignment)
            db.session.commit()
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            expected_answers = Answer.query \
                .filter_by(active=True, draft=False, assignment_id=self.fixtures.assignment.id) \
                .filter(~Answer.id.in_([a.id for a in self.fixtures.dropped_answers])) \
                .order_by(Answer.created.desc()) \
                .paginate(1, 20)
            for i, expected in enumerate(expected_answers.items):
                actual = actual_answers[i]
                self.assertEqual(expected.content, actual['content'])
                if expected.score:
                    self.assertEqual(expected.score.rank, actual['score']['rank'])
                    self.assertFalse('normalized_score' in actual['score'])
                else:
                    self.assertIsNone(actual['score'])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_answers.total, rv.json['total'])

            # test the second page
            rv = self.client.get(self.base_url + '?page=2')
            self.assert200(rv)
            actual_answers = rv.json['objects']
            expected_answers = Answer.query \
                .filter_by(active=True, draft=False, assignment_id=self.fixtures.assignment.id) \
                .filter(~Answer.id.in_([a.id for a in self.fixtures.dropped_answers])) \
                .order_by(Answer.created.desc()) \
                .paginate(2, 20)
            for i, expected in enumerate(expected_answers.items):
                actual = actual_answers[i]
                self.assertEqual(expected.content, actual['content'])
                if expected.score:
                    self.assertEqual(expected.score.rank, actual['score']['rank'])
                    self.assertFalse('normalized_score' in actual['score'])
                else:
                    self.assertIsNone(actual['score'])
            self.assertEqual(2, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_answers.total, rv.json['total'])

            # test sorting by rank (display_rank_limit 10)
            self.fixtures.assignment.rank_display_limit = 10
            db.session.commit()
            rv = self.client.get(self.base_url + '?orderBy=score')
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            expected = sorted(
                [answer for answer in self.fixtures.answers if answer.score],
                key=lambda ans: (ans.score.score, ans.created),
                reverse=True)[:10]
            self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            # test sorting by rank (display_rank_limit 20)
            self.fixtures.assignment.rank_display_limit = 20
            db.session.commit()
            rv = self.client.get(self.base_url + '?orderBy=score')
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            expected = sorted(
                [answer for answer in self.fixtures.answers if answer.score],
                key=lambda ans: (ans.score.score, ans.created),
                reverse=True)[:20]
            self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            # test sorting by rank (display_rank_limit None)
            self.fixtures.assignment.rank_display_limit = None
            db.session.commit()
            rv = self.client.get(self.base_url + '?orderBy=score')
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            expected = sorted(
                [answer for answer in self.fixtures.answers if answer.score],
                key=lambda ans: (ans.score.score, ans.created),
                reverse=True)[:20]
            self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            # test author filter
            rv = self.client.get(self.base_url + '?author={}'.format(self.fixtures.students[0].uuid))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['user_id'], self.fixtures.students[0].uuid)

            # test group filter
            rv = self.client.get(self.base_url + '?group={}'.format(self.fixtures.groups[0]))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), len(self.fixtures.answers) / len(self.fixtures.groups))

            # test ids filter
            ids = {a.uuid for a in self.fixtures.answers[:3]}
            rv = self.client.get(self.base_url + '?ids={}'.format(','.join(ids)))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(ids, {str(a['id']) for a in result})

            # test top_answer filter
            top_answer_ids = {a.uuid for a in top_answers}
            rv = self.client.get(self.base_url + '?top=true')
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(top_answer_ids, {a['id'] for a in result})

            # test combined filter
            rv = self.client.get(
                self.base_url + '?orderBy=score&group={}'.format(
                    self.fixtures.groups[0]
                )
            )
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            answers_per_group = int(len(self.fixtures.answers) / len(self.fixtures.groups)) if len(
                self.fixtures.groups) else 0
            answers = self.fixtures.answers[:answers_per_group]
            expected = sorted(answers, key=lambda ans: ans.score.score, reverse=True)
            self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])

            # all filters
            rv = self.client.get(
                self.base_url + '?orderBy=score&group={}&author={}&top=true&page=1&perPage=20'.format(
                    self.fixtures.groups[0],
                    self.fixtures.students[0].uuid
                )
            )
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['user_id'], self.fixtures.students[0].uuid)

            # add instructor answer
            answer = AnswerFactory(
                assignment=self.fixtures.assignment,
                user=self.fixtures.instructor
            )
            self.fixtures.answers.append(answer)
            db.session.commit()
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            result = rv.json['objects']
            user_uuids = [a['user_id'] for a in result]
            self.assertEqual(len(self.fixtures.answers), rv.json['total'])
            # first answer should be instructor answer
            self.assertEqual(self.fixtures.instructor.uuid, result[0]['user_id'])
            # no dropped student answers should be included
            for dropped_student in self.fixtures.dropped_students:
                self.assertNotIn(dropped_student.uuid, user_uuids)

            # test data retrieve before answer period ended with non-privileged user
            self.fixtures.assignment.answer_end = datetime.datetime.now() + datetime.timedelta(days=2)
            db.session.add(self.fixtures.assignment)
            db.session.commit()
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            self.assertEqual(1, len(actual_answers))
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

        # test data retrieve before answer period ended with privileged user
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            self.assertEqual(20, len(actual_answers))
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(self.fixtures.answers), rv.json['total'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_create_answer(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        # test login required
        expected_answer = {'content': 'this is some answer content'}
        rv = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.post(self.base_url, data=json.dumps(expected_answer),
                                        content_type='application/json')
            self.assert403(rv)
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert403(rv)

        # test invalid format
        with self.login(self.fixtures.students[0].username):
            invalid_answer = {'post': {'blah': 'blah'}}
            rv = self.client.post(
                self.base_url,
                data=json.dumps(invalid_answer),
                content_type='application/json')
            self.assert400(rv)
            # test invalid assignment
            rv = self.client.post(
                self._build_url(self.fixtures.course.uuid, "9392402"),
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert404(rv)
            # test invalid course
            rv = self.client.post(
                self._build_url("9392402", self.fixtures.assignment.uuid),
                data=json.dumps(expected_answer), content_type='application/json')
            self.assert404(rv)

        # test create successful
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            # retrieve again and verify
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # user should not have grades
            new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.fixtures.assignment, self.fixtures.instructor)
            self.assertIsNone(new_course_grade)
            self.assertIsNone(new_assignment_grade)

            # test instructor could submit multiple answers for his/her own
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # user should not have grades
            new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.fixtures.assignment, self.fixtures.instructor)
            self.assertIsNone(new_course_grade)
            self.assertIsNone(new_assignment_grade)

            # test instructor could submit multiple answers for his/her own
            expected_answer.update({'user_id': self.fixtures.instructor.uuid})
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # user should not have grades
            new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.fixtures.assignment, self.fixtures.instructor)
            self.assertIsNone(new_course_grade)
            self.assertIsNone(new_assignment_grade)

            # test instructor could submit on behave of a student
            self.fixtures.add_students(1)
            expected_answer.update({'user_id': self.fixtures.students[-1].uuid})
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # user should have grades
            new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.students[-1])
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(self.fixtures.assignment, self.fixtures.students[-1])
            self.assertIsNotNone(new_course_grade)
            self.assertIsNotNone(new_assignment_grade)

            # test instructor can not submit additional answers for a student
            expected_answer.update({'user_id': self.fixtures.students[0].uuid})
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Answer Not Saved")
            self.assertEqual(rv.json['message'], "An answer has already been submitted for this assignment by you or on your behalf.")

        self.fixtures.add_students(1)
        self.fixtures.course.calculate_grade(self.fixtures.students[-1])
        self.fixtures.assignment.calculate_grade(self.fixtures.students[-1])
        expected_answer = {'content': 'this is some answer content', 'draft': True}
        with self.login(self.fixtures.students[-1].username):
            course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.students[-1]).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.students[-1]).grade

            # test create draft successful
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)
            self.assertEqual(expected_answer['draft'], actual_answer.draft)

            # grades should not change
            new_course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.draft_student).grade
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.draft_student).grade
            self.assertEqual(new_course_grade, course_grade)
            self.assertEqual(new_assignment_grade, assignment_grade)

        with self.login(self.fixtures.instructor.username):
            # test instructor can submit outside of grace period
            self.fixtures.assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
            db.session.add(self.fixtures.assignment)
            db.session.commit()

            self.fixtures.add_students(1)
            expected_answer.update({'user_id': self.fixtures.students[-1].uuid})
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

        # test create successful
        self.fixtures.add_students(1)
        self.fixtures.course.calculate_grade(self.fixtures.students[-1])
        self.fixtures.assignment.calculate_grade(self.fixtures.students[-1])
        expected_answer = {'content': 'this is some answer content'}
        with self.login(self.fixtures.students[-1].username):
            # test student can not submit answers after answer grace period
            self.fixtures.assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
            db.session.add(self.fixtures.assignment)
            db.session.commit()

            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual("Answer Not Saved", rv.json['title'])
            self.assertEqual("The answer deadline has passed. No answers can be saved beyond the deadline unless the instructor saves it on your behalf.",
                rv.json['message'])

            # test student can submit answers within answer grace period
            self.fixtures.assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
            db.session.add(self.fixtures.assignment)
            db.session.commit()

            course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.students[-1]).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignment, self.fixtures.students[-1]).grade

            lti_consumer = self.lti_data.lti_consumer
            student = self.fixtures.students[-1]
            (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                student, self.fixtures.course, self.fixtures.assignment)

            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # grades should increase
            new_course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.students[-1])
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignment, self.fixtures.students[-1])
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

        # test create successful for system admin
        with self.login('root'):
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)

            # retrieve again and verify
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

            # test system admin could submit multiple answers for his/her own
            rv = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(rv)
            actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
            self.assertEqual(expected_answer['content'], actual_answer.content)

    def test_get_answer(self):
        assignment_uuid = self.fixtures.assignments[0].uuid
        answer = self.fixtures.answers[0]
        draft_answer = self.fixtures.draft_answers[0]

        # test login required
        rv = self.client.get(self.base_url + '/' + answer.uuid)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url + '/' + answer.uuid)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(self._build_url("999", assignment_uuid, '/' + answer.uuid))
            self.assert404(rv)

            # test invalid answer id
            rv = self.client.get(self._build_url(self.fixtures.course.uuid, assignment_uuid, '/' + "999"))
            self.assert404(rv)

            # test invalid get another user's draft answer
            rv = self.client.get(self.base_url + '/' + draft_answer.uuid)
            self.assert403(rv)

            # test authorized student
            rv = self.client.get(self.base_url + '/' + answer.uuid)
            self.assert200(rv)
            self.assertEqual(assignment_uuid, rv.json['assignment_id'])
            self.assertEqual(answer.user_uuid, rv.json['user_id'])
            self.assertEqual(answer.content, rv.json['content'])
            self.assertFalse(rv.json['draft'])

            self.assertEqual(answer.score.rank, rv.json['score']['rank'])
            self.assertFalse('normalized_score' in rv.json['score'])

        # test authorized student draft answer
        with self.login(self.fixtures.draft_student.username):
            rv = self.client.get(self.base_url + '/' + draft_answer.uuid)
            self.assert200(rv)
            self.assertEqual(assignment_uuid, rv.json['assignment_id'])
            self.assertEqual(draft_answer.user_uuid, rv.json['user_id'])
            self.assertEqual(draft_answer.content, rv.json['content'])
            self.assertTrue(rv.json['draft'])

        # test authorized teaching assistant
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(self.base_url + '/' + answer.uuid)
            self.assert200(rv)
            self.assertEqual(assignment_uuid, rv.json['assignment_id'])
            self.assertEqual(answer.user_uuid, rv.json['user_id'])
            self.assertEqual(answer.content, rv.json['content'])

            self.assertEqual(answer.score.rank, rv.json['score']['rank'])
            self.assertEqual(int(answer.score.normalized_score), rv.json['score']['normalized_score'])

        # test authorized instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self.base_url + '/' + answer.uuid)
            self.assert200(rv)
            self.assertEqual(assignment_uuid, rv.json['assignment_id'])
            self.assertEqual(answer.user_uuid, rv.json['user_id'])
            self.assertEqual(answer.content, rv.json['content'])

            self.assertEqual(answer.score.rank, rv.json['score']['rank'])
            self.assertEqual(int(answer.score.normalized_score), rv.json['score']['normalized_score'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_edit_answer(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        assignment_uuid = self.fixtures.assignments[0].uuid
        answer = self.fixtures.answers[0]
        expected = {'id': answer.uuid, 'content': 'This is an edit'}
        draft_answer = self.fixtures.draft_answers[0]
        draft_expected = {'id': draft_answer.uuid, 'content': 'This is an edit', 'draft': True}

        # test login required
        rv = self.client.post(
            self.base_url + '/' + answer.uuid,
            data=json.dumps(expected),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.students[1].username):
            rv = self.client.post(
                self.base_url + '/' + answer.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self._build_url("999", assignment_uuid, '/' + answer.uuid),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid assignment id
            rv = self.client.post(
                self._build_url(self.fixtures.course.uuid, "999", '/' + answer.uuid),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            rv = self.client.post(
                self.base_url + '/999',
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

        # test unmatched answer id
        with self.login(self.fixtures.students[1].username):
            rv = self.client.post(
                self.base_url + '/' + self.fixtures.answers[1].uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert400(rv)

        with self.login(self.fixtures.draft_student.username):
            course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.draft_student).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.draft_student).grade

            lti_consumer = self.lti_data.lti_consumer
            student = self.fixtures.draft_student
            (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                student, self.fixtures.course, self.fixtures.assignment)

            # test edit draft by author
            rv = self.client.post(
                self.base_url + '/' + draft_answer.uuid,
                data=json.dumps(draft_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(draft_answer.uuid, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])
            self.assertEqual(draft_answer.draft, rv.json['draft'])
            self.assertTrue(rv.json['draft'])

            # grades should not change
            new_course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.draft_student).grade
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.draft_student).grade
            self.assertEqual(new_course_grade, course_grade)
            self.assertEqual(new_assignment_grade, assignment_grade)

            mocked_update_assignment_grades_run.assert_not_called()
            mocked_update_course_grades_run.assert_not_called()

            # set draft to false
            draft_expected_copy = draft_expected.copy()
            draft_expected_copy['draft'] = False
            rv = self.client.post(
                self.base_url + '/' + draft_answer.uuid,
                data=json.dumps(draft_expected_copy),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(draft_answer.uuid, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])
            self.assertEqual(draft_answer.draft, rv.json['draft'])
            self.assertFalse(rv.json['draft'])

            # grades should increase
            new_course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.draft_student)
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.draft_student)
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

            # setting draft to true when false should not work
            rv = self.client.post(
                self.base_url + '/' + draft_answer.uuid,
                data=json.dumps(draft_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(draft_answer.uuid, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])
            self.assertEqual(draft_answer.draft, rv.json['draft'])
            self.assertFalse(rv.json['draft'])

        # test edit by author
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self.base_url + '/' + answer.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(answer.uuid, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])

        # test edit by user that can manage posts
        manage_expected = {
            'id': answer.uuid,
            'content': 'This is another edit'
        }
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                self.base_url + '/' + answer.uuid,
                data=json.dumps(manage_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(answer.uuid, rv.json['id'])
            self.assertEqual('This is another edit', rv.json['content'])

        # test edit by author
        with self.login(self.fixtures.students[0].username):
            # test student can not submit answers after answer grace period
            self.fixtures.assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
            db.session.add(self.fixtures.assignment)
            db.session.commit()

            rv = self.client.post(
                self.base_url + '/' + answer.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)
            self.assertEqual("Answer Not Updated", rv.json['title'])
            self.assertEqual("The answer deadline has passed. No answers can be updated beyond the deadline unless the instructor updates it on your behalf.",
                rv.json['message'])

            # test student can submit answers within answer grace period
            self.fixtures.assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
            db.session.add(self.fixtures.assignment)
            db.session.commit()

            rv = self.client.post(
                self.base_url + '/' + answer.uuid,
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(answer.uuid, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_delete_answer(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        answer_uuid = self.fixtures.answers[0].uuid

        # test login required
        rv = self.client.delete(self.base_url + '/' + answer_uuid)
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.students[1].username):
            rv = self.client.delete(self.base_url + '/' + answer_uuid)
            self.assert403(rv)

        # test invalid answer id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.delete(self.base_url + '/999')
            self.assert404(rv)

            lti_consumer = self.lti_data.lti_consumer
            student = self.fixtures.students[0]
            (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                student, self.fixtures.course, self.fixtures.assignment)

            course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.students[0]).grade
            assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.students[0]).grade

            # test deletion by author
            rv = self.client.delete(self.base_url + '/' + answer_uuid)
            self.assert200(rv)
            self.assertEqual(answer_uuid, rv.json['id'])

            # grades should decrease
            new_course_grade = CourseGrade.get_user_course_grade(
                self.fixtures.course, self.fixtures.students[0])
            new_assignment_grade = AssignmentGrade.get_user_assignment_grade(
                self.fixtures.assignments[0], self.fixtures.students[0])
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

        # test deletion by user that can manage posts
        with self.login(self.fixtures.instructor.username):
            answer_uuid2 = self.fixtures.answers[1].uuid
            rv = self.client.delete(self.base_url + '/' + answer_uuid2)
            self.assert200(rv)
            self.assertEqual(answer_uuid2, rv.json['id'])

    def test_get_user_answers(self):
        assignment = self.fixtures.assignments[0]
        answer = self.fixtures.answers[0]
        draft_answer = self.fixtures.draft_answers[0]
        url = self._build_url(self.fixtures.course.uuid, assignment.uuid, '/user')

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        with self.login(self.fixtures.students[0].username):
            # test invalid course
            rv = self.client.get(self._build_url("999", assignment.uuid, '/user'))
            self.assert404(rv)

            # test invalid assignment
            rv = self.client.get(self._build_url(self.fixtures.course.uuid, "999", '/user'))
            self.assert404(rv)

            # test successful query
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(answer.uuid, rv.json['objects'][0]['id'])
            self.assertEqual(answer.content, rv.json['objects'][0]['content'])
            self.assertEqual(answer.draft, rv.json['objects'][0]['draft'])

            # test draft query
            rv = self.client.get(url, query_string={'draft': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test unsaved query
            rv = self.client.get(url, query_string={'unsaved': True})
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(answer.uuid, rv.json['objects'][0]['id'])
            self.assertEqual(answer.content, rv.json['objects'][0]['content'])
            self.assertEqual(answer.draft, rv.json['objects'][0]['draft'])

            answer.content = answer.content+"123"
            db.session.commit()

            rv = self.client.get(url, query_string={'unsaved': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))


        with self.login(self.fixtures.draft_student.username):
             # test successful query
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test draft query
            rv = self.client.get(url, query_string={'draft': True})
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(draft_answer.uuid, rv.json['objects'][0]['id'])
            self.assertEqual(draft_answer.content, rv.json['objects'][0]['content'])
            self.assertEqual(draft_answer.draft, rv.json['objects'][0]['draft'])

            # test unsaved query
            rv = self.client.get(url, query_string={'unsaved': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test draft + unsaved query
            rv = self.client.get(url, query_string={'draft': True, 'unsaved': True})
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['objects']))
            self.assertEqual(draft_answer.uuid, rv.json['objects'][0]['id'])
            self.assertEqual(draft_answer.content, rv.json['objects'][0]['content'])
            self.assertEqual(draft_answer.draft, rv.json['objects'][0]['draft'])

            draft_answer.content = draft_answer.content+"123"
            db.session.commit()

            rv = self.client.get(url, query_string={'draft': True, 'unsaved': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test draft query
            rv = self.client.get(url, query_string={'draft': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

            # test unsaved query
            rv = self.client.get(url, query_string={'unsaved': True})
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['objects']))

    def test_flag_answer(self):
        answer = self.fixtures.answers[0]
        flag_url = self.base_url + "/" + answer.uuid + "/flagged"
        # test login required
        expected_flag_on = {'flagged': True}
        expected_flag_off = {'flagged': False}
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_on),
                content_type='application/json')
            self.assert403(rv)

        # test flagging
        with self.login(self.fixtures.students[0].username):
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
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_on),
                content_type='application/json')
            self.assert200(rv)

        # create another student
        self.fixtures.add_students(1)
        other_student = self.fixtures.students[-1]
        # try to unflag answer as other student, should fail
        with self.login(other_student.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_off),
                content_type='application/json')
            self.assert400(rv)

        # test allow unflagging by instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_off),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                expected_flag_off['flagged'],
                rv.json['flagged'],
                "Expected answer to be flagged.")

    def test_top_answer(self):
        answer = self.fixtures.answers[0]
        top_answer_url = self.base_url + "/" + answer.uuid + "/top"
        expected_top_on = {'top_answer': True}
        expected_top_off = {'top_answer': False}

        # test login required
        rv = self.client.post(
            top_answer_url,
            data=json.dumps(expected_top_on),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_on),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_on),
                content_type='application/json')
            self.assert403(rv)

        # test allow setting top_answer by instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_on),
                content_type='application/json')
            self.assert200(rv)
            self.assertTrue(rv.json['top_answer'])

            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_off),
                content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['top_answer'])

        # test allow setting top_answer by teaching assistant
        with self.login(self.fixtures.ta.username):
            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_on),
                content_type='application/json')
            self.assert200(rv)
            self.assertTrue(rv.json['top_answer'])

            rv = self.client.post(
                top_answer_url,
                data=json.dumps(expected_top_off),
                content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['top_answer'])

class AnswerDemoAPITests(ComPAIRAPIDemoTestCase):
    def setUp(self):
        super(AnswerDemoAPITests, self).setUp()

    def test_delete_demo_answer(self):
        answers = Answer.query.all()

        for answer in answers:
            url = '/api/courses/' + answer.course_uuid + '/assignments/' + answer.assignment_uuid + '/answers/' + answer.uuid

            with self.login('root'):
                # test deletion fails
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.delete(url)
                self.assert400(rv)

                # test deletion success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.delete(url)
                self.assert200(rv)

    def test_edit_demo_answer(self):
        answers = Answer.query.all()

        for answer in answers:
            url = '/api/courses/' + answer.course_uuid + '/assignments/' + answer.assignment_uuid + '/answers/' + answer.uuid

            expected = {
                'id': answer.uuid,
                'content': 'This is an edit'
            }

            with self.login('root'):
                # test deletion fails
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert400(rv)


                # test deletion success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert200(rv)