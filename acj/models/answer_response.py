# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class AnswerResponse(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'answer_response'
    
    # table columns
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    content = db.Column(db.Text)
    private = db.Column(db.Boolean(name='private'), default=True, nullable=False)
    self_eval = db.Column(db.Boolean(name='self_eval'), default=False, nullable=False)
    
    # relationships
    # answer via Answer Model
    # user via User Model
    
    # hyprid and other functions
    course_id = association_proxy('answer', 'course_id')
    assignment_id = association_proxy('answer', 'assignment_id')
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')