import mimetypes

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

    # hyprid and other functions
    @hybrid_property
    def extension(self):
        return self.name.rsplit('.', 1)[1] if '.' in self.name else None

    @hybrid_property
    def mimetype(self):
        mimetype, encoding = mimetypes.guess_type(self.name)
        return mimetype

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()