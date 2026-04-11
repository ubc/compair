# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
import nh3

from compair.notifications.notification import Notification
from compair.models import CourseRole, EmailNotificationMethod
from compair.core import db
from compair.tests.test_compair import ComPAIRTestCase
from data.fixtures.test_data import AnswerCommentsTestData


class NotificationTests(ComPAIRTestCase):
    def setUp(self):
        super(NotificationTests, self).setUp()
        self.data = AnswerCommentsTestData()
        self.assignment = self.data.get_assignments()[0]
        self.answer_comment = self.data.get_non_draft_answer_comments_by_assignment(self.assignment)[0]
        self.answer = self.answer_comment.answer

    def _get_html_render_call(self, mock_render_template):
        return next(
            c for c in mock_render_template.call_args_list
            if c.args[0] == 'notification_new_answer_comment.html'
        )

    @mock.patch('compair.notifications.notification.send_message')
    def test_no_notification_sent_when_mail_notification_disabled(self, mock_send_message):
        self.app.config['MAIL_NOTIFICATION_ENABLED'] = False

        Notification.send_new_answer_comment(self.answer_comment)

        mock_send_message.delay.assert_not_called()

    @mock.patch('compair.notifications.notification.send_message')
    def test_no_notification_sent_when_no_recipient(self, mock_send_message):
        self.answer.user.email_notification_method = EmailNotificationMethod.disable
        db.session.commit()

        Notification.send_new_answer_comment(self.answer_comment)

        mock_send_message.delay.assert_not_called()

    @mock.patch('compair.notifications.notification.send_message')
    def test_send_message_called_with_correct_recipient_and_subject(self, mock_send_message):
        Notification.send_new_answer_comment(self.answer_comment)

        mock_send_message.delay.assert_called_once()
        call_kwargs = mock_send_message.delay.call_args.kwargs
        self.assertEqual(call_kwargs['recipients'], [self.answer.user.email])
        self.assertIn(self.assignment.course.name, call_kwargs['subject'])

    @mock.patch('compair.notifications.notification.send_message')
    @mock.patch('compair.notifications.notification.render_template')
    def test_instructor_label_set_for_instructor(self, mock_render_template, mock_send_message):
        answer_comment = self.data.create_answer_comment(self.data.get_authorized_instructor(), self.answer)

        Notification.send_new_answer_comment(answer_comment)

        html_render_call = self._get_html_render_call(mock_render_template)
        self.assertEqual(html_render_call.kwargs['instructor_label'], CourseRole.instructor.value)

    @mock.patch('compair.notifications.notification.send_message')
    @mock.patch('compair.notifications.notification.render_template')
    def test_instructor_label_set_for_teaching_assistant(self, mock_render_template, mock_send_message):
        answer_comment = self.data.create_answer_comment(self.data.get_authorized_ta(), self.answer)

        Notification.send_new_answer_comment(answer_comment)

        html_render_call = self._get_html_render_call(mock_render_template)
        self.assertEqual(html_render_call.kwargs['instructor_label'], CourseRole.teaching_assistant.value)

    @mock.patch('compair.notifications.notification.send_message')
    @mock.patch('compair.notifications.notification.render_template')
    def test_instructor_label_none_for_student_author(self, mock_render_template, mock_send_message):
        Notification.send_new_answer_comment(self.answer_comment)

        html_render_call = self._get_html_render_call(mock_render_template)
        self.assertIsNone(html_render_call.kwargs['instructor_label'])

    @mock.patch('compair.notifications.notification.send_message')
    @mock.patch('compair.notifications.notification.render_template')
    def test_sanitized_content_passed_to_template(self, mock_render_template, mock_send_message):
        self.answer_comment.content = '<p>hello</p><script>alert("xss")</script>'

        with mock.patch('compair.notifications.notification.nh3.clean', wraps=nh3.clean) as mock_clean:
            Notification.send_new_answer_comment(self.answer_comment)

        mock_clean.assert_called_once_with(self.answer_comment.content)

        html_render_call = self._get_html_render_call(mock_render_template)
        sanitized = html_render_call.kwargs['sanitized_comment_content']
        self.assertNotIn('<script>', sanitized)
        self.assertIn('<p>hello</p>', sanitized)

    @mock.patch('compair.notifications.notification.send_message')
    @mock.patch('compair.notifications.notification.render_template')
    def test_none_content_passes_empty_string_to_template(self, mock_render_template, mock_send_message):
        self.answer_comment.content = None

        Notification.send_new_answer_comment(self.answer_comment)

        html_render_call = self._get_html_render_call(mock_render_template)
        self.assertEqual(html_render_call.kwargs['sanitized_comment_content'], '')
