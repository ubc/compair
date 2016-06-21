# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Criterion(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    public = db.Column(db.Boolean(name='public'), default=False,
        nullable=False, index=True)
    default = db.Column(db.Boolean(name='default'), default=True,
        nullable=False, index=True)

    # relationships
    # user via User Model

    # assignment many-to-many criterion with association assignment_criteria
    assignment_criteria = db.relationship("AssignmentCriterion",
        back_populates="criterion", lazy='dynamic')

    comparisons = db.relationship("Comparison", backref="criterion", lazy='dynamic')
    scores = db.relationship("Score", backref="criterion", lazy='dynamic')

    # hyprid and other functions
    @hybrid_property
    def compared(self):
        return self.compare_count > 0

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.compare_count = column_property(
            select([func.count(Comparison.id)]).
            where(Comparison.criterion_id == cls.id),
            deferred=True,
            group="counts"
        )