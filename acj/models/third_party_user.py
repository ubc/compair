import hashlib
from flask import current_app
from datetime import datetime
import time

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from acj.core import db

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class ThirdPartyUser(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'third_party_user'

    # table columns
    type = db.Column(EnumType(ThirdPartyType, name="thirdpartytype"), nullable=False, index=True) # e.g. CWL
    unique_identifier = db.Column(db.String(255), nullable=False, index=True) # e.g. CWL username
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True) # ie ComPAIR account ID

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()
