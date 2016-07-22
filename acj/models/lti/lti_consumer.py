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
    def get_by_consumer_key(cls, consumer_key):
        lti_consumer = LTIConsumer.query \
            .filter_by(
                active=True,
                key=consumer_key
            ) \
            .one()

        return lti_consumer

    @classmethod
    def get_by_tool_provider(cls, tool_provider):
        lti_consumer = LTIConsumer.get_by_consumer_key(
            tool_provider.consumer_key)

        if lti_consumer == None:
            return None

        lti_consumer.lti_version = tool_provider.lti_version
        lti_consumer.tool_consumer_instance_guid = tool_provider.tool_consumer_instance_guid
        lti_consumer.tool_consumer_instance_name = tool_provider.tool_consumer_instance_name
        lti_consumer.tool_consumer_instance_url = tool_provider.tool_consumer_instance_url
        lti_consumer.lis_outcome_service_url = tool_provider.lis_outcome_service_url

        # update if needed
        if lti_consumer.session.is_modified(lti_consumer, include_collections=False):
            db.session.add(lti_consumer)
            db.session.commit()

        return lti_consumer

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()