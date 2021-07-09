from datetime import datetime

from sqlalchemy.ext.declarative import declared_attr

from compair.core import db

class ModifyTrackingMixin(db.Model):
    __abstract__ = True

    @declared_attr
    def modified(cls):
        return db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def modified_user_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('user.id', ondelete="SET NULL"),
            nullable=True
        )