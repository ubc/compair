from sqlalchemy.ext.declarative import declared_attr

from acj.core import db

class ActiveMixin(db.Model):
    __abstract__ = True
    
    @declared_attr
    def active(cls):
        return db.Column(
            db.Boolean(name='active'),
            default=True,
            nullable=False
        )