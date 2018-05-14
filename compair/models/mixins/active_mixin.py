from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import joinedload

from compair.core import db, abort

class ActiveMixin(db.Model):
    __abstract__ = True

    @declared_attr
    def active(cls):
        return db.Column(db.Boolean(), default=True, nullable=False, index=True)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.filter_by(uuid=model_uuid).one_or_none()
        if model is None or not model.active:
            abort(404, title=title, message=message)
        return model