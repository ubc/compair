# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *
from importlib import import_module

from compair.core import db

class AnswerComment(DefaultTableMixin, UUIDMixin, AttemptMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'answer_comment'

    # table columns
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    content = db.Column(db.Text)
    comment_type = db.Column(Enum(AnswerCommentType),
        nullable=False, index=True)
    draft = db.Column(db.Boolean(), default=False, nullable=False, index=True)

    # relationships
    # answer via Answer Model
    # user via User Model

    #readonly

    # hybrid and other functionsx
    course_id = association_proxy('answer', 'course_id', creator=lambda course_id:
        import_module('compair.models.answer').Answer(course_id=course_id))
    course_uuid = association_proxy('answer', 'course_uuid')

    assignment_id = association_proxy('answer', 'assignment_id')
    assignment_uuid = association_proxy('answer', 'assignment_uuid')

    answer_uuid = association_proxy('answer', 'uuid')

    user_avatar = association_proxy('user', 'avatar')
    user_uuid = association_proxy('user', 'uuid')
    user_displayname = association_proxy('user', 'displayname')
    user_student_number = association_proxy('user', 'student_number')
    user_fullname = association_proxy('user', 'fullname')
    user_fullname_sortable = association_proxy('user', 'fullname_sortable')
    user_system_role = association_proxy('user', 'system_role')

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Feedback Unavailable"
        if not message:
            message = "Sorry, this feedback was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Feedback Unavailable"
        if not message:
            message = "Sorry, this feedback was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()
