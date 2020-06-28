# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class LTIResourceLink(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_resource_link'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    lti_context_id = db.Column(db.Integer, db.ForeignKey("lti_context.id", ondelete="CASCADE"),
        nullable=True)
    resource_link_id = db.Column(db.String(191), nullable=False)
    resource_link_title = db.Column(db.String(255), nullable=True)
    launch_presentation_return_url = db.Column(db.Text, nullable=True)
    custom_param_assignment_id = db.Column(db.String(255), nullable=True)
    compair_assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # compair_assignment via Assignment Model
    # lti_consumer via LTIConsumer Model
    # lti_context via LTIContext Model
    lti_user_resource_links = db.relationship("LTIUserResourceLink", backref="lti_resource_link", lazy="dynamic")

    # hybrid and other functions
    context_id = association_proxy('lti_context', 'context_id')
    compair_assignment_uuid = association_proxy('compair_assignment', 'uuid')

    def is_linked_to_assignment(self):
        return self.compair_assignment_id != None

    def _update_link_to_compair_assignment(self, lti_context):
        from compair.models import Assignment

        if self.custom_param_assignment_id and lti_context and lti_context.compair_course_id:
            # check if assignment exists
            assignment = Assignment.query \
                .filter_by(
                    uuid=self.custom_param_assignment_id,
                    course_id=lti_context.compair_course_id,
                    active=True
                ) \
                .one_or_none()

            if assignment:
                self.compair_assignment = assignment
                return self

        self.compair_assignment = None
        return self

    @classmethod
    def get_by_lti_consumer_id_and_resource_link_id(cls, lti_consumer_id, resource_link_id):
        return LTIResourceLink.query \
            .filter_by(
                lti_consumer_id=lti_consumer_id,
                resource_link_id=resource_link_id
            ) \
            .one_or_none()

    @classmethod
    def get_by_tool_provider(cls, lti_consumer, tool_provider, lti_context=None):
        lti_resource_link = LTIResourceLink.get_by_lti_consumer_id_and_resource_link_id(
            lti_consumer.id, tool_provider.resource_link_id)

        if lti_resource_link == None:
            lti_resource_link = LTIResourceLink(
                lti_consumer_id=lti_consumer.id,
                resource_link_id=tool_provider.resource_link_id
            )
            db.session.add(lti_resource_link)

        lti_resource_link.lti_context_id = lti_context.id if lti_context else None
        lti_resource_link.resource_link_title = tool_provider.resource_link_title
        lti_resource_link.launch_presentation_return_url = tool_provider.launch_presentation_return_url
        lti_resource_link.custom_param_assignment_id = tool_provider.custom_assignment
        lti_resource_link._update_link_to_compair_assignment(lti_context)

        db.session.commit()

        return lti_resource_link

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_consumer_id', 'resource_link_id', name='_unique_lti_consumer_and_lti_resource_link'),
        DefaultTableMixin.default_table_args
    )
