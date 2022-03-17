# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class Criterion(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'criterion'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    public = db.Column(db.Boolean(), default=False,
        nullable=False, index=True)
    default = db.Column(db.Boolean(), default=True,
        nullable=False, index=True)

    # relationships
    # user via User Model

    # assignment many-to-many criterion with association assignment_criteria
    user_uuid = association_proxy('user', 'uuid')

    assignment_criteria = db.relationship("AssignmentCriterion",
        back_populates="criterion", lazy='dynamic')

    comparison_criteria = db.relationship("ComparisonCriterion", backref="criterion", lazy='dynamic')
    answer_criteria_scores = db.relationship("AnswerCriterionScore", backref="criterion", lazy='dynamic')

    # hybrid and other functions
    @hybrid_property
    def compared(self):
        return self.compare_count > 0

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Criterion Unavailable"
        if not message:
            message = "Sorry, this criterion was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Criterion Unavailable"
        if not message:
            message = "Sorry, this criterion was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.compare_count = column_property(
            select([func.count(ComparisonCriterion.id)]).
            where(ComparisonCriterion.criterion_id == cls.id).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )
