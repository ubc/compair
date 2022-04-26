import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class KalturaMedia(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'kaltura_media'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)

    service_url = db.Column(db.String(255), nullable=False)
    partner_id = db.Column(db.Integer, default=0, nullable=False)
    player_id = db.Column(db.Integer, default=0, nullable=False)

    upload_ks = db.Column(db.String(1024), nullable=False)
    upload_token_id = db.Column(db.String(191), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=True)

    entry_id = db.Column(db.String(255), nullable=True)
    download_url = db.Column(db.String(255), nullable=True)

    # relationships
    # user via User Model
    files = db.relationship("File", backref="kaltura_media", lazy='dynamic')

    # hybrid and other functions
    @hybrid_property
    def extension(self):
        return self.file_name.lower().rsplit('.', 1)[1] if '.' in self.file_name else None

    @hybrid_property
    def media_type(self):
        from compair.kaltura import KalturaCore

        if self.extension in KalturaCore.video_extensions():
            return 1
        elif self.extension in KalturaCore.audio_extensions():
            return 5
        return None

    @hybrid_property
    def show_recent_warning(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        # modified will be when the upload was completed
        warning_period = self.modified.replace(tzinfo=pytz.utc) + datetime.timedelta(minutes=5)

        return now < warning_period

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()
