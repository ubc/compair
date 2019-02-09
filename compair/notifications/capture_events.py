from compair.models import AnswerCommentType, UserCourse, CourseRole
from compair.api.answer_comment import on_answer_comment_create, on_answer_comment_modified
from compair.tasks.assignment_notification import on_answer_period_ending_soon, \
    on_comparison_period_ending_soon, on_self_eval_period_ending_soon
from .notification import Notification
from flask import current_app

def capture_notification_events():
    # answer comment events
    on_answer_comment_create.connect(notification_on_answer_comment_create)
    on_answer_comment_modified.connect(notification_on_answer_comment_modified)

def capture_assignment_ending_soon_events():
    # answer/comparison/self-eval period ending soon
    on_answer_period_ending_soon.connect(notification_on_answer_period_ending_soon)
    on_comparison_period_ending_soon.connect(notification_on_comparison_period_ending_soon)
    on_self_eval_period_ending_soon.connect(notification_on_self_eval_period_ending_soon)

# on_answer_comment_create
def notification_on_answer_comment_create(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    # don't notify on drafts
    if answer_comment.draft:
        return

    # don't notify on comments to self
    if user.id == answer_comment.answer.user_id:
        return

    # don't notify on self evaluations
    if answer_comment.comment_type == AnswerCommentType.self_evaluation:
        return

    Notification.send_new_answer_comment(answer_comment)

# on_answer_comment_modified
def notification_on_answer_comment_modified(sender, user, **extra):
    answer_comment = extra.get('answer_comment')
    was_draft = extra.get('was_draft')

    # don't notify on drafts or updates to when wasn't previously a draft
    if answer_comment.draft or not was_draft:
        return

    # don't notify on comments to self
    if user.id == answer_comment.answer.user_id:
        return

    # don't notify on self evaluations
    if answer_comment.comment_type == AnswerCommentType.self_evaluation:
        return

    Notification.send_new_answer_comment(answer_comment)


def notification_on_answer_period_ending_soon(sender, course, assignment, student):
    Notification.send_answer_period_ending_soon(course, assignment, student)

def notification_on_comparison_period_ending_soon(sender, course, assignment, student):
    Notification.send_comparison_period_ending_soon(course, assignment, student)

def notification_on_self_eval_period_ending_soon(sender, course, assignment, student):
    Notification.send_self_eval_period_ending_soon(course, assignment, student)