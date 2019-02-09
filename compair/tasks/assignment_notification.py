from datetime import datetime, timedelta
import pytz

from flask import current_app
from sqlalchemy import and_, or_
from compair.core import celery, db
from compair.models import Course, Assignment, User, Answer, AnswerComment, UserCourse, \
    CourseRole, EmailNotificationMethod, \
    AssignmentNotification, AssignmentNotificationType, AnswerCommentType
from compair.core import event

# We cannot import Notification from compair.notifications directly as Notification is imported as part of ComPAIR app.
# Trying to import it here will create circular import and fail.
# Instead, we use event to trigger it
on_answer_period_ending_soon = event.signal('ANSWER_PERIOD_ENDING_SOON')
on_comparison_period_ending_soon = event.signal('COMPARISON_PERIOD_ENDING_SOON')
on_self_eval_period_ending_soon = event.signal('SELF_EVAL_PERIOD_ENDING_SOON')

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def check_assignment_period_ending(self):
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    soon = now + timedelta(hours=24)  # 24 hours from now

    _scan_answer_period_end(self, soon)
    _scan_comparison_period_end(self, soon)
    _scan_self_eval_period_end(self, soon)

def _scan_answer_period_end(self, end):
    current_app.logger.debug("Looking for assignments with answering period ending soon...")

    courses = Course.query \
        .filter(Course.active==True) \
        .all()
    for course in [c for c in courses if c.available]:
        for assignment in [a for a in course.assignments if a.active and a.answer_period_ending_soon(end)]:
            for student in [uc.user for uc in course.user_courses if uc.course_role==CourseRole.student]:
                if not _has_answered(assignment, student) and not _has_notified(assignment, student, AssignmentNotificationType.answer_period_end):
                    if student.email_notification_method == EmailNotificationMethod.enable and student.email:
                        current_app.logger.debug("Going to remind student " + str(student.id) + " for answering assignment " + str(assignment.id))
                        on_answer_period_ending_soon.send(
                            self,
                            course=course,
                            assignment=assignment,
                            student=student)


def _scan_comparison_period_end(self, end):
    current_app.logger.debug("Looking for assignments with comparison period ending soon...")

    courses = Course.query \
        .filter(Course.active==True) \
        .all()
    for course in [c for c in courses if c.available]:
        for assignment in [a for a in course.assignments if a.active and a.comparison_period_ending_soon(end)]:
            for student in [uc.user for uc in course.user_courses if uc.course_role==CourseRole.student]:
                if not _has_compared(assignment, student) and not _has_notified(assignment, student, AssignmentNotificationType.comparison_period_end):
                    if student.email_notification_method == EmailNotificationMethod.enable and student.email:
                        current_app.logger.debug("Going to remind student " + str(student.id) + " for doing comparison for assignment " + str(assignment.id))
                        on_comparison_period_ending_soon.send(
                            self,
                            course=course,
                            assignment=assignment,
                            student=student)


def _scan_self_eval_period_end(self, end):
    current_app.logger.debug("Looking for assignments with self-eval period ending soon...")

    courses = Course.query \
        .filter(Course.active==True) \
        .all()
    for course in [c for c in courses if c.available]:
        for assignment in [a for a in course.assignments if a.active and a.self_eval_period_ending_soon(end)]:
            for student in [uc.user for uc in course.user_courses if uc.course_role==CourseRole.student]:
                # if not answered, there is nothing to self-eval
                if _has_answered(assignment, student) and \
                    not _has_self_evaluated(assignment, student) and \
                    not _has_notified(assignment, student, AssignmentNotificationType.self_eval_period_end):

                    if student.email_notification_method == EmailNotificationMethod.enable and student.email:
                        current_app.logger.debug("Going to remind student " + str(student.id) + " for doing self-eval for assignment " + str(assignment.id))
                        on_self_eval_period_ending_soon.send(
                            self,
                            course=course,
                            assignment=assignment,
                            student=student)


def _find_user_answers(assignment, user):
    group = user.get_course_group(assignment.course_id)
    group_id = group.id if group and group.active else None

    found_answers = Answer.query \
        .filter_by(
            assignment_id=assignment.id,
            comparable=True,
            active=True,
            practice=False,
            draft=False
        ) \
        .filter(or_(
            Answer.user_id == user.id,
            and_(Answer.group_id == group_id, Answer.group_id != None)
        )) \
        .all()
    return found_answers


def _has_answered(assignment, user):
    return len(_find_user_answers(assignment, user)) > 0


def _has_compared(assignment, user):
    return assignment.completed_comparison_count_for_user(user.id) >= assignment.total_comparisons_required


def _has_self_evaluated(assignment, user):
    group = user.get_course_group(assignment.course_id)
    group_id = group.id if group else None

    answers = _find_user_answers(assignment, user)

    if not answers:
        return False

    # try to find submitted self-eval
    self_eval_count = AnswerComment.query \
        .filter(and_(
            AnswerComment.answer_id==answers[0].id,
            AnswerComment.user_id==user.id,
            AnswerComment.comment_type==AnswerCommentType.self_evaluation,
            AnswerComment.active==True,
            AnswerComment.draft==False) \
        ) \
        .count()

    return self_eval_count > 0


def _has_notified(assignment, user, notification_type):
    notify_count = AssignmentNotification.query \
        .filter_by(
            assignment_id = assignment.id,
            user_id = user.id,
            notification_type = notification_type.value
        ) \
        .count()
    return notify_count > 0
