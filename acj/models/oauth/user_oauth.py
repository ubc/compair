# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from acj.core import db

class UserOAuth(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'user_oauth'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False)
    auth_type = db.Column(EnumType(AuthType, name="auth_type"), nullable=False)
    auth_source_id = db.Column(db.Integer, nullable=False)

    # relationships
    # user via User Model



    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        db.UniqueConstraint('auth_type', 'auth_source_id', name='_unique_auth_type_and_auth_source'),
        DefaultTableMixin.default_table_args
    )