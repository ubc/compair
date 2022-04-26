# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from compair.algorithms import ScoredObject

from . import *

from compair.core import db

class AnswerCriterionScore(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'answer_criterion_score'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete="CASCADE"),
        nullable=False)

    """
    Comparative Judgement
    score = expected score / number of opponents
    score_variable1 = expected score
    score_variable2 = None

    Elo Rating
    score = Elo rating
    score_variable1 = Elo rating
    score_variable2 = None

    True Skill Rating
    score = Rating's Mu - (Default Mu / Default Sigma) * Rating's Sigma
    score_variable1 = Rating's Mu
    score_variable2 = Rating's Sigma
    """

    scoring_algorithm = db.Column(Enum(ScoringAlgorithm), nullable=True,
                                  default=ScoringAlgorithm.elo)
    score = db.Column(db.Float, default=0, nullable=False, index=True)
    variable1 = db.Column(db.Float, nullable=True)
    variable2 = db.Column(db.Float, nullable=True)
    rounds = db.Column(db.Integer, default=0, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    loses = db.Column(db.Integer, default=0, nullable=False)
    opponents = db.Column(db.Integer, default=0, nullable=False)

    # relationships
    # assignment via Assignment Model
    # answer via Answer Model
    # criterion via Criterion Model

    # hybrid and other functions
    criterion_uuid = association_proxy('criterion', 'uuid')

    def convert_to_scored_object(self):
        return ScoredObject(
            key=self.answer_id,
            score=self.score,
            variable1=self.variable1,
            variable2=self.variable2,
            rounds=self.rounds,
            wins=self.wins,
            loses=self.loses,
            opponents=self.opponents
        )

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        s_alias = cls.__table__.alias()
        cls.normalized_score = column_property(
            select([
                (cls.score - func.min(s_alias.c.score)) / (func.max(s_alias.c.score) - func.min(s_alias.c.score)) * 100
            ]).
            where(and_(
                s_alias.c.criterion_id == cls.criterion_id,
                s_alias.c.assignment_id == cls.assignment_id,
            )).
            scalar_subquery()
        )

    __table_args__ = (
        db.UniqueConstraint('answer_id', 'criterion_id', name='_unique_answer_and_criterion'),
        DefaultTableMixin.default_table_args
    )
