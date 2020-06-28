# sqlalchemy
from sqlalchemy.orm import column_property
from sqlalchemy import exc, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from . import *

from compair.core import db

class LTINonce(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_nonce'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    oauth_nonce = db.Column(db.String(191), nullable=False)
    oauth_timestamp = db.Column(db.TIMESTAMP, nullable=False)

    # relationships
    # lti_consumer via LTIConsumer Model

    # hybrid and other functions
    @classmethod
    def is_valid_nonce(cls, oauth_consumer_key, oauth_nonce, oauth_timestamp):
        from . import LTIConsumer
        lti_consumer = LTIConsumer.get_by_consumer_key(oauth_consumer_key)

        if lti_consumer == None:
            return False

        try:
            # is valid if it is unique on consumer, nonce, and timestamp
            # validate based on insert passing the unique check or not
            lti_nonce = LTINonce(
                lti_consumer_id=lti_consumer.id,
                oauth_nonce=oauth_nonce,
                oauth_timestamp=datetime.fromtimestamp(float(oauth_timestamp))
            )
            db.session.add(lti_nonce)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            return False

        return True

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('lti_consumer_id', 'oauth_nonce', 'oauth_timestamp', name='_unique_lti_consumer_nonce_and_timestamp'),
        DefaultTableMixin.default_table_args
    )