from datetime import datetime

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import current_user

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.session import Session
from sqlalchemy import event

from acj.core import db

class CreateTrackingMixin(db.Model):
    __abstract__ = True
    
    @declared_attr
    def created(cls):
        return db.Column(
            db.DateTime,
            default=datetime.utcnow,
            nullable=False
        )
    
    @declared_attr
    def created_user_id(cls):
        return db.Column(
            db.Integer, 
            db.ForeignKey('user.id', ondelete="SET NULL"),
            nullable=True
        )    

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        def receive_before_update(mapper, conn, target):
            target.created = datetime.utcnow()
            
            if current_user.is_authenticated():
                target.created_user_id = current_user.id