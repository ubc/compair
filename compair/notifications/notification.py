from compair.core import celery, db
from compair.models import AssignmentComment, User, UserCourse, \
    CourseRole, AnswerCommentType, EmailNotificationMethod
from flask import current_app, render_template

from compair.tasks import send_message, send_messages

class Notification(object):
    @classmethod
    def _notification_enabled(cls):
        return current_app.config.get('MAIL_NOTIFICATION_ENABLED', False)

    @classmethod
    def send_new_help_comment(cls, assignment_comment):
        if not cls._notification_enabled():
            return

        author = assignment_comment.user
        assignment = assignment_comment.assignment
        course = assignment.course

        # ensure recipients are instructors in class, have an email, and have email_notification_method enabled
        recipients = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                User.email != None,
                User.email != "",
                User.email_notification_method == EmailNotificationMethod.enable,
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.instructor
            ) \
            .all()

        # check if there are any valid recipients
        if len(recipients) < 1:
            return

        # send the messages
        subject = "New Help Comment in "+course.name

        messages = []
        for recipient in recipients:
            html_body = render_template(
                'notification_new_help_comment.html',
                user=recipient,
                subject=subject,
                course=course,
                assignment=assignment,
                author=author,
                comment=assignment_comment,
            )
            text_body = render_template(
                'notification_new_help_comment.txt',
                user=recipient,
                course=course,
                assignment=assignment,
                author=author,
                comment=assignment_comment,
            )

            messages.append({
                'recipients': [recipient.email],
                'subject': subject,
                'html_body': html_body,
                'text_body': text_body
            })

        send_messages.delay(messages)

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
        )

        send_message.delay(
            recipients=[recipient.email],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )