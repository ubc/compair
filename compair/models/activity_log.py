# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class ActivityLog(DefaultTableMixin):
    __tablename__ = 'activity_log'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL"),
        nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="SET NULL"),
        nullable=True)
    timestamp = db.Column(
        db.TIMESTAMP,
        default=func.current_timestamp(),
        nullable=False
    )
    event = db.Column(db.String(50))
    data = db.Column(db.Text)
    status = db.Column(db.String(20))
    message = db.Column(db.Text)
    session_id = db.Column(db.String(100))
