import mimetypes

# sqlalchemy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db, abort

class File(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'file'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    kaltura_media_id = db.Column(db.Integer, db.ForeignKey('kaltura_media.id', ondelete="SET NULL"),
        nullable=True)
    name = db.Column(db.String(255), nullable=False)
    alias = db.Column(db.String(255), nullable=False)

    # relationships
    # user via User Model
    # kaltura_media via KalturaMedia Model

    assignments = db.relationship("Assignment", backref="file", lazy='dynamic')
    answers = db.relationship("Answer", backref="file", lazy='dynamic')

    # hyprid and other functions
    @hybrid_property
    def extension(self):
        return self.name.lower().rsplit('.', 1)[1] if '.' in self.name else None

    @hybrid_property
    def mimetype(self):
        mimetype, encoding = mimetypes.guess_type(self.name)
        return mimetype

    @hybrid_property
    def active(self):
        return self.assignment_count + self.answer_count > 0

    @classmethod
    def get_active_or_404(cls, model_id, joinedloads=[], title=None, message=None):
        if not title:
            title = "Attachment Unavailable"
        if not message:
            message = "The attachment was removed from the system or is no longer accessible."

        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.get_or_404(model_id)
        if model is None or not model.active:
            abort(404, title=title, message=message)
        return model

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Attachment Unavailable"
        if not message:
            message = "The attachment was removed from the system or is no longer accessible."

        query = cls.query
        # load relationships if needed
        for load_string in joinedloads:
            query.options(joinedload(load_string))

        model = query.filter_by(uuid=model_uuid).one_or_none()
        if model is None or not model.active:
            abort(404, title=title, message=message)
        return model

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.assignment_count = column_property(
            select([func.count(Assignment.id)]).
            where(and_(
                Assignment.file_id == cls.id,
                Assignment.active == True
            )),
            deferred=True,
            group="counts"
        )

        cls.answer_count = column_property(
            select([func.count(Answer.id)]).
            where(and_(
                Answer.file_id == cls.id,
                Answer.active == True
            )),
            deferred=True,
            group="counts"
        )