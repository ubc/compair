# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIConsumer(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'lti_consumer'

    # table columns
    oauth_consumer_key = db.Column(db.String(255), unique=True, nullable=False)
    oauth_consumer_secret = db.Column(db.String(255), nullable=False)
    lti_version = db.Column(db.String(20), nullable=False)
    tool_consumer_instance_guid = db.Column(db.String(255), unique=True, nullable=True)
    tool_consumer_instance_name = db.Column(db.String(255), nullable=True)
    tool_consumer_instance_url = db.Column(db.Text, nullable=True)
    lis_outcome_service_url = db.Column(db.Text, nullable=True)

    # relationships

    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()