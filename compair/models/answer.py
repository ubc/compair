# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *
from importlib import import_module

from compair.core import db

class Answer(DefaultTableMixin, UUIDMixin, AttemptMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'answer'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete="CASCADE"),
        nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete="SET NULL"),
        nullable=True)
    content = db.Column(db.Text)
    round = db.Column(db.Integer, default=0, nullable=False)
    practice = db.Column(db.Boolean(), default=False, nullable=False, index=True)
    draft = db.Column(db.Boolean(), default=False, nullable=False, index=True)
    top_answer = db.Column(db.Boolean(), default=False, nullable=False, index=True)
    comparable = db.Column(db.Boolean(), default=True, nullable=False, index=True)
    submission_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # relationships
    # assignment via Assignment Model
    # user via User Model
    # group via Group Model
    # file via File Model

    comments = db.relationship("AnswerComment", backref="answer")
    score = db.relationship("AnswerScore", uselist=False, backref="answer")
    criteria_scores = db.relationship("AnswerCriterionScore", backref="answer")

    # hybrid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('compair.models.assignment').Assignment(course_id=course_id))
    course_uuid = association_proxy('assignment', 'course_uuid')

    assignment_uuid = association_proxy('assignment', 'uuid')

    user_avatar = association_proxy('user', 'avatar')
    user_uuid = association_proxy('user', 'uuid')
    user_displayname = association_proxy('user', 'displayname')
    user_student_number = association_proxy('user', 'student_number')
    user_fullname = association_proxy('user', 'fullname')
    user_fullname_sortable = association_proxy('user', 'fullname_sortable')
    user_system_role = association_proxy('user', 'system_role')

    group_uuid = association_proxy('group', 'uuid')
    group_avatar = association_proxy('group', 'avatar')
    group_name = association_proxy('group', 'name')

    @hybrid_property
    def private_comment_count(self):
        return self.comment_count - self.public_comment_count

    @hybrid_property
    def group_answer(self):
        return self.group_id != None

    @group_answer.expression
    def group_answer(cls):
        return cls.group_id != None

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Answer Unavailable"
        if not message:
            message = "Sorry, this answer was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Answer Unavailable"
        if not message:
            message = "Sorry, this answer was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.comment_count = column_property(
            select([func.count(AnswerComment.id)]).
            where(and_(
                AnswerComment.answer_id == cls.id,
                AnswerComment.active == True,
                AnswerComment.draft == False
            )).scalar_subquery(),
            deferred=True,
            group='counts'
        )

        cls.public_comment_count = column_property(
            select([func.count(AnswerComment.id)]).
            where(and_(
                AnswerComment.answer_id == cls.id,
                AnswerComment.active == True,
                AnswerComment.draft == False,
                AnswerComment.comment_type == AnswerCommentType.public
            )).scalar_subquery(),
            deferred=True,
            group='counts'
        )

        cls.self_evaluation_count = column_property(
            select([func.count(AnswerComment.id)]).
            where(and_(
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.active == True,
                AnswerComment.draft == False,
                AnswerComment.answer_id == cls.id
            )).scalar_subquery(),
            deferred=True,
            group='counts'
        )
