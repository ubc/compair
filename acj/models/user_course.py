from enum import Enum

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from acj.core import db

class UserCourse(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'user_course'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False)
    course_id = db.Column(db.Integer,  db.ForeignKey("course.id", ondelete="CASCADE"), 
        nullable=False)
    course_role = db.Column(EnumType(CourseRole, name="course_role"), 
        nullable=False, index=True)
    group_name = db.Column(db.String(255), nullable=True, index=True)
    
    # relationships
    # user many-to-many course with association user_course
    user = db.relationship("User", foreign_keys=[user_id], back_populates="user_courses")
    course = db.relationship("Course", back_populates="user_courses")
    
    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('course_id', 'user_id', name='_unique_user_and_course'),
        DefaultTableMixin.default_table_args
    )