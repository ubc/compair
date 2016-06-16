# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Course(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # relationships

    # user many-to-many course with association user_course
    user_courses = db.relationship("UserCourse", back_populates="course", lazy="dynamic")

    assignments = db.relationship("Assignment", backref="course", lazy="dynamic")

    # hyprid and other functions

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()