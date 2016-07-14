# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *
from importlib import import_module

from acj.core import db
from acj.algorithms import ComparisonPair


class ComparisonExample(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'comparison_example'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    answer1_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    answer2_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)

    # relationships
    # assignment via Assignment Model
    comparisons = db.relationship("Comparison", backref="comparison_example", lazy="dynamic")
    answer1 = db.relationship("Answer", foreign_keys=[answer1_id])
    answer2 = db.relationship("Answer", foreign_keys=[answer2_id])

    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('acj.models.assignment').Assignment(course_id=course_id))

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()