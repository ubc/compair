# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *
from importlib import import_module

from acj.core import db

class AnswerComment(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'answer_comment'

    # table columns
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    content = db.Column(db.Text)
    comment_type = db.Column(EnumType(AnswerCommentType, name="comment_type"),
        nullable=False, index=True)

    # relationships
    # answer via Answer Model
    # user via User Model

    #readonly

    # hyprid and other functionsx
    course_id = association_proxy('answer', 'course_id', creator=lambda course_id:
        import_module('acj.models.answer').Answer(course_id=course_id))
    assignment_id = association_proxy('answer', 'assignment_id')
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()