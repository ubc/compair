import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_, case, exists
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db
from compair.util import sql_utcnow

class Course(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'course'

    # table columns
    name = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    term = db.Column(db.String(255), nullable=False)
    sandbox = db.Column(db.Boolean(), nullable=False, default=False, index=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    # relationships

    # user many-to-many course with association user_course
    user_courses = db.relationship("UserCourse", back_populates="course", lazy="dynamic")
    assignments = db.relationship("Assignment", backref="course", lazy="dynamic")
    grades = db.relationship("CourseGrade", backref="course", lazy='dynamic')
    groups = db.relationship("Group", backref="course", lazy='dynamic')

    # lti
    lti_contexts = db.relationship("LTIContext", backref="compair_course", lazy='dynamic')

    # hybrid and other functions
    @hybrid_property
    def lti_linked(self):
        return self.lti_context_count > 0

    @hybrid_property
    def lti_has_sis_data(self):
        return self.lti_context_sis_count > 0

    @hybrid_property
    def lti_sis_data(self):
        sis_data = {}
        for lti_context in self.lti_contexts.all():
            sis_course_id = lti_context.lis_course_offering_sourcedid
            sis_section_id = lti_context.lis_course_section_sourcedid
            if not sis_course_id or not sis_section_id:
                continue
            sis_data.setdefault(sis_course_id, []).append(sis_section_id)
        return sis_data

    @hybrid_property
    def available(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())

        # must be after start date if set
        if self.start_date and self.start_date.replace(tzinfo=pytz.utc) > now:
            return False

        # must be before end date if set
        if self.end_date and now >= self.end_date.replace(tzinfo=pytz.utc):
            return False

        return True

    @hybrid_property
    def start_date_order(self):
        if self.start_date:
            return self.start_date
        elif self.min_assignment_answer_start:
            return self.min_assignment_answer_start
        else:
            return self.created

    @start_date_order.expression
    def start_date_order(cls):
        return case([
            (cls.start_date != None, cls.start_date),
            (cls.min_assignment_answer_start != None, cls.min_assignment_answer_start)
        ], else_ = cls.created)

    def calculate_grade(self, user):
        from . import CourseGrade
        CourseGrade.calculate_grade(self, user)

    def calculate_group_grade(self, group):
        from . import CourseGrade
        CourseGrade.calculate_group_grade(self, group)

    def calculate_grades(self):
        from . import CourseGrade
        CourseGrade.calculate_grades(self)

    def clear_lti_links(self):
        for lti_context in self.lti_contexts.all():
            lti_context.compair_course_id = None
        for assignment in self.assignments.all():
            assignment.clear_lti_links()

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Course Unavailable"
        if not message:
            message = "Sorry, this course was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Course Unavailable"
        if not message:
            message = "Sorry, this course was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        from .lti_models import LTIContext
        from . import Assignment, UserCourse, CourseRole
        super(cls, cls).__declare_last__()

        cls.groups_locked = column_property(
            exists([1]).
            where(and_(
                Assignment.course_id == cls.id,
                Assignment.active == True,
                Assignment.enable_group_answers == True,
                or_(
                    and_(Assignment.compare_start == None, Assignment.answer_end <= sql_utcnow()),
                    and_(Assignment.compare_start != None, Assignment.compare_start <= sql_utcnow())
                )
            )),
            deferred=True,
            group="group_associates"
        )

        cls.min_assignment_answer_start = column_property(
            select([func.min(Assignment.answer_start)]).
            where(and_(
                Assignment.course_id == cls.id,
                Assignment.active == True
            )).
            scalar_subquery(),
            deferred=True,
            group="min_associates"
        )

        cls.lti_context_count = column_property(
            select([func.count(LTIContext.id)]).
            where(LTIContext.compair_course_id == cls.id).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

        cls.lti_context_sis_count = column_property(
            select([func.count(LTIContext.id)]).
            where(and_(
                LTIContext.compair_course_id == cls.id,
                LTIContext.lis_course_offering_sourcedid != None,
                LTIContext.lis_course_section_sourcedid != None,
            )).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

        cls.assignment_count = column_property(
            select([func.count(Assignment.id)]).
            where(and_(
                Assignment.course_id == cls.id,
                Assignment.active == True
            )).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

        cls.student_assignment_count = column_property(
            select([func.count(Assignment.id)]).
            where(and_(
                Assignment.course_id == cls.id,
                Assignment.active == True,
                Assignment.answer_start <= sql_utcnow()
            )).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

        cls.student_count = column_property(
            select([func.count(UserCourse.id)]).
            where(and_(
                UserCourse.course_id == cls.id,
                UserCourse.course_role == CourseRole.student
            )).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )
