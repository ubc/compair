# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from acj.core import db

class LTIUserResourceLink(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_user_resource_link'

    # table columns
    lti_resource_link_id = db.Column(db.Integer, db.ForeignKey("lti_resource_link.id", ondelete="CASCADE"),
        nullable=False)
    lti_user_id = db.Column(db.Integer, db.ForeignKey("lti_user.id", ondelete="CASCADE"),
        nullable=False)
    roles = db.Column(db.String(255), nullable=True)
    lis_result_sourcedid = db.Column(db.String(255), nullable=True)
    acj_user_course_id = db.Column(db.Integer, db.ForeignKey("user_course.id", ondelete="CASCADE"),
        nullable=True)
    course_role = db.Column(EnumType(CourseRole, name="course_role"),
        nullable=False)

    # relationships
    # acj_user_course via UserCourse Model

    # hyprid and other functions
    def is_linked_to_user_course(self):
        return self.acj_user_course_id != None

    @classmethod
    def get_by_lti_resouce_link_id_and_lti_user_id(cls, lti_resouce_link_id, lti_user_id):
        lti_user = LTIContext.query \
            .filter_by(
                lti_resouce_link_id=lti_resouce_link_id,
                lti_user_id=lti_user_id
            ) \
            .one()

        return lti_user

    @classmethod
    def get_by_tool_provider(cls, lti_resource_link, lti_user, tool_provider):
        from . import CourseRole

        lti_user_resource_link = LTIUserResourceLink.get_by_lti_resouce_link_id_and_lti_user_id(
            lti_resource_link.id, lti_user.id)

        if lti_user_resource_link == None:
            lti_user_resource_link = LTIUserResourceLink(
                lti_resource_link_id=lti_resource_link.id,
                lti_user_id=lti_user.id
            )
        lti_user_resource_link.roles = tool_provider.roles
        lti_user_resource_link.lis_result_sourcedid = tool_provider.lis_result_sourcedid

        # set course role every time
        if tool_provider.is_instructor:
            lti_user_resource_link.course_role = CourseRole.instructor
        elif tool_provider.has_role("TeachingAssistant"):
            lti_user_resource_link.course_role = CourseRole.teaching_assistant
        else:
            lti_user_resource_link.course_role = CourseRole.student

        # create/update if needed
        if lti_user_resource_link.session.is_modified(lti_user_resource_link, include_collections=False):
            db.session.add(lti_user_resource_link)
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