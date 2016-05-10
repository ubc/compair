# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Answer(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete="SET NULL"), 
        nullable=True)
    content = db.Column(db.Text)
    round = db.Column(db.Integer, default=0, nullable=False)
    flagged = db.Column(db.Boolean(name='flagged'), default=False, nullable=False)
    flagger_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL"),
        nullable=True)
    
    # relationships
    # assignment via Assignment Model
    # user via User Model
    # file via File Model
    
    responses = db.relationship("AnswerResponse", backref="answer", lazy="dynamic")
    scores = db.relationship("Score", backref="answer", lazy="dynamic", 
        order_by='score.criteria_id')
    
    
    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id')
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')
    
    #TODO
    response_count = column_property(
        select([func.count(AnswerResponse.id)]).
        where(AnswerResponse.answer_id == id),
        deferred=True,
        group='counts'
    )
    
    private_response_count = column_property(
        select([func.count(AnswerResponse.id)]).
        where(and_(
            AnswerResponse.answer_id == id,
            or_(AnswerResponse.private == True,
                AnswerResponse.self_eval == False)
        )),
        deferred=True,
        group='counts'
    )
    
    self_eval_count = column_property(
        select([func.count(AnswerResponse.id)]).
        where(AnswerResponse.self_eval == True),
        deferred=True,
        group='counts'
    )

    @hybrid_property
    def public_response_count(self):
        return self.response_count - self.private_response_count

    




