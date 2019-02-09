from compair.core import celery, db
from compair.models import User, UserCourse, CourseRole, \
    AnswerCommentType, EmailNotificationMethod, \
    AssignmentNotification, AssignmentNotificationType
from flask import current_app, render_template, url_for

from compair.tasks import send_message, send_messages

class Notification(object):
    @classmethod
    def _notification_enabled(cls):
        return current_app.config.get('MAIL_NOTIFICATION_ENABLED', False)

    @classmethod
    def send_new_answer_comment(cls, answer_comment):
        if not cls._notification_enabled():
            return

        author = answer_comment.user
        answer = answer_comment.answer
        assignment = answer.assignment
        course = assignment.course
        instructor_label = None

        # ensure recipient is student in class, has an email, and has email_notification_method enabled
        recipient = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                User.id == answer.user_id,
                User.email != None,
                User.email != "",
                User.email_notification_method == EmailNotificationMethod.enable,
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .first()

        # check if recipient is valid
        if not recipient:
            return

        # get the instructor/teaching assistant label if needed
        user_course = UserCourse.query \
            .filter(
                UserCourse.user_id == author.id,
                UserCourse.course_id == course.id
            ) \
            .first()
        if user_course:
            if user_course.course_role == CourseRole.instructor:
                instructor_label = CourseRole.instructor.value
            elif user_course.course_role == CourseRole.teaching_assistant:
                instructor_label = CourseRole.teaching_assistant.value

        # send the message
        subject = "New Answer Feedback in "+course.name
        html_body = render_template(
            'notification_new_answer_comment.html',
            user=recipient,
            subject=subject,
            course=course,
            assignment=assignment,
            author=author,
            comment=answer_comment,
            instructor_label=instructor_label,
            answer_comment_types=AnswerCommentType,
            compair_app_url_base=cls._get_base_url(),
        )
        text_body = render_template(
            'notification_new_answer_comment.txt',
            user=recipient,
            course=course,
            assignment=assignment,
            author=author,
            comment=answer_comment,
            instructor_label=instructor_label,
            answer_comment_types=AnswerCommentType,
            compair_app_url_base=cls._get_base_url(),
        )

        send_message.delay(
            recipients=[recipient.email],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    @classmethod
    def send_answer_period_ending_soon(cls, course, assignment, student):
        if not cls._notification_enabled():
            current_app.logger.debug("Email notification disabled. No action taken")
            return

        # ensure recipient is student in class, has an email, and has email_notification_method enabled
        recipient = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                User.id == student.id,
                User.email != None,
                User.email != "",
                User.email_notification_method == EmailNotificationMethod.enable,
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .first()

        # check if recipient is valid
        if not recipient:
            current_app.logger.debug("Email not found or unsubscribed. No action taken")
            return

        # send the message
        subject = "Answer period ending soon for an assignment in "+course.name
        html_body = render_template(
            'notification_answer_period_ending_soon.html',
            user=recipient,
            subject=subject,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )
        text_body = render_template(
            'notification_answer_period_ending_soon.txt',
            user=recipient,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )

        send_message.delay(
            recipients=[recipient.email],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        cls._mark_notified(assignment, student, AssignmentNotificationType.answer_period_end)

    @classmethod
    def send_comparison_period_ending_soon(cls, course, assignment, student):
        if not cls._notification_enabled():
            current_app.logger.debug("Email notification disabled. No action taken")
            return

        # ensure recipient is student in class, has an email, and has email_notification_method enabled
        recipient = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                User.id == student.id,
                User.email != None,
                User.email != "",
                User.email_notification_method == EmailNotificationMethod.enable,
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .first()

        # check if recipient is valid
        if not recipient:
            current_app.logger.debug("Email not found or unsubscribed. No action taken")
            return

        # send the message
        subject = "Comparison period ending soon for an assignment in "+course.name
        html_body = render_template(
            'notification_comparison_period_ending_soon.html',
            user=recipient,
            subject=subject,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )
        text_body = render_template(
            'notification_comparison_period_ending_soon.txt',
            user=recipient,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )

        send_message.delay(
            recipients=[recipient.email],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        cls._mark_notified(assignment, student, AssignmentNotificationType.comparison_period_end)

    @classmethod
    def send_self_eval_period_ending_soon(cls, course, assignment, student):
        if not cls._notification_enabled():
            current_app.logger.debug("Email notification disabled. No action taken")
            return

        # ensure recipient is student in class, has an email, and has email_notification_method enabled
        recipient = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                User.id == student.id,
                User.email != None,
                User.email != "",
                User.email_notification_method == EmailNotificationMethod.enable,
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .first()

        # check if recipient is valid
        if not recipient:
            current_app.logger.debug("Email not found or unsubscribed. No action taken")
            return

        # send the message
        subject = "Self-Evaluation period ending soon for an assignment in "+course.name
        html_body = render_template(
            'notification_self_eval_period_ending_soon.html',
            user=recipient,
            subject=subject,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )
        text_body = render_template(
            'notification_self_eval_period_ending_soon.txt',
            user=recipient,
            course=course,
            assignment=assignment,
            compair_app_url_base=cls._get_base_url(),
        )

        send_message.delay(
            recipients=[recipient.email],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        cls._mark_notified(assignment, student, AssignmentNotificationType.self_eval_period_end)

    @classmethod
    def _mark_notified(cls, assignment, user, notification_type):
        assignment_notification = AssignmentNotification(
            assignment_id = assignment.id,
            user_id = user.id,
            notification_type = notification_type.value
        )
        db.session.add(assignment_notification)
        db.session.commit()

    @classmethod
    def _get_base_url(cls):
        # For notifications triggered by backgrouond tasks,
        # there will be no endpoint routes defined for celery workers.
        # But the static_url_path is set.
        # So should be able to resolve 'static' in url_for
        base_url = None
        try:
            base_url = url_for('route_app', _external=True, _anchor='')
        except:
            base_url = url_for('static', _external=True, _anchor='', filename='')

        return base_url