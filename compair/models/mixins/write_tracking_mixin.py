from compair.core import db
from .create_tracking_mixin import CreateTrackingMixin
from .modify_tracking_mixin import ModifyTrackingMixin

from datetime import datetime
from flask_login import current_user
from sqlalchemy import event

class WriteTrackingMixin(ModifyTrackingMixin, CreateTrackingMixin):
    __abstract__ = True

    _write_tracking_enabled = True

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        def receive_before_insert(mapper, conn, target):
            if target._write_tracking_enabled:
                now = datetime.utcnow()

                target.created = now
                target.modified = now

                if current_user and current_user.is_authenticated:
                    target.created_user_id = current_user.id
                    target.modified_user_id = current_user.id

        @event.listens_for(cls, 'before_update')
        def receive_before_update(mapper, conn, target):
            if target._write_tracking_enabled:
                # only update fields when there is a real change
                # http://docs.sqlalchemy.org/en/latest/orm/events.html#sqlalchemy.orm.events.MapperEvents.before_update
                if db.session.object_session(target).is_modified(target, include_collections=False):
                    target.modified = datetime.utcnow()

                    if current_user and current_user.is_authenticated:
                        target.modified_user_id = current_user.id
                    else:
                        target.modified_user_id = None