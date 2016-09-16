import hashlib
from flask import current_app
from datetime import datetime
import time

# sqlalchemy
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
    third_party_type = db.Column(EnumType(ThirdPartyType, name="third_party_type"), nullable=False)
    unique_identifier = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    # relationships
    # user via User Model

    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('third_party_type', 'unique_identifier', name='_unique_third_party_type_and_unique_identifier'),
        DefaultTableMixin.default_table_args
    )