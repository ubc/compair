from six import text_type

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class LTIUserResourceLink(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_user_resource_link'

    # table columns
    lti_resource_link_id = db.Column(db.Integer, db.ForeignKey("lti_resource_link.id", ondelete="CASCADE"),
        nullable=False)
    lti_user_id = db.Column(db.Integer, db.ForeignKey("lti_user.id", ondelete="CASCADE"),
        nullable=False)
    roles = db.Column(db.String(255), nullable=True)
    lis_result_sourcedid = db.Column(db.String(255), nullable=True)
    course_role = db.Column(Enum(CourseRole), nullable=False)

    # relationships
    # lti_user via LTIUser Model
    # lti_resource_link via LTIResourceLink Model

    # hybrid and other functions
    context_id = association_proxy('lti_resource_link', 'context_id')
    resource_link_id = association_proxy('lti_resource_link', 'resource_link_id')
    user_id = association_proxy('lti_user', 'user_id')
    compair_user_id = association_proxy('lti_user', 'compair_user_id')

    @classmethod
    def get_by_lti_resource_link_id_and_lti_user_id(cls, lti_resource_link_id, lti_user_id):
        return LTIUserResourceLink.query \
            .filter_by(
                lti_resource_link_id=lti_resource_link_id,
                lti_user_id=lti_user_id
            ) \
            .one_or_none()

    @classmethod
    def get_by_tool_provider(cls, lti_resource_link, lti_user, tool_provider):
        from . import CourseRole

        lti_user_resource_link = LTIUserResourceLink.get_by_lti_resource_link_id_and_lti_user_id(
            lti_resource_link.id, lti_user.id)

        if lti_user_resource_link == None:
            lti_user_resource_link = LTIUserResourceLink(
                lti_resource_link_id=lti_resource_link.id,
                lti_user_id=lti_user.id
            )
            db.session.add(lti_user_resource_link)

        lti_user_resource_link.roles = text_type(tool_provider.roles)
        lti_user_resource_link.lis_result_sourcedid = tool_provider.lis_result_sourcedid

        # set course role every time
        if tool_provider.roles and any(
                    role.lower().find("instructor") >= 0 or
                    role.lower().find("faculty") >= 0 or
                    role.lower().find("staff") >= 0
                    for role in tool_provider.roles
                ):
            lti_user_resource_link.course_role = CourseRole.instructor
        elif tool_provider.roles and any(role.lower().find("teachingassistant") >= 0 for role in tool_provider.roles):
            lti_user_resource_link.course_role = CourseRole.teaching_assistant
        else:
            lti_user_resource_link.course_role = CourseRole.student

        db.session.commit()

        return lti_user_resource_link

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_resource_link_id', 'lti_user_id', name='_unique_lti_resource_link_and_lti_user'),
        DefaultTableMixin.default_table_args
    )
