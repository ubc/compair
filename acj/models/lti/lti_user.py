# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIUser(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_user'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    lis_person_name_given = db.Column(db.String(255), nullable=True)
    lis_person_name_family = db.Column(db.String(255), nullable=True)
    lis_person_name_full = db.Column(db.String(255), nullable=True)
    lis_person_contact_email_primary = db.Column(db.String(255), nullable=True)
    user_oauth_id = db.Column(db.Integer, db.ForeignKey("user_oauth.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # TODO: build relationship on UserOAuth with
    # auth_type == AuthType.lti && auth_source_id = self.id

    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_consumer_id', 'user_id', name='_unique_lti_consumer_and_lti_user'),
        DefaultTableMixin.default_table_args
    )