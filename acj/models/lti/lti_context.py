# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIContext(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_context'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    context_id = db.Column(db.String(255), nullable=False)
    context_type = db.Column(db.String(255), nullable=True)
    context_title = db.Column(db.String(255), nullable=True)
    ext_ims_lis_memberships_id = db.Column(db.String(255), nullable=True)
    ext_ims_lis_memberships_url = db.Column(db.Text, nullable=True)
    acj_course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # acj_course via Course Model
    # lti_consumer via LTIConsumer Model
    lti_memberships = db.relationship("LTIMembership", backref="lti_context", lazy="dynamic")
    lti_resource_links = db.relationship("LTIResourceLink", backref="lti_context")

    # hyprid and other functions
    def is_linked_to_course(self):
        return self.acj_course_id != None

    @classmethod
    def get_by_lti_consumer_id_and_context_id(cls, lti_consumer_id, context_id):
        return LTIContext.query \
            .filter_by(
                lti_consumer_id=lti_consumer_id,
                context_id=context_id
            ) \
            .one_or_none()

    @classmethod
    def get_by_tool_provider(cls, lti_consumer, tool_provider):
        if tool_provider.context_id == None:
            return None

        lti_context = LTIContext.get_by_lti_consumer_id_and_context_id(
            lti_consumer.id, tool_provider.context_id)

        if lti_context == None:
            lti_context = LTIContext(
                lti_consumer_id=lti_consumer.id,
                context_id=tool_provider.context_id
            )
            db.session.add(lti_context)

        lti_context.context_type = tool_provider.context_type
        lti_context.context_title = tool_provider.context_title
        lti_context.ext_ims_lis_memberships_id = tool_provider.ext_ims_lis_memberships_id
        lti_context.ext_ims_lis_memberships_url = tool_provider.ext_ims_lis_memberships_url

        db.session.commit()

        return lti_context

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        db.UniqueConstraint('lti_consumer_id', 'context_id', name='_unique_lti_consumer_and_lti_context'),
        DefaultTableMixin.default_table_args
    )
