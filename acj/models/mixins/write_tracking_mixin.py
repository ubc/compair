import datetime

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import current_user

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.session import Session
from sqlalchemy import event

from acj.core import db

class WriteTrackingMixin(db.Model):
    __abstract__ = True
    
    @declared_attr
    def modified(cls):
        return db.Column(
            db.DateTime,
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow,
            nullable=False
        )
    
    @declared_attr
    def modified_user_id(cls):
        return db.Column(
            db.Integer, 
            db.ForeignKey('user.id', ondelete="SET NULL"),
            nullable=True
        )
    
    @declared_attr
    def created(cls):
        return db.Column(
            db.DateTime,
            default=datetime.datetime.utcnow,
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
            target.modified = datetime.utcnow()
            
            if current_user is not None: 
                target.created_user_id = current_user.id
                target.modified_user_id = current_user.id
            
        @event.listens_for(cls, 'before_update')
        def receive_before_update(mapper, conn, target):
            # only update fields when there is a real change
            # http://docs.sqlalchemy.org/en/latest/orm/events.html#sqlalchemy.orm.events.MapperEvents.before_update
            if Session.object_session(target). \
                    is_modified(target, include_collections=False):
                target.modified = datetime.utcnow()
                
                if current_user is not None:
                    target.modified_user_id = current_user.id