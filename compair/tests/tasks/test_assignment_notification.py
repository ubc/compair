# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from compair.core import mail
from compair.tasks.assignment_notification import check_assignment_period_ending
from compair.tasks.send_mail import send_message
from compair.models import CourseRole

from data.fixtures.test_data import AnswerPeriodEndingSoonTestData, \
    ComparePeriodEndingSoonTestData, SelfEvalEndingSoonTestData
from compair.tests.test_compair import ComPAIRTestCase

class AssignmentNotificationTests(ComPAIRTestCase):

    def setUp(self):
        super(AssignmentNotificationTests, self).setUp()

    def _answer_notification_expected(self):
        expected = 0
        groups = self.data.get_groups()
        for assignment in self.data.get_assignments():
            if assignment.active and assignment.answer_period:
                # expect to notify all students...
                expected = expected + self.data.get_course().student_count
                # ... unless they answered
                answers = self.data.answers_by_assignment.get(assignment.id, {})
                if assignment.enable_group_answers:
                    for answer in answers:
                        if answer.group_answer and not answer.draft:
                            for group in groups:
                                if group.id == answer.group_id:
                                    expected = expected - group.user_courses.count()
                else:
                    expected = expected - len([a for a in answers if not a.draft])
        return expected

    def _compare_notification_expected(self):
        expected = 0
        for assignment in self.data.get_assignments():
            if assignment.active and assignment.compare_period and assignment.compare_end:
                for student in [uc.user for uc in self.data.get_course().user_courses.all() if uc.course_role == CourseRole.student]:
                    if assignment.completed_comparison_count_for_user(student.id) < assignment.total_comparisons_required:
                        expected += 1
        return expected

    def _self_eval_notification_expected(self):
        expected = 0
        groups = self.data.get_groups()
        for assignment in self.data.get_assignments():
            if assignment.active and assignment.self_eval_period and assignment.self_eval_end:
                # expect to notify all students...
                expected = expected + self.data.get_course().student_count
                # ... unless they answered and self-evaluated
                if assignment.enable_group_answers:
                    for answer in [a for a in assignment.answers if a.group_answer and not a.draft]:
                        for group in groups:
                            if group.id == answer.group_id:
                                expected = expected - (group.user_courses.count() - answer.self_evaluation_count)
                else:
                    expected = expected - len([a for a in assignment.answers if not a.draft and a.self_evaluation_count > 0])
        return expected

    def test_answer_notification_count(self):
        # combinations of submitted answers and drafts
        for num_answer in range(0, 3):
            for num_draft in range(0, 3):
                self.data = AnswerPeriodEndingSoonTestData(num_answer, num_draft)

                with mail.record_messages() as outbox:
                    # trigger the task explicitly
                    check_assignment_period_ending.apply()
                    # check emails sent
                    notification_count = len([m for m in outbox if m.subject.startswith('Answer period ending soon')])
                    self.assertEqual(notification_count, self._answer_notification_expected())

    def test_compare_notification_count(self):
        self.data = ComparePeriodEndingSoonTestData()

        with mail.record_messages() as outbox:
            # trigger the task explicitly
            check_assignment_period_ending.apply()
            # check emails sent
            notification_count = len([m for m in outbox if m.subject.startswith('Comparison period ending soon')])
            self.assertEqual(notification_count, self._compare_notification_expected())

    def test_self_eval_notification_count(self):
        self.data = SelfEvalEndingSoonTestData()

        with mail.record_messages() as outbox:
            # trigger the task explicitly
            check_assignment_period_ending.apply()
            # check emails sent
            notification_count = len([m for m in outbox if m.subject.startswith('Self-Evaluation period ending soon')])
            self.assertEqual(notification_count, self._self_eval_notification_expected())
