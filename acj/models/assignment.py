import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from acj.core import db

class Assignment(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"),
        nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete="SET NULL"),
        nullable=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    answer_start = db.Column(db.DateTime(timezone=True))
    answer_end = db.Column(db.DateTime(timezone=True))
    compare_start = db.Column(db.DateTime(timezone=True), nullable=True)
    compare_end = db.Column(db.DateTime(timezone=True), nullable=True)
    number_of_comparisons = db.Column(db.Integer, nullable=False)
    students_can_reply = db.Column(db.Boolean(name='students_can_reply'),
        default=False, nullable=False)
    enable_self_evaluation = db.Column(db.Boolean(name='enable_self_evaluation'),
        default=False, nullable=False)
    pairing_algorithm = db.Column(EnumType(PairingAlgorithm, name="pairing_algorithm"),
        nullable=True, default=PairingAlgorithm.random)
    rank_display_limit = db.Column(db.Integer, nullable=True)

    # relationships
    # user via User Model
    # course via Course Model
    # file via File Model

    # assignment many-to-many criterion with association assignment_criteria
    assignment_criteria = db.relationship("AssignmentCriterion", back_populates="assignment")

    answers = db.relationship("Answer", backref="assignment", lazy="dynamic",
        order_by=Answer.created.desc())
    comments = db.relationship("AssignmentComment", backref="assignment", lazy="dynamic")
    comparisons = db.relationship("Comparison", backref="assignment", lazy="dynamic")
    comparison_examples = db.relationship("ComparisonExample", backref="assignment", lazy="dynamic")
    scores = db.relationship("Score", backref="assignment", lazy="dynamic")

    # hyprid and other functions
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')

    @hybrid_property
    def criteria(self):
        from . import Criterion, AssignmentCriterion
        return Criterion.query \
            .with_entities(Criterion) \
            .join(AssignmentCriterion) \
            .filter(and_(
                Criterion.active == True,
                AssignmentCriterion.active == True,
                AssignmentCriterion.assignment_id == self.id
            )) \
            .all()

    @hybrid_property
    def compared(self):
        return self.compare_count > 0

    def completed_comparison_count_for_user(self, user_id):
        comparison_count = self.comparisons \
            .filter_by(
                user_id=user_id,
                completed=True
            ) \
            .count()

        return comparison_count / self.criteria_count if self.criteria_count else 0

    @hybrid_property
    def available(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now

    @hybrid_property
    def answer_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        return answer_start <= now < answer_end

    @hybrid_property
    def answer_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        grace = self.answer_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now < grace

    @hybrid_property
    def compare_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        if not self.compare_start:
            return now >= answer_end
        else:
            return self.compare_start.replace(tzinfo=pytz.utc) <= now < self.compare_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def compare_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        if self.compare_start and self.compare_end:
            grace = self.compare_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
            compare_start = self.compare_start.replace(tzinfo=pytz.utc)
            return compare_start <= now < grace
        else:
            answer_end = self.answer_end.replace(tzinfo=pytz.utc)
            return now >= answer_end

    @hybrid_property
    def after_comparing(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        # compare period not set
        if not self.compare_start:
            return now >= answer_end
        # compare period is set
        else:
            return now >= self.compare_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def evaluation_count(self):
        evaluation_count = self.compare_count / self.criteria_count if self.criteria_count else 0
        return evaluation_count + self.self_evaluation_count

    @hybrid_property
    def total_comparisons_required(self):
        return self.number_of_comparisons + self.comparison_example_count

    @hybrid_property
    def total_steps_required(self):
        return self.total_comparisons_required + (1 if self.enable_self_evaluation else 0)

    def __repr__(self):
        if self.id:
            return "assignment " + str(self.id)
        else:
            return "assignment"

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.answer_count = column_property(
            select([func.count(Answer.id)]).
            where(and_(
                Answer.assignment_id == cls.id,
                Answer.active == True,
                Answer.draft == False,
                Answer.practice == False
            )),
            deferred=True,
            group="counts"
        )

        cls.comment_count = column_property(
            select([func.count(AssignmentComment.id)]).
            where(and_(
                AssignmentComment.assignment_id == cls.id,
                AssignmentComment.active == True
            )),
            deferred=True,
            group="counts"
        )

        cls.criteria_count = column_property(
            select([func.count(AssignmentCriterion.id)]).
            where(and_(
                AssignmentCriterion.assignment_id == cls.id,
                AssignmentCriterion.active == True
            )),
            deferred=True,
            group="counts"
        )

        cls.comparison_example_count = column_property(
            select([func.count(ComparisonExample.id)]).
            where(and_(
                ComparisonExample.assignment_id == cls.id,
                ComparisonExample.active == True
            )),
            deferred=True,
            group="counts"
        )

        cls.compare_count = column_property(
            select([func.count(Comparison.id)]).
            where(Comparison.assignment_id == cls.id),
            deferred=True,
            group="counts"
        )

        cls.self_evaluation_count = column_property(
            select([func.count(AnswerComment.id)]).
            where(and_(
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.active == True,
                AnswerComment.answer_id == Answer.id,
                AnswerComment.draft == False,
                Answer.assignment_id == cls.id
            )),
            deferred=True,
            group="counts"
        )