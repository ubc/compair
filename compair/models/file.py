# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class File(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'file'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    name = db.Column(db.String(255), nullable=False)
    alias = db.Column(db.String(255), nullable=False)

    # relationships
    # user via User Model

    assignments = db.relationship("Assignment", backref="file", lazy='dynamic')
    answers = db.relationship("Answer", backref="file", lazy='dynamic')

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()