# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import io
import os
import unicodecsv as csv
import re
import six

from sqlalchemy import or_
from data.fixtures import DefaultFixture
from data.fixtures.test_data import TestFixture
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import CourseRole, Answer, Comparison, AnswerComment, AnswerCommentType, AssignmentGrade
from compair.core import db
from flask import current_app

class ReportAPITest(ComPAIRAPITestCase):
    def setUp(self):
        super(ReportAPITest, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_assignments=2,
            num_additional_criteria=1, num_groups=10, num_answers=25,
            num_group_assignments=2, num_group_answers=8,
            with_draft_student=True, with_comments=True, with_comparisons=True)
        self.url = "/api/courses/" + self.fixtures.course.uuid + "/report"
        self.files_to_cleanup = []

        self.delimiter = ",".encode('utf-8') if six.PY2 else ","

    def tearDown(self):
        folder = current_app.config['REPORT_FOLDER']

        for file_name in self.files_to_cleanup:
            file_path = os.path.join(folder, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(e)

    def test_generate_report(self):
        # test login required
        rv = self.client.post(self.url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(self.url)
            self.assert403(rv)

        for student in [self.fixtures.students[0], self.fixtures.unauthorized_student]:
            for user_context in [ \
                    self.login(student.username), \
                    self.impersonate(DefaultFixture.ROOT_USER, student)]:
                with user_context:
                    rv = self.client.post(self.url)
                    self.assert403(rv)

        # valid instructor with invalid params
        with self.login(self.fixtures.instructor.username):
            params = {
                'group_id': None,
                'type': "participation",
                'assignment': None
            }

            # test invalid course id
            rv = self.client.post('/api/courses/999/report', data=json.dumps(params), content_type='application/json')
            self.assert404(rv)

            # test missing report type
            invalid_params = params.copy()
            invalid_params['type'] = None
            rv = self.client.post(self.url, data=json.dumps(invalid_params), content_type='application/json')
            self.assert400(rv)

            # test invalid  report type
            invalid_params = params.copy()
            invalid_params['type'] = "invalid_type"
            rv = self.client.post(self.url, data=json.dumps(invalid_params), content_type='application/json')
            self.assert400(rv)

            # test invalid assignment id
            invalid_params = params.copy()
            invalid_params['assignment'] = "999"
            rv = self.client.post(self.url, data=json.dumps(invalid_params), content_type='application/json')
            self.assert404(rv)

            # test invalid group name
            invalid_params = params.copy()
            invalid_params['group_id'] = "999"
            rv = self.client.post(self.url, data=json.dumps(invalid_params), content_type='application/json')
            self.assert404(rv)

        # participation with valid instructor
        with self.login(self.fixtures.instructor.username):
            params = {
                'group_id': None,
                'type': "participation",
                'assignment': None
            }

            # test authorized user entire course
            rv = self.client.post(self.url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                assignments = self.fixtures.assignments
                self._check_participation_report_heading_rows(assignments, heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )
                for student in sorted_students:
                    next_row = next(reader)
                    self._check_participation_report_user_row(assignments, student, next_row)

            # test authorized user entire course (reversed criterion order)
            for assignment in self.fixtures.assignments:
                assignment_criteria = [assignment_criterion \
                    for assignment_criterion in assignment.assignment_criteria \
                    if assignment_criterion.active]
                assignment_criteria.reverse()

                for index, assignment_criterion in enumerate(assignment_criteria):
                    assignment.assignment_criteria.remove(assignment_criterion)
                    assignment.assignment_criteria.insert(index, assignment_criterion)

                db.session.commit()
                assignment.assignment_criteria.reorder()

            rv = self.client.post(self.url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                assignments = self.fixtures.assignments
                self._check_participation_report_heading_rows(assignments, heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )
                for student in sorted_students:
                    next_row = next(reader)
                    self._check_participation_report_user_row(assignments, student, next_row)

            # test authorized user one assignment
            single_assignment_params = params.copy()
            single_assignment_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(single_assignment_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                assignments = [self.fixtures.assignments[0]]
                self._check_participation_report_heading_rows(assignments, heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )
                for student in sorted_students:
                    next_row = next(reader)
                    self._check_participation_report_user_row(assignments, student, next_row)

            # test authorized user entire course with group name filter
            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                assignments = self.fixtures.assignments
                self._check_participation_report_heading_rows(assignments, heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )
                for student in sorted_students:
                    if student.user_courses[0].group_id != self.fixtures.groups[0].id:
                        continue

                    next_row = next(reader)
                    self._check_participation_report_user_row(assignments, student, next_row)

            # test authorized single assignment with group filter
            group_params = params.copy()
            group_params['assignment'] = self.fixtures.assignments[0].uuid
            group_params['group_id'] = self.fixtures.groups[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                assignments = [self.fixtures.assignments[0]]
                self._check_participation_report_heading_rows(assignments, heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )
                for student in sorted_students:
                    if student.user_courses[0].group_id != self.fixtures.groups[0].id:
                        continue

                    next_row = next(reader)
                    self._check_participation_report_user_row(assignments, student, next_row)

        # participation_stat with valid instructor
        with self.login(self.fixtures.instructor.username):
            params = {
                'group_id': None,
                'type': "participation_stat",
                'assignment': None
            }

            # test authorized user entire course
            rv = self.client.post(self.url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading = next(reader)
                assignments = self.fixtures.assignments
                self._check_participation_stat_report_heading_rows(heading)

                overall_stats = {}

                course_users = sorted(self.fixtures.students + [self.fixtures.instructor, self.fixtures.ta],
                    key=lambda u: (u.lastname, u.firstname, u.id))
                user_rows = {}   # structure: user_uuid / [rows from report]
                overall_rows = {}  # structure: user_uuid / row
                for next_row in reader:
                    if next_row[0] == '(Overall in Course)':
                        overall_rows[next_row[4]] = next_row
                    else:
                        user_rows.setdefault(next_row[4], []).append(next_row)
                for assignment in assignments:
                    for user in course_users:
                        user_stats = self._check_participation_stat_report_user_row(assignment, user, [row for row in user_rows[user.uuid] if row[0]==assignment.name], overall_stats)

                # overall
                for user in course_users:
                    self._check_participation_stat_report_user_overall_row(user, overall_rows[user.uuid], overall_stats)

            # test authorized user one assignment
            single_assignment_params = params.copy()
            single_assignment_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(single_assignment_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading = next(reader)
                self._check_participation_stat_report_heading_rows(heading)

                overall_stats = {}

                course_users = sorted(self.fixtures.students + [self.fixtures.instructor, self.fixtures.ta],
                    key=lambda u: (u.lastname, u.firstname, u.id))

                user_rows = {}   # structure: user_uuid / [rows from report]
                for next_row in reader:
                    user_rows.setdefault(next_row[4], []).append(next_row)
                for user in course_users:
                    user_stats = self._check_participation_stat_report_user_row(self.fixtures.assignments[0], user, user_rows[user.uuid], overall_stats)

            # test authorized user entire course with group_id filter
            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading = next(reader)
                assignments = self.fixtures.assignments
                self._check_participation_stat_report_heading_rows(heading)

                overall_stats = {}

                group_members = [u for u in self.fixtures.students if u.user_courses[0].group_id == self.fixtures.groups[0].id]
                group_members = sorted(group_members, key=lambda m: (m.lastname, m.firstname, m.id))

                user_rows = {}   # structure: user_uuid / [rows from report]
                overall_rows = {}  # structure: user_uuid / row
                for next_row in reader:
                    if next_row[0] == '(Overall in Course)':
                        overall_rows[next_row[4]] = next_row
                    else:
                        user_rows.setdefault(next_row[4], []).append(next_row)
                for assignment in assignments:
                    for member in group_members:
                        user_stats = self._check_participation_stat_report_user_row(assignment, member, [row for row in user_rows[member.uuid] if row[0]==assignment.name], overall_stats)

                # overall
                for member in group_members:
                    self._check_participation_stat_report_user_overall_row(member, overall_rows[member.uuid], overall_stats)

            # test authorized user one assignment
            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            group_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading = next(reader)
                self._check_participation_stat_report_heading_rows(heading)

                overall_stats = {}

                group_members = [u for u in self.fixtures.students if u.user_courses[0].group_id == self.fixtures.groups[0].id]
                group_members = sorted(group_members, key=lambda m: (m.lastname, m.firstname, m.id))

                user_rows = {}   # structure: user_uuid / [rows from report]
                for next_row in reader:
                    user_rows.setdefault(next_row[4], []).append(next_row)
                for member in group_members:
                    user_stats = self._check_participation_stat_report_user_row(self.fixtures.assignments[0], member, user_rows[member.uuid], overall_stats)

        # peer_feedback with valid instructor
        with self.login(self.fixtures.instructor.username):
            params = {
                'group_id': None,
                'type': "peer_feedback",
                'assignment': None
            }

            # test authorized user entire course
            rv = self.client.post(self.url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                self._check_peer_feedback_report_heading_rows(heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )

                for assignment in self.fixtures.assignments:
                    for student in sorted_students:
                        self._check_peer_feedback_report_user_rows(assignment, student, reader)

            # test authorized user one assignment
            single_assignment_params = params.copy()
            single_assignment_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(single_assignment_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                self._check_peer_feedback_report_heading_rows(heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )

                for student in sorted_students:
                    self._check_peer_feedback_report_user_rows(self.fixtures.assignments[0], student, reader)

            # test authorized user entire course with group_id filter
            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                self._check_peer_feedback_report_heading_rows(heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )

                for assignment in self.fixtures.assignments:
                    for student in sorted_students:
                        if student.user_courses[0].group_id != self.fixtures.groups[0].uuid:
                            continue
                        self._check_peer_feedback_report_user_rows(assignment, student, reader)

            # test authorized user one assignment
            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            group_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                self._check_peer_feedback_report_heading_rows(heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )

                for student in sorted_students:
                    if student.user_courses[0].group_id != self.fixtures.groups[0].uuid:
                        continue
                    self._check_peer_feedback_report_user_rows(self.fixtures.assignments[0], student, reader)

            # test authorized user one assignment (content's html parsed)
            original_content = {}
            for answer_comment in self.fixtures.answer_comments:
                if answer_comment.user.user_courses[0].group_id != self.fixtures.groups[0].id or \
                        answer_comment.assignment_id != self.fixtures.assignments[0].id:
                    continue
                original_content[answer_comment.id] = answer_comment.content
                answer_comment.content = '<p id="some_id">&#39;&quot;&gt;&lt;&amp;&nbsp;<\/p>'+answer_comment.content
            db.session.commit()

            group_params = params.copy()
            group_params['group_id'] = self.fixtures.groups[0].uuid
            group_params['assignment'] = self.fixtures.assignments[0].uuid
            rv = self.client.post(self.url, data=json.dumps(group_params), content_type='application/json')
            self.assert200(rv)
            self.assertIsNotNone(rv.json['file'])
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

            tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], file_name)
            with open(tmp_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.delimiter)

                heading1 = next(reader)
                heading2 = next(reader)
                self._check_peer_feedback_report_heading_rows(heading1, heading2)

                sorted_students = sorted(self.fixtures.students,
                    key=lambda student: (student.lastname, student.firstname, student.id)
                )

                for student in sorted_students:
                    if student.user_courses[0].group_id != self.fixtures.groups[0].id:
                        continue

                    answer_comments = sorted(
                        [ac for ac in self.fixtures.answer_comments if ac.user_id == student.id and
                            ac.assignment_id == self.fixtures.assignments[0].id],
                        key=lambda ac: (ac.created)
                    )

                    if len(answer_comments) > 0:
                        for answer_comment in answer_comments:
                            row = next(reader)
                            self.assertEqual(row[8], '\'"><& '+original_content[answer_comment.id])
                    else:
                        # skip user with no comments
                        row = next(reader)

        # test file unsafe course name
        with self.login(self.fixtures.instructor.username):
            self.fixtures.course.name = self.fixtures.course.name + " 2016/2017"
            db.session.commit()
            params = {
                'group_id': None,
                'type': "participation",
                'assignment': None
            }
            rv = self.client.post(self.url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            file_name = rv.json['file'].split("/")[-1]
            self.files_to_cleanup.append(file_name)

    def _check_participation_stat_report_heading_rows(self, heading):
        expected_heading = [
            'Assignment', 'Last Name', 'First Name', 'Student Number', 'User UUID',
            'Answer', 'Answer ID', 'Answer Deleted', 'Answer Submission Date', 'Answer Last Modified',
            'Answer Score (Normalized)', 'Overall Rank',
            'Comparisons Submitted', 'Comparisons Required', 'Comparison Requirements Met',
            'Self-Evaluation Submitted', 'Feedback Submitted (During Comparisons)', 'Feedback Submitted (Outside Comparisons)']

        self.assertEqual(expected_heading, heading)

    def _check_participation_stat_report_user_overall_row(self, student, row, overall_stats):
        expected_row = []

        overall_stats.setdefault(student.id, {
            'answers_submitted': 0,
            'evaluations_submitted': 0,
            'evaluations_required': 0,
            'evaluation_requirements_met': True,
            'comparison_feedback_submitted': 0,
            'standalone_feedback_submitted': 0,
            'self_evaluation_count': 0
        })
        user_stats = overall_stats[student.id]

        expected_row.append("(Overall in Course)")
        expected_row.append(student.lastname)
        expected_row.append(student.firstname)
        expected_row.append(student.student_number)
        expected_row.append(student.uuid)
        expected_row.append(str(user_stats["answers_submitted"]))
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append(str(user_stats["evaluations_submitted"]))
        expected_row.append(str(user_stats["evaluations_required"]))
        expected_row.append("Yes" if user_stats["evaluation_requirements_met"] else "No")
        expected_row.append(str(user_stats["self_evaluation_count"]))
        expected_row.append(str(user_stats["comparison_feedback_submitted"]))
        expected_row.append(str(user_stats["standalone_feedback_submitted"]))

        self.assertEqual(row, expected_row)


    def _check_participation_stat_report_user_row(self, assignment, student, rows, overall_stats):
        expected_row = []
        current_row = 0

        overall_stats.setdefault(student.id, {
            'answers_submitted': 0,
            'evaluations_submitted': 0,
            'evaluations_required': 0,
            'evaluation_requirements_met': True,
            'comparison_feedback_submitted': 0,
            'standalone_feedback_submitted': 0,
            'self_evaluation_count': 0
        })
        user_stats = overall_stats[student.id]

        if not assignment.enable_group_answers:
            answers = Answer.query \
                .filter_by(
                    user_id=student.id,
                    assignment_id=assignment.id,
                    draft=False,
                    practice=False,
                    comparable=True
                ) \
                .order_by(Answer.active.desc()) \
                .all()
        else:
            group = student.get_course_group(self.fixtures.course.id)
            answers = Answer.query \
                .filter_by(
                    group_id=group.id,
                    assignment_id=assignment.id,
                    draft=False,
                    practice=False,
                    comparable=True
                ) \
                .order_by(Answer.active.desc()) \
                .all() if group else []

        active_answer_submitted = len([ans for ans in answers if ans.active])
        if active_answer_submitted == 0:
            answers = [None] + answers

        # per assignment stats: evaluation required
        user_stats["evaluations_required"] += assignment.total_comparisons_required
        # per assignment stats: evaluation submitted
        comparisons = Comparison.query \
            .filter(
                Comparison.completed == True,
                Comparison.user_id == student.id,
                Comparison.assignment_id == assignment.id
            ) \
            .all()
        evaluations_submitted = len(comparisons)
        user_stats["evaluations_submitted"] += evaluations_submitted
        # per assignment stats: evaluation requirement met
        if assignment.total_comparisons_required > evaluations_submitted:
            user_stats["evaluation_requirements_met"] = False
        # per assignment stats: feedback submitted
        answer_comments = AnswerComment.query \
            .filter(
                AnswerComment.user_id == student.id,
                AnswerComment.assignment_id == assignment.id,
                AnswerComment.draft == False,
                AnswerComment.comment_type == AnswerCommentType.evaluation
            ) \
            .all()
        comparison_feedback_submitted = len(answer_comments)
        user_stats["comparison_feedback_submitted"] += comparison_feedback_submitted
        answer_comments = AnswerComment.query \
            .filter(
                AnswerComment.user_id == student.id,
                AnswerComment.assignment_id == assignment.id,
                AnswerComment.draft == False,
                or_(AnswerComment.comment_type == AnswerCommentType.private,
                    AnswerComment.comment_type == AnswerCommentType.public) \
            ) \
            .all()
        standalone_feedback_submitted = len(answer_comments)
        user_stats["standalone_feedback_submitted"] += standalone_feedback_submitted
        # per assignment stats: self-eval submitted
        self_evaluation = AnswerComment.query \
            .filter_by(comment_type=AnswerCommentType.self_evaluation) \
            .join(Answer) \
            .filter(Answer.assignment_id == assignment.id) \
            .filter(AnswerComment.user_id == student.id) \
            .filter(AnswerComment.draft == False) \
            .with_entities(Answer.assignment_id, AnswerComment.user_id) \
            .all()
        self_evaluation_count = len(self_evaluation)
        user_stats["self_evaluation_count"] += self_evaluation_count

        for answer in answers:
            expected_row = []
            expected_row.append(assignment.name)
            expected_row.append(student.lastname)
            expected_row.append(student.firstname)
            expected_row.append(student.student_number)
            expected_row.append(student.uuid)

            if answer:
                expected_row.append(self._snippet(answer.content))
                expected_row.append(answer.uuid)
                expected_row.append('N' if answer.active else 'Y')
                if answer.active:
                    user_stats["answers_submitted"] += 1
                expected_row.append(answer.submission_date.strftime("%Y-%m-%d %H:%M:%S") if answer.submission_date else "N/A")
                expected_row.append(answer.modified.strftime("%Y-%m-%d %H:%M:%S") if answer.modified else "N/A")
            else:
                expected_row.append("N/A")
                expected_row.append("N/A")
                expected_row.append("N/A")
                expected_row.append("N/A")
                expected_row.append("N/A")

            if answer and answer.score:
                expected_row.append(str(round(answer.score.normalized_score, 0)))   # round the floating point value for comparison
                expected_row.append(str(answer.score.rank) if answer.score.rank else '')
            else:
                expected_row.append("Not Evaluated")
                expected_row.append("Not Evaluated")

            expected_row.append(str(evaluations_submitted))

            expected_row.append(str(assignment.total_comparisons_required))

            if assignment.total_comparisons_required > evaluations_submitted:
                expected_row.append("No")
            else:
                expected_row.append("Yes")

            expected_row.append(str(self_evaluation_count))
            expected_row.append(str(comparison_feedback_submitted))
            expected_row.append(str(standalone_feedback_submitted))

            self.assertEqual(rows[current_row], expected_row)
            current_row += 1


    def _check_participation_report_heading_rows(self, assignments, heading1, heading2):
        expected_heading1 = ['', '', '']
        for assignment in assignments:
            expected_heading1.append(assignment.name)
            expected_heading1.append("")
            expected_heading1.append("")
            expected_heading1.append("")
            expected_heading1.append("")
            expected_heading1.append("")
            expected_heading1.append("")

        expected_heading2 = ['Last Name', 'First Name', 'Student Number']
        for assignment in assignments:
            expected_heading2.append("Participation Grade")
            expected_heading2.append("Answer")
            expected_heading2.append("Attachment")
            expected_heading2.append("Answer Score (Normalized)")
            expected_heading2.append("Comparisons Submitted ("+str(assignment.total_comparisons_required)+" required)")
            expected_heading2.append("Feedback Submitted (During Comparisons)")
            expected_heading2.append("Feedback Submitted (Outside Comparisons)")

        self.assertEqual(expected_heading1, heading1)
        self.assertEqual(expected_heading2, heading2)

    def _check_participation_report_user_row(self, assignments, student, row):
        self.assertEqual(row[0], student.lastname)
        self.assertEqual(row[1], student.firstname)
        self.assertEqual(row[2], student.student_number)

        index = 3
        for assignment in assignments:
            answer = None
            answer_count = 0
            if not assignment.enable_group_answers:
                answer_query = Answer.query \
                    .filter(
                        Answer.user_id == student.id,
                        Answer.assignment_id == assignment.id,
                        Answer.draft == False,
                        Answer.active == True
                    )
                answer = answer_query.first()
                answer_count = answer_query.count()
            else:
                group = student.get_course_group(self.fixtures.course.id)
                answer_query = Answer.query \
                    .filter(
                        Answer.group_id == group.id,
                        Answer.assignment_id == assignment.id,
                        Answer.draft == False,
                        Answer.active == True
                    )
                answer = answer_query.first() if group else None
                answer_count = answer_query.count() if group else 0

            # Participation Grade
            grade = AssignmentGrade.query \
                .filter(
                    AssignmentGrade.user_id == student.id,
                    AssignmentGrade.assignment_id == assignment.id,
                ).first()
            self.assertEqual(float(row[index]), round(grade.grade*100, 0))
            index += 1

            # Answer Submitted
            # self.assertEqual(row[index], str(answer_count))
            # index += 1

            # Answer
            if answer:
                self.assertEqual(row[index], answer.content)
            else:
                self.assertEqual(row[index], "")
            index += 1

            # Attachment
            if answer and answer.file:
                self.assertTrue(row[index].startswith("=HYPERLINK"))
            else:
                self.assertEqual(row[index], "")
            index += 1

            # Answer Score
            if answer:
                if answer.score:
                    self.assertAlmostEqual(float(row[index]), round(answer.score.normalized_score, 0))
                else:
                    self.assertEqual(row[index], "Not Evaluated")
            else:
                self.assertEqual(row[index], "No Answer")
            index += 1

            # Evaluation Submitted
            evaluations_submitted = Comparison.query \
                .filter(
                    Comparison.user_id == student.id,
                    Comparison.assignment_id == assignment.id
                ) \
                .count()
            self.assertEqual(row[index], str(evaluations_submitted))
            index += 1

            # comparison feedback submitted
            comparison_feedback_submitted = AnswerComment.query \
                .join(Answer, AnswerComment.answer_id == Answer.id) \
                .filter(
                    Answer.assignment_id == assignment.id,
                    AnswerComment.user_id == student.id,
                    AnswerComment.draft == False,
                    AnswerComment.comment_type == AnswerCommentType.evaluation
                ).count()
            self.assertEqual(row[index], str(comparison_feedback_submitted))
            index += 1

            # standalone feedback submitted
            standalone_feedback_submitted = AnswerComment.query \
                .join(Answer, AnswerComment.answer_id == Answer.id) \
                .filter(
                    Answer.assignment_id == assignment.id,
                    AnswerComment.user_id == student.id,
                    AnswerComment.draft == False,
                    or_(AnswerComment.comment_type == AnswerCommentType.public,
                    AnswerComment.comment_type == AnswerCommentType.private) \
                ).count()
            self.assertEqual(row[index], str(standalone_feedback_submitted))
            index += 1

    def _check_peer_feedback_report_heading_rows(self, heading1, heading2):
        expected_heading1 = [
            "",
            "Feedback Author", "", "",
            "Answer Author", "", "",
            "", ""
        ]
        self.assertEqual(expected_heading1, heading1)
        expected_heading2 = [
            "Assignment",
            "Last Name", "First Name", "Student Number",
            "Last Name", "First Name", "Student Number",
            "Feedback Type", "Feedback", "Feedback Character Count"
        ]
        self.assertEqual(expected_heading2, heading2)

    def _check_peer_feedback_report_user_rows(self, assignment, student, reader):

        answer_comments = sorted(
            [ac for ac in self.fixtures.answer_comments if ac.user_id == student.id and ac.assignment_id == assignment.id],
            key=lambda ac: (ac.created)
        )

        if len(answer_comments) > 0:
            for answer_comment in answer_comments:
                row = next(reader)

                feedback_type = ""
                if answer_comment.comment_type == AnswerCommentType.evaluation:
                    feedback_type = "Comparison"
                elif answer_comment.comment_type == AnswerCommentType.private:
                    feedback_type = "Private Reply"
                elif answer_comment.comment_type == AnswerCommentType.public:
                    feedback_type = "Public Reply"

                excepted_row = [
                    assignment.name,
                    student.lastname, student.firstname, student.student_number
                ]

                if answer_comment.answer.group_answer:
                    answer_group = answer_comment.answer.group
                    excepted_row += [answer_group.name, "", ""]
                else:
                    answer_user = answer_comment.answer.user
                    excepted_row += [answer_user.lastname, answer_user.firstname, answer_user.student_number]

                excepted_row += [feedback_type, self._strip_html(answer_comment.content)]
                char_count = len(self._strip_html(answer_comment.content))
                excepted_row.append(str(char_count))

                self.assertEqual(row, excepted_row)
        else:
            row = next(reader)

            excepted_row = [
                assignment.name,
                student.lastname, student.firstname, student.student_number,
                "---", "---", "---",
                "", ""
            ]

            self.assertEqual(row, excepted_row)

    def _strip_html(self, text):
        text = re.sub('<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', '\'')
        return text

    def _snippet(self, content, length=100, suffix='...'):
        if content == None:
            return ""
        content = self._strip_html(content)
        content = content.replace('\n', ' ').replace('\r', '').strip()
        if len(content) <= length:
            return content
        else:
            return ' '.join(content[:length+1].split(' ')[:-1]) + suffix