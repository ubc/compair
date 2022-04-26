from enum import Enum

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class UserCourse(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'user_course'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete="SET NULL"),
        nullable=True)
    course_role = db.Column(Enum(CourseRole),
        nullable=False, index=True)

    # relationships
    # user many-to-many course with association user_course
    user = db.relationship("User", foreign_keys=[user_id], back_populates="user_courses")
    course = db.relationship("Course", back_populates="user_courses")
    group = db.relationship("Group", back_populates="user_courses")

    # hybrid and other functions
    user_uuid = association_proxy('user', 'uuid')
    course_uuid = association_proxy('course', 'uuid')

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('course_id', 'user_id', name='_unique_user_and_course'),
        DefaultTableMixin.default_table_args
    )
