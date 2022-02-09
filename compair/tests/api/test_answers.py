# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
import mock

from compair import db
from data.fixtures import AnswerFactory, DefaultFixture
from data.fixtures.test_data import TestFixture, LTITestData
from compair.models import Answer, CourseGrade, AssignmentGrade, \
    CourseRole, SystemRole, User
from compair.tests.test_compair import ComPAIRAPITestCase, ComPAIRAPIDemoTestCase


class AnswersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(AnswersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=5,
            num_group_assignments=1, with_draft_student=True, num_non_comparable_ans=2)

        self.assignment = self.fixtures.assignment
        self.group_assignment = self.fixtures.assignments[1]

        self.base_url = self._build_url(self.fixtures.course.uuid, self.assignment.uuid)
        self.lti_data = LTITestData()

    def _build_url(self, course_uuid, assignment_uuid, tail=""):
        url = '/api/courses/' + course_uuid + '/assignments/' + assignment_uuid + '/answers' + tail
        return url

    def test_get_all_answers(self):
        # add some answers to top answers
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)
            answers = [answer for answer in self.fixtures.answers if answer.assignment_id == assignment.id]

            top_answers = answers[:5]
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

            student = self.fixtures.students[0]
            for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
                with user_context:
                    # test non-existent entry
                    rv = self.client.get(self._build_url(self.fixtures.course.uuid, "4903409"))
                    self.assert404(rv)

                    # test data retrieve is correct
                    assignment.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
                    db.session.commit()
                    rv = self.client.get(self.base_url)
                    self.assert200(rv)
                    actual_answers = rv.json['objects']
                    expected_answers = sorted([answer for answer in answers], key=lambda ans: ans.submission_date, reverse=True)
                    expected_answers = sorted(expected_answers, key=lambda ans: ans.comparable)[:20]
                    for i, expected in enumerate(expected_answers):
                        actual = actual_answers[i]
                        self.assertEqual(expected.content, actual['content'])
                        # students should NOT see rank/score when not retrieving answers ordered by score
                        self.assertFalse('score' in actual)
                    self.assertEqual(1, rv.json['page'])
                    self.assertEqual(20, rv.json['per_page'])
                    self.assertEqual(len(answers), rv.json['total'])
                    if not assignment.enable_group_answers:
                        self.assertEqual(2, rv.json['pages'])
                    else:
                        self.assertEqual(1, rv.json['pages'])

                    # test the second page
                    if not assignment.enable_group_answers:
                        rv = self.client.get(self.base_url + '?page=2')
                        self.assert200(rv)
                        actual_answers = rv.json['objects']
                        expected_answers = sorted([answer for answer in answers], key=lambda ans: ans.submission_date, reverse=True)
                        expected_answers = sorted(expected_answers, key=lambda ans: ans.comparable)[20:]
                        for i, expected in enumerate(expected_answers):
                            actual = actual_answers[i]
                            self.assertEqual(expected.content, actual['content'])
                            # students should NOT see rank/score when not retrieving answers ordered by score
                            self.assertFalse('score' in actual)
                        self.assertEqual(2, rv.json['page'])
                        self.assertEqual(2, rv.json['pages'])
                        self.assertEqual(20, rv.json['per_page'])
                        self.assertEqual(len(answers), rv.json['total'])

                    # test sorting by rank (display_rank_limit 10)
                    assignment.rank_display_limit = 10
                    db.session.commit()
                    rv = self.client.get(self.base_url + '?orderBy=score')
                    self.assert200(rv)
                    result = rv.json['objects']
                    # test the result is paged and sorted
                    expected = sorted(
                        [answer for answer in answers if answer.score],
                        key=lambda ans: (ans.score.score, ans.submission_date),
                        reverse=True)[:10]
                    self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])
                    for ans in result:
                        self.assertTrue('score' in ans)
                        self.assertFalse('normalized_score' in ans['score'])
                        self.assertTrue('rank' in ans['score'])
                    self.assertEqual(1, rv.json['page'])
                    self.assertEqual(1, rv.json['pages'])
                    self.assertEqual(20, rv.json['per_page'])
                    self.assertEqual(len(expected), rv.json['total'])

                    # test sorting by rank (display_rank_limit 20)
                    assignment.rank_display_limit = 20
                    db.session.commit()
                    rv = self.client.get(self.base_url + '?orderBy=score')
                    self.assert200(rv)
                    result = rv.json['objects']
                    # test the result is paged and sorted
                    expected = sorted(
                        [answer for answer in answers if answer.score],
                        key=lambda ans: (ans.score.score, ans.submission_date),
                        reverse=True)[:20]
                    self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])
                    for ans in result:
                        self.assertTrue('score' in ans)
                        self.assertFalse('normalized_score' in ans['score'])
                        self.assertTrue('rank' in ans['score'])
                    self.assertEqual(1, rv.json['page'])
                    self.assertEqual(1, rv.json['pages'])
                    self.assertEqual(20, rv.json['per_page'])
                    self.assertEqual(len(expected), rv.json['total'])

                    # test sorting by rank (display_rank_limit None).
                    # expect to see errors if the course has no display rank limit set
                    assignment.rank_display_limit = None
                    db.session.commit()
                    rv = self.client.get(self.base_url + '?orderBy=score')
                    self.assert400(rv)

                    assignment.rank_display_limit = 20
                    db.session.commit()

                    # test author filter
                    rv = self.client.get(self.base_url + '?author={}'.format(self.fixtures.students[0].uuid))
                    self.assert200(rv)
                    result = rv.json['objects']
                    self.assertEqual(len(result), 1)
                    if not assignment.enable_group_answers:
                        self.assertEqual(result[0]['user_id'], self.fixtures.students[0].uuid)
                    else:
                        group = self.fixtures.students[0].get_course_group(self.fixtures.course.id)
                        self.assertEqual(result[0]['group_id'], group.uuid)

                    # test group filter
                    rv = self.client.get(self.base_url + '?group={}'.format(self.fixtures.groups[0].uuid))
                    self.assert200(rv)
                    result = rv.json['objects']
                    expected_answers = self.fixtures.get_assignment_answers_for_group(
                        assignment, self.fixtures.groups[0])
                    self.assertEqual(len(result), len(expected_answers))

                    # test ids filter
                    ids = {a.uuid for a in answers[:3]}
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
                            self.fixtures.groups[0].uuid
                        )
                    )
                    self.assert200(rv)
                    result = rv.json['objects']
                    # test the result is paged and sorted
                    expected_answers = self.fixtures.get_assignment_answers_for_group(assignment, self.fixtures.groups[0])
                    expected = sorted([ ans for ans in expected_answers if ans.comparable and ans.score ], key=lambda ans: ans.score.score, reverse=True)
                    self.assertEqual([a.uuid for a in expected], [a['id'] for a in result])

                    # all filters
                    rv = self.client.get(
                        self.base_url + '?orderBy=score&group={}&author={}&top=true&page=1&perPage=20'.format(
                            self.fixtures.groups[0].uuid,
                            self.fixtures.students[0].uuid
                        )
                    )
                    self.assert200(rv)
                    result = rv.json['objects']
                    self.assertEqual(len(result), 1)
                    if not assignment.enable_group_answers:
                        self.assertEqual(result[0]['user_id'], self.fixtures.students[0].uuid)
                    else:
                        group = self.fixtures.students[0].get_course_group(self.fixtures.course.id)
                        self.assertEqual(result[0]['group_id'], group.uuid)

                    # test data retrieve before answer period ended with non-privileged user
                    assignment.answer_end = datetime.datetime.now() + datetime.timedelta(days=2)
                    db.session.add(assignment)
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
                # add instructor answer
                answer = AnswerFactory(
                    assignment=assignment,
                    user=self.fixtures.instructor
                )
                self.fixtures.answers.append(answer)
                db.session.commit()
                answers = [answer for answer in self.fixtures.answers if answer.assignment_id == assignment.id]

                rv = self.client.get(self.base_url)
                self.assert200(rv)
                result = rv.json['objects']
                user_uuids = [a['user_id'] for a in result]
                self.assertEqual(len(answers), rv.json['total'])
                # first answer should be instructor answer
                self.assertEqual(self.fixtures.instructor.uuid, result[0]['user_id'])
                # no dropped student answers should be included
                for dropped_student in self.fixtures.dropped_students:
                    self.assertNotIn(dropped_student.uuid, user_uuids)

                rv = self.client.get(self.base_url)
                self.assert200(rv)
                actual_answers = rv.json['objects']
                self.assertEqual(1, rv.json['page'])
                self.assertEqual(20, rv.json['per_page'])
                self.assertEqual(len(answers), rv.json['total'])
                if not assignment.enable_group_answers:
                    self.assertEqual(20, len(actual_answers))
                    self.assertEqual(2, rv.json['pages'])
                else:
                    self.assertEqual(len(answers), len(actual_answers))
                    self.assertEqual(1, rv.json['pages'])

                # test sorting by score
                # for instructors, all comparable answers should be included, regardless whether they are compared or not
                rv = self.client.get(self.base_url + '?orderBy=score')
                self.assert200(rv)
                result = rv.json['objects']
                # test the result is paged and sorted
                expected = sorted(
                    [answer for answer in answers if answer.comparable],
                    key=lambda ans: (ans.score.score if ans.score else float('-inf'), ans.submission_date),
                    reverse=True)
                self.assertEqual([a.uuid for a in expected[:20]], [a['id'] for a in result])
                self.assertEqual(1, rv.json['page'])
                self.assertEqual(20, rv.json['per_page'])
                self.assertEqual(len(expected), rv.json['total'])
                if not assignment.enable_group_answers:
                    self.assertEqual(2, rv.json['pages'])
                else:
                    self.assertEqual(1, rv.json['pages'])

                if not assignment.enable_group_answers:
                    # get the second page
                    rv = self.client.get(self.base_url, query_string={'orderBy': 'score', 'page': 2})
                    self.assert200(rv)
                    result = rv.json['objects']
                    expected = sorted(
                        [answer for answer in answers if answer.comparable],
                        key=lambda ans: (ans.score.score if ans.score else float('-inf'), ans.submission_date),
                        reverse=True)
                    self.assertEqual([a.uuid for a in expected[20:]], [a['id'] for a in result])
                    self.assertEqual(2, rv.json['page'])
                    self.assertEqual(2, rv.json['pages'])
                    self.assertEqual(20, rv.json['per_page'])
                    self.assertEqual(len(expected), rv.json['total'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_create_answer(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            # test login required
            expected_answer = {'content': 'this is some answer content'}
            rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
            self.assert401(rv)

            # test unauthorized users
            with self.login(self.fixtures.unauthorized_student.username):
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert403(rv)

            with self.login(self.fixtures.unauthorized_instructor.username):
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert403(rv)

            # test invalid format
            with self.login(self.fixtures.students[0].username):
                invalid_answer = {'post': {'blah': 'blah'}}
                rv = self.client.post(self.base_url, data=json.dumps(invalid_answer), content_type='application/json')
                self.assert400(rv)

                # test invalid assignment
                rv = self.client.post(
                    self._build_url(self.fixtures.course.uuid, "9392402"),
                    data=json.dumps(expected_answer), content_type='application/json')
                self.assert404(rv)

                # test invalid course
                rv = self.client.post(
                    self._build_url("9392402", assignment.uuid),
                    data=json.dumps(expected_answer), content_type='application/json')
                self.assert404(rv)

            # check that students can only submit answers when they are enrolled in a group for group assignments
            if assignment == self.group_assignment.id:
                self.fixtures.add_students(1)
                with self.login(self.fixtures.students[-1].username):
                    rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("You are currently not in any group for this course. Please contact your instructor to be added to a group.", rv.json['message'])

                    # add student to group
                    self.fixtures.add_group(self.fixtures.course)
                    self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])
                    rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                    self.assert200(rv)

            # student answers can only be comparable
            for comparable in [True, False, None]:
                self.fixtures.add_students(1)
                self.fixtures.add_group(self.fixtures.course)
                self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])
                with self.login(self.fixtures.students[-1].username):
                    comp_ans = expected_answer.copy()
                    if comparable is not None:
                        comp_ans['comparable'] = comparable
                    rv = self.client.post(self.base_url, data=json.dumps(comp_ans), content_type='application/json')
                    self.assert200(rv)
                    # retrieve again and verify
                    actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                    self.assertEqual(comp_ans['content'], actual_answer.content)
                    self.assertIsNotNone(actual_answer.submission_date)
                    self.assertTrue(actual_answer.comparable)

            with self.login(self.fixtures.instructor.username):
                # test create successful
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)

                # retrieve again and verify
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)

                # test comparable instructor answers
                for comparable in [True, False]:
                    comp_ans = expected_answer.copy()
                    comp_ans['comparable'] = comparable
                    rv = self.client.post(self.base_url, data=json.dumps(comp_ans), content_type='application/json')
                    self.assert200(rv)
                    # retrieve again and verify
                    actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                    self.assertEqual(comp_ans['content'], actual_answer.content)
                    self.assertEqual(comparable, actual_answer.comparable)

                # user should not have grades
                new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.instructor)
                self.assertIsNone(new_course_grade)
                self.assertIsNone(new_assignment_grade)

                # test instructor could submit multiple answers for his/her own
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)

                # user should not have grades
                new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.instructor)
                self.assertIsNone(new_course_grade)
                self.assertIsNone(new_assignment_grade)

                # test instructor could submit multiple answers for his/her own
                instructor_ans = expected_answer.copy()
                instructor_ans['user_id'] = self.fixtures.instructor.uuid

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(instructor_ans['content'], actual_answer.content)

                # user should not have grades
                new_course_grade = CourseGrade.get_user_course_grade( self.fixtures.course, self.fixtures.instructor)
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.instructor)
                self.assertIsNone(new_course_grade)
                self.assertIsNone(new_assignment_grade)

                # test instructor could submit on behalf of a student
                self.fixtures.add_students(1)
                self.fixtures.add_group(self.fixtures.course)
                self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])
                instructor_ans = expected_answer.copy()
                if not assignment.enable_group_answers:
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid
                else:
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(instructor_ans['content'], actual_answer.content)

                # user should have grades
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, self.fixtures.students[-1])
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.students[-1])
                self.assertIsNotNone(new_course_grade)
                self.assertIsNotNone(new_assignment_grade)

                # test instructor can not submit additional answers for a student
                instructor_ans = expected_answer.copy()
                if not assignment.enable_group_answers:
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid
                else:
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert400(rv)
                self.assertEqual(rv.json['title'], "Answer Not Submitted")
                self.assertEqual(rv.json['message'], "An answer has already been submitted for this assignment by you or on your behalf.")

                # test instructor could submit on behalf of a student who has a draft answer
                self.fixtures.add_students(1)
                self.fixtures.add_group(self.fixtures.course)
                self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])

                instructor_ans = expected_answer.copy()
                if not assignment.enable_group_answers:
                    self.fixtures.add_answer(assignment, self.fixtures.students[-1], draft=True)
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid
                else:
                    self.fixtures.add_group_answer(assignment, self.fixtures.groups[-1], draft=True)
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid
                draft_answer = self.fixtures.answers[-1]

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(instructor_ans['content'], actual_answer.content)
                self.assertFalse(draft_answer.active)

            self.fixtures.add_students(1)
            self.fixtures.add_group(self.fixtures.course)
            self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])
            self.fixtures.course.calculate_grade(self.fixtures.students[-1])
            assignment.calculate_grade(self.fixtures.students[-1])
            expected_answer = {'content': 'this is some answer content', 'draft': True}
            with self.login(self.fixtures.students[-1].username):
                course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, self.fixtures.students[-1]).grade
                assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.students[-1]).grade

                # test create draft successful
                rv = self.client.post( self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)
                self.assertEqual(expected_answer['draft'], actual_answer.draft)
                self.assertIsNone(actual_answer.submission_date)

                # grades should not change
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, self.fixtures.students[-1]).grade
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.students[-1]).grade
                self.assertEqual(new_course_grade, course_grade)
                self.assertEqual(new_assignment_grade, assignment_grade)

            with self.login(self.fixtures.instructor.username):
                # test instructor can submit outside of grace period
                assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
                db.session.add(assignment)
                db.session.commit()

                instructor_ans = expected_answer.copy()
                if not assignment.enable_group_answers:
                    self.fixtures.add_students(1)
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid
                else:
                    self.fixtures.add_group(self.fixtures.course)
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(instructor_ans['content'], actual_answer.content)

                if not assignment.enable_group_answers:
                    self.assertEqual(actual_answer.user_id, self.fixtures.students[-1].id)
                    self.assertIsNone(actual_answer.group_id)
                else:
                    self.assertEqual(actual_answer.group_id, self.fixtures.groups[-1].id)
                    self.assertIsNone(actual_answer.user_id)

                # test instructor cannot submit on behalf of a student or group when the assignment doesn't allow it
                instructor_ans = expected_answer.copy()
                if not assignment.enable_group_answers:
                    self.fixtures.add_group(self.fixtures.course)
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid
                else:
                    self.fixtures.add_students(1)
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid

                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert400(rv)
                if not assignment.enable_group_answers:
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("Group answers are not allowed for this assignment.", rv.json['message'])
                else:
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("Students can only submit group answers for this assignment.", rv.json['message'])

                # test cannot set user_id to none existing user
                instructor_ans = expected_answer.copy()
                instructor_ans['user_id'] = '999'
                rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                self.assert404(rv)

                if assignment.enable_group_answers:
                    # test cannot set group_id to none existing group
                    instructor_ans = expected_answer.copy()
                    instructor_ans['group_id'] = '999'
                    rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                    self.assert404(rv)

                    # test cannot set both user_id and group_id
                    instructor_ans = expected_answer.copy()
                    self.fixtures.add_students(1)
                    instructor_ans['user_id'] = self.fixtures.students[-1].uuid
                    self.fixtures.add_group(self.fixtures.course)
                    instructor_ans['group_id'] = self.fixtures.groups[-1].uuid
                    rv = self.client.post(self.base_url, data=json.dumps(instructor_ans), content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("You cannot submit an answer for a user and a group at the same time.", rv.json['message'])

            # test create successful
            self.fixtures.add_students(1)
            self.fixtures.course.calculate_grade(self.fixtures.students[-1])
            assignment.calculate_grade(self.fixtures.students[-1])
            expected_answer = {'content': 'this is some answer content'}
            with self.login(self.fixtures.students[-1].username):
                # test student can not submit answers after answer grace period
                assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
                db.session.add(assignment)
                db.session.commit()

                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert403(rv)
                self.assertEqual("Answer Not Submitted", rv.json['title'])
                self.assertEqual("Sorry, the answer deadline has passed. No answers can be submitted after the deadline unless the instructor submits the answer for you.",
                    rv.json['message'])

                # test student can submit answers within answer grace period
                assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
                db.session.add(assignment)
                db.session.commit()

                course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, self.fixtures.students[-1]).grade
                assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.students[-1]).grade

                lti_consumer = self.lti_data.lti_consumer
                student = self.fixtures.students[-1]
                (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
                    student, self.fixtures.course, assignment)

                if assignment.enable_group_answers:
                    # test student cannot submit answer if not in a group
                    rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("You are currently not in any group for this course. Please contact your instructor to be added to a group.",
                        rv.json['message'])

                self.fixtures.add_group(self.fixtures.course)
                self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])

                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)

                # grades should increase
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, self.fixtures.students[-1])
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, self.fixtures.students[-1])
                self.assertGreater(new_course_grade.grade, course_grade)
                self.assertGreater(new_assignment_grade.grade, assignment_grade)

                mocked_update_assignment_grades_run.assert_called_once_with(
                    lti_consumer.id,
                    [[lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id]]
                )
                mocked_update_assignment_grades_run.reset_mock()

                mocked_update_course_grades_run.assert_called_once_with(
                    lti_consumer.id,
                    [[lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id]]
                )
                mocked_update_course_grades_run.reset_mock()

            # test create successful for system admin
            with self.login('root'):
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)

                # retrieve again and verify
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)

                # test system admin could submit multiple answers for his/her own
                rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                self.assert200(rv)
                actual_answer = Answer.query.filter_by(uuid=rv.json['id']).one()
                self.assertEqual(expected_answer['content'], actual_answer.content)

            # can't create during impersonation
            student = self.fixtures.students[-1]
            instructor = self.fixtures.instructor
            for impersonator in [DefaultFixture.ROOT_USER, instructor]:
                with self.impersonate(impersonator, student):
                    rv = self.client.post(self.base_url, data=json.dumps(expected_answer), content_type='application/json')
                    self.assert403(rv)
                    self.assertTrue(rv.json['disabled_by_impersonation'])

    def test_get_answer(self):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)
            assignment_uuid = assignment.uuid

            student = self.fixtures.students[0]
            draft_student = self.fixtures.draft_student

            if not assignment.enable_group_answers:
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.user_id == student.id][0]
                draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id and a.user_id == draft_student.id][0]
            else:
                group = student.get_course_group(self.fixtures.course.id)
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.group_id == group.id][0]
                draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id and a.group_id == self.fixtures.draft_group.id][0]

            # test login required
            rv = self.client.get(self.base_url + '/' + answer.uuid)
            self.assert401(rv)

            # test unauthorized user
            with self.login(self.fixtures.unauthorized_instructor.username):
                rv = self.client.get(self.base_url + '/' + answer.uuid)
                self.assert403(rv)

            for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
                with user_context:
                    # test invalid course id
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

                    # students should not see score/rank when retrieving answer by id
                    self.assertFalse('score' in rv.json)

            # test authorized student draft answer
            for user_context in [self.login(draft_student.username), self.impersonate(self.fixtures.instructor, draft_student)]:
                with user_context:
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
        student = self.fixtures.students[0]
        draft_student = self.fixtures.draft_student

        lti_consumer = self.lti_data.lti_consumer
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            draft_student, self.fixtures.course, self.assignment)
        (lti_user_resource_link3, lti_user_resource_link4) = self.lti_data.setup_student_user_resource_links(
            draft_student, self.fixtures.course, self.group_assignment)

        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            if not assignment.enable_group_answers:
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.user_id == student.id][0]
                draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id and a.user_id == draft_student.id][0]
            else:
                group = student.get_course_group(self.fixtures.course.id)
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.group_id == group.id][0]
                draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id and a.group_id == self.fixtures.draft_group.id][0]

            expected = {'id': answer.uuid, 'content': 'This is an edit'}
            draft_expected = {'id': draft_answer.uuid, 'content': 'This is an edit', 'draft': True}

            # test login required
            rv = self.client.post(self.base_url + '/' + answer.uuid, data=json.dumps(expected), content_type='application/json')
            self.assert401(rv)

            # test unauthorized user
            with self.login(self.fixtures.students[-1].username):
                rv = self.client.post(self.base_url + '/' + answer.uuid, data=json.dumps(expected), content_type='application/json')
                self.assert403(rv)

            # test invalid course id
            with self.login(student.username):
                rv = self.client.post(self._build_url("999", assignment.uuid, '/' + answer.uuid),
                    data=json.dumps(expected), content_type='application/json')
                self.assert404(rv)

                # test invalid assignment id
                rv = self.client.post(self._build_url(self.fixtures.course.uuid, "999", '/' + answer.uuid),
                    data=json.dumps(expected), content_type='application/json')
                self.assert404(rv)

                # test invalid answer id
                rv = self.client.post(self.base_url + '/999',
                    data=json.dumps(expected), content_type='application/json')
                self.assert404(rv)

            # test unmatched answer id
            self.fixtures.add_students(1)
            self.fixtures.add_group(self.fixtures.course)
            self.fixtures.change_user_group(self.fixtures.course, self.fixtures.students[-1], self.fixtures.groups[-1])
            if not assignment.enable_group_answers:
                self.fixtures.add_answer(assignment, self.fixtures.students[-1])
            else:
                self.fixtures.add_group_answer(assignment, self.fixtures.groups[-1])

            with self.login(self.fixtures.instructor.username):
                rv = self.client.post(self.base_url + '/' + self.fixtures.answers[-1].uuid,
                    data=json.dumps(expected), content_type='application/json')
                self.assert400(rv)

            with self.login(draft_student.username):
                course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, draft_student).grade
                assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, draft_student).grade

                # test edit draft by author
                rv = self.client.post(self.base_url + '/' + draft_answer.uuid,
                    data=json.dumps(draft_expected), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(draft_answer.uuid, rv.json['id'])
                self.assertEqual('This is an edit', rv.json['content'])
                self.assertEqual(draft_answer.draft, rv.json['draft'])
                self.assertIsNone(rv.json['submission_date'])
                self.assertTrue(rv.json['draft'])

                # grades should not change
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, draft_student).grade
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, draft_student).grade
                self.assertEqual(new_course_grade, course_grade)
                self.assertEqual(new_assignment_grade, assignment_grade)

                mocked_update_assignment_grades_run.assert_not_called()
                mocked_update_course_grades_run.assert_not_called()

                # set draft to false
                draft_expected_copy = draft_expected.copy()
                draft_expected_copy['draft'] = False
                rv = self.client.post(self.base_url + '/' + draft_answer.uuid,
                    data=json.dumps(draft_expected_copy), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(draft_answer.uuid, rv.json['id'])
                self.assertEqual('This is an edit', rv.json['content'])
                self.assertEqual(draft_answer.draft, rv.json['draft'])
                self.assertIsNotNone(rv.json['submission_date'])
                self.assertFalse(rv.json['draft'])

                current_submission_date = rv.json['submission_date']

                # grades should increase
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, draft_student)
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, draft_student)
                self.assertGreater(new_course_grade.grade, course_grade)
                self.assertGreater(new_assignment_grade.grade, assignment_grade)

                if not assignment.enable_group_answers:
                    mocked_update_assignment_grades_run.assert_called_once_with(
                        lti_consumer.id,
                        [[lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id]]
                    )
                else:
                    mocked_update_assignment_grades_run.assert_called_once_with(
                        lti_consumer.id,
                        [[lti_user_resource_link4.lis_result_sourcedid, new_assignment_grade.id]]
                    )
                mocked_update_assignment_grades_run.reset_mock()

                self.assertEqual(mocked_update_course_grades_run.call_count, 2)
                mocked_update_course_grades_run.assert_any_call(
                    lti_consumer.id,
                    [[lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id]]
                )
                mocked_update_course_grades_run.assert_any_call(
                    lti_consumer.id,
                    [[lti_user_resource_link3.lis_result_sourcedid, new_course_grade.id]]
                )
                mocked_update_course_grades_run.reset_mock()

                # setting draft to true when false should not work
                rv = self.client.post(self.base_url + '/' + draft_answer.uuid,
                    data=json.dumps(draft_expected), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(draft_answer.uuid, rv.json['id'])
                self.assertEqual('This is an edit', rv.json['content'])
                self.assertEqual(draft_answer.draft, rv.json['draft'])
                self.assertIsNotNone(rv.json['submission_date'])
                self.assertEqual(current_submission_date, rv.json['submission_date'])
                self.assertFalse(rv.json['draft'])

                mocked_update_assignment_grades_run.reset_mock()
                mocked_update_course_grades_run.reset_mock()

            # test edit by author
            with self.login(student.username):
                previous_submission_date = answer.submission_date
                rv = self.client.post(self.base_url + '/' + answer.uuid,
                    data=json.dumps(expected), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(answer.uuid, rv.json['id'])
                self.assertEqual('This is an edit', rv.json['content'])
                self.assertEqual(previous_submission_date, answer.submission_date)

            # test edit by user that can manage posts
            with self.login(self.fixtures.instructor.username):
                manage_expected = {
                    'id': answer.uuid,
                    'content': 'This is another edit'
                }
                rv = self.client.post(self.base_url + '/' + answer.uuid,
                    data=json.dumps(manage_expected), content_type='application/json')
                self.assert200(rv)
                self.assertEqual(answer.uuid, rv.json['id'])
                self.assertEqual('This is another edit', rv.json['content'])

                # test instructor could submit on behalf of a student or group
                self.fixtures.add_answer(assignment, self.fixtures.instructor, draft=True)
                instructor_answer = self.fixtures.answers[-1]
                if not assignment.enable_group_answers:
                    self.fixtures.add_students(1)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'user_id': self.fixtures.students[-1].uuid,
                        'content': 'This is another edit'
                    }
                else:
                    self.fixtures.add_group(self.fixtures.course)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'group_id': self.fixtures.groups[-1].uuid,
                        'content': 'This is another edit'
                    }
                rv = self.client.post(
                    self.base_url + '/' + instructor_answer.uuid,
                    data=json.dumps(manage_expected),
                    content_type='application/json')
                self.assert200(rv)
                self.assertEqual(instructor_answer.uuid, rv.json['id'])
                self.assertEqual('This is another edit', rv.json['content'])
                if not assignment.enable_group_answers:
                    self.assertEqual(instructor_answer.user_uuid, rv.json['user_id'])
                    self.assertEqual(instructor_answer.user_id, self.fixtures.students[-1].id)
                else:
                    self.assertEqual(instructor_answer.group_uuid, rv.json['group_id'])
                    self.assertEqual(instructor_answer.group_id, self.fixtures.groups[-1].id)

                # test instructor cannot submit on behalf of a student or group when the assignment doesn't allow it
                self.fixtures.add_answer(assignment, self.fixtures.instructor, draft=True)
                instructor_answer = self.fixtures.answers[-1]
                if not assignment.enable_group_answers:
                    self.fixtures.add_group(self.fixtures.course)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'group_id': self.fixtures.groups[-1].uuid,
                        'content': 'This is another edit'
                    }
                else:
                    self.fixtures.add_students(1)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'user_id': self.fixtures.students[-1].uuid,
                        'content': 'This is another edit'
                    }
                rv = self.client.post(
                    self.base_url + '/' + instructor_answer.uuid,
                    data=json.dumps(manage_expected),
                    content_type='application/json')
                self.assert400(rv)
                if not assignment.enable_group_answers:
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("Group answers are not allowed for this assignment.", rv.json['message'])
                else:
                    self.assertEqual("Answer Not Submitted", rv.json['title'])
                    self.assertEqual("Students can only submit group answers for this assignment.", rv.json['message'])

                # test instructor could submit on behalf of a student who has a draft answer
                self.fixtures.add_answer(assignment, self.fixtures.instructor, draft=True)
                instructor_answer = self.fixtures.answers[-1]
                if not assignment.enable_group_answers:
                    self.fixtures.add_students(1)
                    self.fixtures.add_answer(assignment, self.fixtures.students[-1], draft=True)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'user_id': self.fixtures.students[-1].uuid,
                        'content': 'This is another edit'
                    }
                else:
                    self.fixtures.add_group(self.fixtures.course)
                    self.fixtures.add_group_answer(assignment, self.fixtures.groups[-1], draft=True)
                    manage_expected = {
                        'id': instructor_answer.uuid,
                        'group_id': self.fixtures.groups[-1].uuid,
                        'content': 'This is another edit'
                    }
                draft_answer = self.fixtures.answers[-1]

                rv = self.client.post(
                    self.base_url + '/' + instructor_answer.uuid,
                    data=json.dumps(manage_expected),
                    content_type='application/json')
                self.assert200(rv)
                self.assertEqual(instructor_answer.uuid, rv.json['id'])
                self.assertEqual('This is another edit', rv.json['content'])
                self.assertFalse(draft_answer.active)
                if not assignment.enable_group_answers:
                    self.assertEqual(instructor_answer.user_uuid, rv.json['user_id'])
                    self.assertEqual(instructor_answer.user_id, self.fixtures.students[-1].id)
                else:
                    self.assertEqual(instructor_answer.group_uuid, rv.json['group_id'])
                    self.assertEqual(instructor_answer.group_id, self.fixtures.groups[-1].id)

            # test edit by author
            with self.login(self.fixtures.students[0].username):
                # test student can not submit answers after answer grace period
                assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
                db.session.add(assignment)
                db.session.commit()

                rv = self.client.post(
                    self.base_url + '/' + answer.uuid,
                    data=json.dumps(expected),
                    content_type='application/json')
                self.assert403(rv)
                self.assertEqual("Answer Not Submitted", rv.json['title'])
                self.assertEqual("Sorry, the answer deadline has passed. No answers can be submitted after the deadline unless the instructor submits the answer for you.",
                    rv.json['message'])

                # test student can submit answers within answer grace period
                assignment.answer_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
                db.session.add(assignment)
                db.session.commit()

                rv = self.client.post(
                    self.base_url + '/' + answer.uuid,
                    data=json.dumps(expected),
                    content_type='application/json')
                self.assert200(rv)
                self.assertEqual(answer.uuid, rv.json['id'])
                self.assertEqual('This is an edit', rv.json['content'])

            # test with impersonation
            student = self.fixtures.students[0]
            instructor = self.fixtures.instructor
            for impersonator in [DefaultFixture.ROOT_USER, instructor]:
                with self.impersonate(impersonator, student):
                    rv = self.client.post(
                        self.base_url + '/' + answer.uuid,
                        data=json.dumps(expected),
                        content_type='application/json')
                    self.assert403(rv)
                    self.assertTrue(rv.json['disabled_by_impersonation'])

    @mock.patch('compair.tasks.lti_outcomes.update_lti_course_grades.run')
    @mock.patch('compair.tasks.lti_outcomes.update_lti_assignment_grades.run')
    def test_delete_answer(self, mocked_update_assignment_grades_run, mocked_update_course_grades_run):
        student = self.fixtures.students[0]

        lti_consumer = self.lti_data.lti_consumer
        (lti_user_resource_link1, lti_user_resource_link2) = self.lti_data.setup_student_user_resource_links(
            student, self.fixtures.course, self.assignment)
        (lti_user_resource_link3, lti_user_resource_link4) = self.lti_data.setup_student_user_resource_links(
            student, self.fixtures.course, self.group_assignment)

        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            if not assignment.enable_group_answers:
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.user_id == student.id][0]
            else:
                group = student.get_course_group(self.fixtures.course.id)
                answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.group_id == group.id][0]

            # test login required
            rv = self.client.delete(self.base_url + '/' + answer.uuid)
            self.assert401(rv)

            # test unauthorized users
            with self.login(self.fixtures.students[-1].username):
                rv = self.client.delete(self.base_url + '/' + answer.uuid)
                self.assert403(rv)

            # test with impersonation
            instructor = self.fixtures.instructor
            for impersonator in [DefaultFixture.ROOT_USER, instructor]:
                with self.impersonate(impersonator, student):
                    rv = self.client.delete(self.base_url + '/' + answer.uuid)
                    self.assert403(rv)
                    self.assertTrue(rv.json['disabled_by_impersonation'])

            with self.login(student.username):
                # test invalid answer id
                rv = self.client.delete(self.base_url + '/999')
                self.assert404(rv)

                course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, student).grade
                assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, student).grade

                # test deletion by author
                rv = self.client.delete(self.base_url + '/' + answer.uuid)
                self.assert200(rv)
                self.assertEqual(answer.uuid, rv.json['id'])

                # grades should decrease
                new_course_grade = CourseGrade.get_user_course_grade(self.fixtures.course, student)
                new_assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, student)
                self.assertLess(new_course_grade.grade, course_grade)
                self.assertLess(new_assignment_grade.grade, assignment_grade)

                if not assignment.enable_group_answers:
                    mocked_update_assignment_grades_run.assert_called_once_with(
                        lti_consumer.id,
                        [[lti_user_resource_link2.lis_result_sourcedid, new_assignment_grade.id]]
                    )
                else:
                    mocked_update_assignment_grades_run.assert_called_once_with(
                        lti_consumer.id,
                        [[lti_user_resource_link4.lis_result_sourcedid, new_assignment_grade.id]]
                    )
                mocked_update_assignment_grades_run.reset_mock()

                self.assertEqual(mocked_update_course_grades_run.call_count, 2)
                mocked_update_course_grades_run.assert_any_call(
                    lti_consumer.id,
                    [[lti_user_resource_link1.lis_result_sourcedid, new_course_grade.id]]
                )
                mocked_update_course_grades_run.assert_any_call(
                    lti_consumer.id,
                    [[lti_user_resource_link3.lis_result_sourcedid, new_course_grade.id]]
                )
                mocked_update_course_grades_run.reset_mock()

            # test deletion by user that can manage posts
            with self.login(self.fixtures.instructor.username):
                for answer in [a for a in self.fixtures.answers if a.assignment_id == assignment.id and a.active]:
                    rv = self.client.delete(self.base_url + '/' + answer.uuid)
                    self.assert200(rv)
                    self.assertEqual(answer.uuid, rv.json['id'])

    def test_get_user_answers(self):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id][0]
            draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id][0]
            url = self._build_url(self.fixtures.course.uuid, assignment.uuid, '/user')

            # test login required
            rv = self.client.get(url)
            self.assert401(rv)

            student = self.fixtures.students[0]
            for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
                with user_context:
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

            with self.login(self.fixtures.instructor.username):
                rv = self.client.get(url)
                self.assert200(rv)
                self.assertEqual(2, len(rv.json['objects']))

                # test draft query
                rv = self.client.get(url, query_string={'draft': True})
                self.assert200(rv)
                self.assertEqual(0, len(rv.json['objects']))

    def test_get_user_draft_answers_during_impersonation(self):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id][0]
            draft_answer = [a for a in self.fixtures.draft_answers if a.assignment_id == assignment.id][0]
            url = self._build_url(self.fixtures.course.uuid, assignment.uuid, '/user')

            student = self.fixtures.draft_student
            with self.impersonate(self.fixtures.instructor, student):
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

    def test_top_answer(self):
        for assignment in [self.assignment, self.group_assignment]:
            self.base_url = self._build_url(self.fixtures.course.uuid, assignment.uuid)

            answer = [a for a in self.fixtures.answers if a.assignment_id == assignment.id][0]
            top_answer_url = self.base_url + "/" + answer.uuid + "/top"
            expected_top_on = {'top_answer': True}
            expected_top_off = {'top_answer': False}

            # test login required
            rv = self.client.post(top_answer_url, data=json.dumps(expected_top_on), content_type='application/json')
            self.assert401(rv)

            # test unauthorized users
            student = self.fixtures.unauthorized_student
            for user_context in [self.login(student.username), self.impersonate(DefaultFixture.ROOT_USER, student)]:
                with user_context:
                    rv = self.client.post(top_answer_url, data=json.dumps(expected_top_on), content_type='application/json')
                    self.assert403(rv)

            student = self.fixtures.students[0]
            for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
                with user_context:
                    rv = self.client.post(top_answer_url, data=json.dumps(expected_top_on), content_type='application/json')
                    self.assert403(rv)

            # test allow setting top_answer by instructor
            with self.login(self.fixtures.instructor.username):
                rv = self.client.post(top_answer_url, data=json.dumps(expected_top_on), content_type='application/json')
                self.assert200(rv)
                self.assertTrue(rv.json['top_answer'])

                rv = self.client.post(top_answer_url, data=json.dumps(expected_top_off), content_type='application/json')
                self.assert200(rv)
                self.assertFalse(rv.json['top_answer'])

            # test allow setting top_answer by teaching assistant
            with self.login(self.fixtures.ta.username):
                rv = self.client.post(top_answer_url, data=json.dumps(expected_top_on), content_type='application/json')
                self.assert200(rv)
                self.assertTrue(rv.json['top_answer'])

                rv = self.client.post(top_answer_url, data=json.dumps(expected_top_off), content_type='application/json')
                self.assert200(rv)
                self.assertFalse(rv.json['top_answer'])

class AnswerDemoAPITests(ComPAIRAPIDemoTestCase):
    def setUp(self):
        super(AnswerDemoAPITests, self).setUp()

    def test_delete_demo_answer(self):
        answers = Answer.query.all()
        student = User.query.filter_by(system_role=SystemRole.student).first()

        for answer in answers:
            url = '/api/courses/' + answer.course_uuid + '/assignments/' + answer.assignment_uuid + '/answers/' + answer.uuid

            with self.login('root'):
                # test deletion fails
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.delete(url)
                self.assert400(rv)

            # test with impersonation
            with self.impersonate(DefaultFixture.ROOT_USER, student):
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.delete(url)
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

            with self.login('root'):
                # test deletion success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.delete(url)
                self.assert200(rv)

    def test_edit_demo_answer(self):
        answers = Answer.query.all()
        student = User.query.filter_by(system_role=SystemRole.student).first()

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

            # test with impersonation
            with self.impersonate(DefaultFixture.ROOT_USER, student):
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert403(rv)
                self.assertTrue(rv.json['disabled_by_impersonation'])

            with self.login('root'):
                # test deletion success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert200(rv)
