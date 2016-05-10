import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Assignment(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
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
    enable_self_eval = db.Column(db.Boolean(name='enable_self_eval'), 
        default=False, nullable=False)
    
    # relationships
    # course via Course Model
    # file via File Model
    
    # assignment many-to-many criteria with association assignment_criteria
    assignment_criteria = db.relationship("AssignmentCriteria", 
        back_populates="assignment", lazy='dynamic')
    
    _answers = db.relationship("Answer", backref="assignment", lazy="dynamic", 
        order_by="answer.created DESC")
    comments = db.relationship("AssignmentComment", backref="assignment", lazy="dynamic")
    comparisons = db.relationship("Comparison", backref="assignment", lazy="dynamic")
    scores = db.relationship("Score", backref="assignment", lazy="dynamic")
    
    # hyprid and other functions

    @hybrid_property
    def criteria(self):
        return self.assignment_criteria.join(Criteria) \
            .filter(AssignmentCriteria.active==True) \
            .filter(Criteria.active==True)
            
    @hybrid_property
    def answers(self):
        return self._answers \
            .filter(Answer.active==True)
        
    answers_count = column_property(
        select([func.count(Answer.id)]).
        where(and_(
            Answer.assignment_id == id,
            Answer.active == True
        )),
        deferred=True,
        group="counts"
    )

    comments_count = column_property(
        select([func.count(AssignmentComment.id)]).
        where(and_(
            AssignmentComment.assignment_id == id, 
            AssignmentComment.active == True
        )),
        deferred=True,
        group="counts"
    )

    criteria_count = column_property(
        select([func.count(AssignmentCriteria.id)]).
        where(and_(
            AssignmentCriteria.assignment_id == id, 
            AssignmentCriteria.active == True
        )),
        deferred=True,
        group="counts"
    )

    compared = column_property(
        select([func.count(Comparison.id) > 0]).
        where(Comparison.assignment_id == id),
        deferred=True,
        group="counts"
    )

    compare_count = column_property(
        select([func.count(Comparison.id)]).
        where(Comparison.assignment_id == id),
        deferred=True,
        group="counts"
    )

    _self_eval_count = column_property(
        select([func.count(AnswerResponse.id)]).
        where(and_(
            AnswerResponse.self_eval == True,
            AnswerResponse.active == True,
            AnswerResponse.answer_id == Answer.id,
            Answer.assignment_id == id
        )),
        deferred=True,
        group="counts"
    )

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
        return evaluation_count + self._self_eval_count

    def __repr__(self):
        if self.id:
            return "Assignment " + str(self.id)
        else:
            return "Assignment"