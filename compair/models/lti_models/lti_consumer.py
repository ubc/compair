# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class LTIConsumer(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'lti_consumer'

    # table columns
    oauth_consumer_key = db.Column(db.String(191), unique=True, nullable=False)
    oauth_consumer_secret = db.Column(db.String(255), nullable=False)
    lti_version = db.Column(db.String(20), nullable=True)
    tool_consumer_instance_guid = db.Column(db.String(191), unique=True, nullable=True)
    tool_consumer_instance_name = db.Column(db.String(255), nullable=True)
    tool_consumer_instance_url = db.Column(db.Text, nullable=True)
    lis_outcome_service_url = db.Column(db.Text, nullable=True)
    global_unique_identifier_param = db.Column(db.String(255), nullable=True)
    student_number_param = db.Column(db.String(255), nullable=True)
    custom_param_regex_sanitizer = db.Column(db.String(255), nullable=True)

    # relationships
    lti_nonces = db.relationship("LTINonce", backref="lti_consumer", lazy="dynamic")
    lti_contexts = db.relationship("LTIContext", backref="lti_consumer", lazy="dynamic")
    lti_resource_links = db.relationship("LTIResourceLink", backref="lti_consumer", lazy="dynamic")
    lti_users = db.relationship("LTIUser", backref="lti_consumer", lazy="dynamic")

    # hybrid and other functions
    @classmethod
    def get_by_consumer_key(cls, consumer_key):
        return LTIConsumer.query \
            .filter_by(
                active=True,
                oauth_consumer_key=consumer_key
            ) \
            .one_or_none()

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

        # do no overwrite lis_outcome_service_url if value is None
        # some LTI consumers do not always send the lis_outcome_service_url
        # ex: Canvas when linking from module instead of an assignment
        if tool_provider.lis_outcome_service_url:
            lti_consumer.lis_outcome_service_url = tool_provider.lis_outcome_service_url

        db.session.commit()

        return lti_consumer

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "LTI Consumer Unavailable"
        if not message:
            message = "Sorry, this LTI consumer was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "LTI Consumer Unavailable"
        if not message:
            message = "Sorry, this LTI consumer was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()
