# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class CaliperLog(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'caliper_log'

    # table columns
    event = db.Column(db.Text)
    transmitted = db.Column(db.Boolean(), default=False, nullable=False, index=True)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()