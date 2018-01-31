import hashlib
import json

from flask import current_app
from datetime import datetime
import time

# sqlalchemy
from sqlalchemy.orm import synonym
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_enum34 import EnumType

from . import *

from compair.core import db

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class ThirdPartyUser(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'third_party_user'

    # table columns
    third_party_type = db.Column(EnumType(ThirdPartyType, name="third_party_type"), nullable=False)
    unique_identifier = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    _params = db.Column(db.Text)

    # relationships
    # user via User Model
    compair_user_uuid = association_proxy('user', 'uuid')

    # hyprid and other functions

    @property
    def params(self):
        return json.loads(self._params) if self._params else None

    @params.setter
    def params(self, params):
        self._params = json.dumps(params) if params else None

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('third_party_type', 'unique_identifier', name='_unique_third_party_type_and_unique_identifier'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Third Party User Unavailable"
        if not message:
            message = "Sorry, this third party user was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)