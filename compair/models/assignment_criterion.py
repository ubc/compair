# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class AssignmentCriterion(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'assignment_criterion'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=False)
    position = db.Column(db.Integer)
    weight = db.Column(db.Integer, default=1, nullable=False)

    # relationships
    # assignment many-to-many criterion with association assignment_criteria
    assignment = db.relationship("Assignment", back_populates="assignment_criteria")
    criterion = db.relationship("Criterion", back_populates="assignment_criteria", lazy='immediate')

    # hybrid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('compair.models.assignment').Assignment(course_id=course_id))
    course_uuid = association_proxy('assignment', 'course_uuid')

    assignment_uuid = association_proxy('assignment', 'uuid')

    criterion_uuid = association_proxy('criterion', 'uuid')

    __table_args__ = (
        # prevent duplicate criteria in assignment
        db.UniqueConstraint('assignment_id', 'criterion_id', name='_unique_assignment_and_criterion'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()