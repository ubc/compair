# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class AssignmentCriterion(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'assignment_criterion'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False)
    criterion_id = db.Column(db.Integer,  db.ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=False)

    # relationships
    # assignment many-to-many criterion with association assignment_criteria
    assignment = db.relationship("Assignment", back_populates="assignment_criteria")
    criterion = db.relationship("Criterion", back_populates="assignment_criteria", lazy='immediate')

    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('acj.models.assignment').Assignment(course_id=course_id))
    __table_args__ = (
        # prevent duplicate criteria in assignment
        db.UniqueConstraint('assignment_id', 'criterion_id', name='_unique_assignment_and_criterion'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()