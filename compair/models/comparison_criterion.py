# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import load_only
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app

from . import *
from importlib import import_module

from compair.core import db
from compair.algorithms import ComparisonPair, ComparisonWinner
from compair.algorithms.pair import generate_pair
from compair.algorithms.score import calculate_score, calculate_score_1vs1


class ComparisonCriterion(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'comparison_criterion'

    # table columns
    comparison_id = db.Column(db.Integer, db.ForeignKey('comparison.id', ondelete="CASCADE"),
        nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete="CASCADE"),
        nullable=False)
    winner = db.Column(Enum(WinningAnswer), nullable=True)
    content = db.Column(db.Text)

    # relationships
    # comparison via Comparison Model
    # criterion via Criterion Model

    # hybrid and other functions
    criterion_uuid = association_proxy('criterion', 'uuid')
    comparison_uuid = association_proxy('comparison', 'uuid')

    answer1_id = association_proxy('comparison', 'answer1_id')
    answer2_id = association_proxy('comparison', 'answer2_id')
    answer1_uuid = association_proxy('comparison', 'answer1_uuid')
    answer2_uuid = association_proxy('comparison', 'answer2_uuid')

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Criterion Unavailable"
        if not message:
            message = "Sorry, this criterion was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    def comparison_pair_winner(self):
        from . import WinningAnswer
        winner = None
        if self.winner == WinningAnswer.answer1:
            winner = ComparisonWinner.key1
        elif self.winner == WinningAnswer.answer2:
            winner = ComparisonWinner.key2
        return winner


    def convert_to_comparison_pair(self):
        return ComparisonPair(
            key1=self.answer1_id,
            key2=self.answer2_id,
            winner=self.comparison_pair_winner()
        )
