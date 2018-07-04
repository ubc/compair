# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import io
import os
import unicodecsv as csv
import re
import six

from data.fixtures import DefaultFixture
from data.fixtures.test_data import TestFixture
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import CourseRole, Answer, Comparison, AnswerComment, AnswerCommentType
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
                for assignment in assignments:
                    for user in course_users:
                        next_row = next(reader)
                        user_stats = self._check_participation_stat_report_user_row(assignment, user, next_row, overall_stats)

                # overall
                for user in course_users:
                    next_row = next(reader)
                    self._check_participation_stat_report_user_overall_row(user, next_row, overall_stats)

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

                for user in course_users:
                    next_row = next(reader)
                    user_stats = self._check_participation_stat_report_user_row(self.fixtures.assignments[0], user, next_row, overall_stats)

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

                for assignment in assignments:
                    for member in group_members:
                        next_row = next(reader)
                        user_stats = self._check_participation_stat_report_user_row(assignment, member, next_row, overall_stats)

                # overall
                for member in group_members:
                    next_row = next(reader)
                    self._check_participation_stat_report_user_overall_row(member, next_row, overall_stats)

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

                for member in group_members:
                    next_row = next(reader)
                    user_stats = self._check_participation_stat_report_user_row(self.fixtures.assignments[0], member, next_row, overall_stats)

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
            'Assignment', 'User UUID', 'Last Name', 'First Name', 'Answer Submitted', 'Answer ID',
            'Answer', 'Overall Rank', 'Overall Score',
            'Evaluations Submitted', 'Evaluations Required', 'Evaluation Requirements Met',
            'Replies Submitted']

        self.assertEqual(expected_heading, heading)

    def _check_participation_stat_report_user_overall_row(self, student, row, overall_stats):
        expected_row = []

        overall_stats.setdefault(student.id, {
            'answers_submitted': 0,
            'evaluations_submitted': 0,
            'evaluations_required': 0,
            'evaluation_requirements_met': True,
            'replies_submitted': 0
        })
        user_stats = overall_stats[student.id]

        expected_row.append("(Overall in Course)")
        expected_row.append(student.uuid)
        expected_row.append(student.lastname)
        expected_row.append(student.firstname)
        expected_row.append(str(user_stats["answers_submitted"]))
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append("")
        expected_row.append(str(user_stats["evaluations_submitted"]))
        expected_row.append(str(user_stats["evaluations_required"]))
        expected_row.append("Yes" if user_stats["evaluation_requirements_met"] else "No")
        expected_row.append(str(user_stats["replies_submitted"]))

        self.assertEqual(row, expected_row)


    def _check_participation_stat_report_user_row(self, assignment, student, row, overall_stats):
        expected_row = []

        overall_stats.setdefault(student.id, {
            'answers_submitted': 0,
            'evaluations_submitted': 0,
            'evaluations_required': 0,
            'evaluation_requirements_met': True,
            'replies_submitted': 0
        })
        user_stats = overall_stats[student.id]

        expected_row.append(assignment.name)
        expected_row.append(student.uuid)
        expected_row.append(student.lastname)
        expected_row.append(student.firstname)

        if not assignment.enable_group_answers:
            answer = Answer.query \
                .filter_by(
                    user_id=student.id,
                    assignment_id=assignment.id,
                    draft=False,
                    practice=False,
                    active=True,
                    comparable=True
                ) \
                .first()
        else:
            group = student.get_course_group(self.fixtures.course.id)
            answer = Answer.query \
                .filter_by(
                    group_id=group.id,
                    assignment_id=assignment.id,
                    draft=False,
                    practice=False,
                    active=True,
                    comparable=True
                ) \
                .first() if group else None

        if answer:
            user_stats["answers_submitted"] += 1
            expected_row.append("1")
            expected_row.append(answer.uuid)
            expected_row.append(self._snippet(answer.content))
        else:
            expected_row.append("0")
            expected_row.append("N/A")
            expected_row.append("N/A")

        if answer and answer.score:
            expected_row.append(str(answer.score.rank))
            expected_row.append(str(round(answer.score.normalized_score, 3)))   # round the floating point value for comparison
            row[8] = str(round(float(row[8]), 3))
        else:
            expected_row.append("Not Evaluated")
            expected_row.append("Not Evaluated")

        comparisons = Comparison.query \
            .filter(
                Comparison.completed == True,
                Comparison.user_id == student.id,
                Comparison.assignment_id == assignment.id
            ) \
            .all()
        evaluations_submitted = len(comparisons)

        user_stats["evaluations_submitted"] += evaluations_submitted
        expected_row.append(str(evaluations_submitted))

        user_stats["evaluations_required"] += assignment.total_comparisons_required
        expected_row.append(str(assignment.total_comparisons_required))

        if assignment.total_comparisons_required > evaluations_submitted:
            user_stats["evaluation_requirements_met"] = False
            expected_row.append("No")
        else:
            expected_row.append("Yes")

        answer_comments = AnswerComment.query \
            .filter(
                AnswerComment.user_id == student.id,
                AnswerComment.assignment_id == assignment.id
            ) \
            .all()

        replies_submitted = len(answer_comments)

        user_stats["replies_submitted"] += replies_submitted
        expected_row.append(str(replies_submitted))

        self.assertEqual(row, expected_row)


    def _check_participation_report_heading_rows(self, assignments, heading1, heading2):
        expected_heading1 = ['', '', '']
        for assignment in assignments:
            expected_heading1.append(assignment.name)
            for criterion in assignment.criteria:
                expected_heading1.append("")

        expected_heading2 = ['Last Name', 'First Name', 'Student No']
        for assignment in assignments:
            expected_heading2.append("Percentage score for answer overall")
            for criterion in assignment.criteria:
                expected_heading2.append("Percentage score for \""+criterion.name+"\"")
            expected_heading2.append("Evaluations Submitted ("+str(assignment.total_comparisons_required)+" required)")

        self.assertEqual(expected_heading1, heading1)
        self.assertEqual(expected_heading2, heading2)

    def _check_participation_report_user_row(self, assignments, student, row):
        self.assertEqual(row[0], student.lastname)
        self.assertEqual(row[1], student.firstname)
        self.assertEqual(row[2], student.student_number)

        index = 3
        for assignment in assignments:
            answer = None
            if not assignment.enable_group_answers:
                answer = Answer.query \
                    .filter(
                        Answer.user_id == student.id,
                        Answer.assignment_id == assignment.id,
                        Answer.draft == False,
                        Answer.active == True
                    ) \
                    .first()
            else:
                group = student.get_course_group(self.fixtures.course.id)
                answer = Answer.query \
                    .filter(
                        Answer.group_id == group.id,
                        Answer.assignment_id == assignment.id,
                        Answer.draft == False,
                        Answer.active == True
                    ) \
                    .first() if group else None

            if answer:
                if answer.score:
                    self.assertAlmostEqual(float(row[index]), answer.score.normalized_score)
                else:
                    self.assertEqual(row[index], "Not Evaluated")

            else:
                self.assertEqual(row[index], "No Answer")
            index += 1

            for criterion in assignment.criteria:
                if answer:
                    criterion_score = next((
                        criterion_score for criterion_score in answer.criteria_scores if \
                        criterion_score.criterion_id == criterion.id
                    ), None)

                    if criterion_score:
                        self.assertAlmostEqual(float(row[index]), criterion_score.normalized_score)
                    else:
                        self.assertEqual(row[index], "Not Evaluated")
                else:
                    self.assertEqual(row[index], "No Answer")
                index += 1

            evaluations_submitted = Comparison.query \
                .filter(
                    Comparison.user_id == student.id,
                    Comparison.assignment_id == assignment.id
                ) \
                .count()

            self.assertEqual(row[index], str(evaluations_submitted))
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
            "Last Name", "First Name", "Student No",
            "Last Name", "First Name", "Student No",
            "Feedback Type", "Feedback"
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