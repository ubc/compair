# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class LTIContext(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'lti_context'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    context_id = db.Column(db.String(191), nullable=False)
    context_type = db.Column(db.String(255), nullable=True)
    context_title = db.Column(db.String(255), nullable=True)
    ext_ims_lis_memberships_id = db.Column(db.String(255), nullable=True)
    ext_ims_lis_memberships_url = db.Column(db.Text, nullable=True)
    custom_context_memberships_url = db.Column(db.Text, nullable=True)
    compair_course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=True)
    lis_course_offering_sourcedid = db.Column(db.String(255), nullable=True)
    lis_course_section_sourcedid = db.Column(db.String(255), nullable=True)

    # relationships
    # compair_course via Course Model
    # lti_consumer via LTIConsumer Model
    lti_memberships = db.relationship("LTIMembership", backref="lti_context", lazy="dynamic")
    lti_resource_links = db.relationship("LTIResourceLink", backref="lti_context")

    # hybrid and other functions
    oauth_consumer_key = association_proxy('lti_consumer', 'oauth_consumer_key')
    compair_course_uuid = association_proxy('compair_course', 'uuid')

    @hybrid_property
    def membership_enabled(self):
        return self.membership_ext_enabled or self.membership_service_enabled

    @hybrid_property
    def membership_ext_enabled(self):
        return self.ext_ims_lis_memberships_url and self.ext_ims_lis_memberships_id

    @hybrid_property
    def membership_service_enabled(self):
        return self.custom_context_memberships_url

    def is_linked_to_course(self):
        return self.compair_course_id != None

    def update_enrolment(self, compair_user_id, course_role):
        from . import UserCourse
        if self.is_linked_to_course():
            user_course = UserCourse.query \
                .filter_by(
                    user_id=compair_user_id,
                    course_id=self.compair_course_id
                ) \
                .one_or_none()

            if user_course is None:
                # create new enrollment
                new_user_course = UserCourse(
                    user_id=compair_user_id,
                    course_id=self.compair_course_id,
                    course_role=course_role
                )
                db.session.add(new_user_course)
            else:
                user_course.course_role=course_role

            db.session.commit()

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

        if tool_provider.lis_course_offering_sourcedid:
            lti_context.lis_course_offering_sourcedid = tool_provider.lis_course_offering_sourcedid
        # lis_course_offering_sourcedid might not be available. if not, then check custom parameter
        elif tool_provider.custom_lis_course_offering_sourcedid:
            lti_context.lis_course_offering_sourcedid = tool_provider.custom_lis_course_offering_sourcedid

        if tool_provider.lis_course_section_sourcedid:
            lti_context.lis_course_section_sourcedid = tool_provider.lis_course_section_sourcedid
        # lis_course_section_sourcedid might not be available. if not, then check custom parameter
        elif tool_provider.custom_lis_course_section_sourcedid:
            lti_context.lis_course_section_sourcedid = tool_provider.custom_lis_course_section_sourcedid

        if tool_provider.custom_context_memberships_url:
            lti_context.custom_context_memberships_url = tool_provider.custom_context_memberships_url

        db.session.commit()

        return lti_context

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        db.UniqueConstraint('lti_consumer_id', 'context_id', name='_unique_lti_consumer_and_lti_context'),
        DefaultTableMixin.default_table_args
    )
