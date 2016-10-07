from sqlalchemy.ext.declarative import declared_attr
from flask import abort
from sqlalchemy.orm import joinedload

from compair.core import db

class ActiveMixin(db.Model):
    __abstract__ = True

    @declared_attr
    def active(cls):
        return db.Column(
            db.Boolean(name='active'),
            default=True,
            nullable=False,
            index=True
        )

    @classmethod
    def get_active_or_404(cls, model_id, joinedloads=[]):
        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.get_or_404(model_id)
        if model is None or not model.active:
            abort(404)
        return model

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[]):
        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.filter_by(uuid=model_uuid).one_or_none()
        if model is None or not model.active:
            abort(404)
        return model