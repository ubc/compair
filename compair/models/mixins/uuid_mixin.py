import uuid
import base64

from compair.core import db
from flask import abort

class UUIDMixin(db.Model):
    __abstract__ = True

    uuid = db.Column(db.CHAR(22), nullable=False, unique=True, default=lambda: str(base64.urlsafe_b64encode(uuid.uuid4().bytes)).replace('=', ''))

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[]):
        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.filter_by(uuid=model_uuid).one_or_none()
        if model is None:
            abort(404)
        return model