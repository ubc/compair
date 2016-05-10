# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Score(DefaultTableMixin, WriteTrackingMixin):
    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('criteria.id', ondelete="CASCADE"),
        nullable=False)
        
    score = db.Column(db.Float, default=0, nullable=False)
    excepted_score = db.Column(db.Float, default=0, nullable=False)
    rounds = db.Column(db.Integer, default=0, nullable=False)
    rounds = db.Column(db.Integer, default=0, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    opponents = db.Column(db.Integer, default=0, nullable=False)
    
    # relationships
    # assignment via Assignment Model
    # answer via Answer Model
    # criteria via Criteria Model
    
    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(WriteTrackingMixin, cls).__declare_last__()
        
        s_alias = cls.__table__.alias()
        cls.normalized_score = column_property(
            select([cls.score / func.max(s_alias.c.score) * 100]).
            where(and_(
                s_alias.c.criteria_id == cls.criteria_id,
                s_alias.c.assignment_id == cls.assignment_id,
            ))
        )

    __table_args__ = (
        db.UniqueConstraint('answer_id', 'criteria_id', name='_unique_answer_and_criteria'),
        DefaultTableMixin.default_table_args
    )