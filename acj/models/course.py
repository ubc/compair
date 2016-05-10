# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class Course(DefaultTableMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # relationships
    
    # user many-to-many course with association user_course
    user_courses = db.relationship("UserCourse", back_populates="course", lazy="dynamic")
    
    assignments = db.relationship("Assignment", backref="course", lazy="dynamic")
    
    # hyprid and other functions

    @classmethod
    def get_by_user(cls, user_id, inactive=False, fields=None):
        query = cls.query.join(UserCourse).filter_by(user_id=user_id)

        if not inactive:
            query = query.filter_by(UserCourse.course_role.notlike(CourseRole.dropped)) 

        if fields:
            query = query.options(load_only(*fields))

        return query.order_by(cls.name).all()

    @classmethod
    def exists_or_404(cls, course_id):
        return cls.query.options(load_only('id')).get_or_404(course_id)

    def enroll(self, users, role):
        if not isinstance(users, list):
            users = [users]

        associations = []
        for user in users:
            associations.append(
                UserCourse(user_id=user.id, course_id=self.id, course_role=role)
            )

        db.session.bulk_save_objects(associations)