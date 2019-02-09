from datetime import datetime

from . import *

from compair.core import db

class AssignmentNotification(DefaultTableMixin):
    __tablename__ = 'assignment_notification'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False)
    notification_type = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        DefaultTableMixin.default_table_args
    )
