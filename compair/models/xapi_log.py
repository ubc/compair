# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class XAPILog(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'xapi_log'

    # table columns
    statement = db.Column(db.Text)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()