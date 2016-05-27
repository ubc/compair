# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class AssignmentCriteria(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'assignment_criteria'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False)
    criteria_id = db.Column(db.Integer,  db.ForeignKey("criteria.id", ondelete="CASCADE"),
        nullable=False)

    # relationships
    # assignment many-to-many criteria with association assignment_criteria
    assignment = db.relationship("Assignment", back_populates="assignment_criteria")
    criteria = db.relationship("Criteria", back_populates="assignment_criteria")

    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('acj.models.assignment').Assignment(course_id=course_id))
    __table_args__ = (
        # prevent duplicate criteria in assignment
        db.UniqueConstraint('assignment_id', 'criteria_id', name='_unique_assignment_and_criteria'),
        DefaultTableMixin.default_table_args
    )