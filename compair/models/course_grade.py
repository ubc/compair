import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from compair.core import db

class CourseGrade(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'course_grade'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"),
        nullable=False)
    grade = db.Column(db.Float, default=0, nullable=False)

    # relationships
    # user via User Model
    # course via Course Model


    # hybrid and other functions
    @classmethod
    def get_course_grades(cls, course):
        return CourseGrade.query \
            .filter_by(course_id=course.id) \
            .all()

    @classmethod
    def get_user_course_grade(cls, course, user):
        return CourseGrade.query \
            .filter_by(
                user_id=user.id,
                course_id=course.id
            ) \
            .one_or_none()


    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('course_id', 'user_id', name='_unique_user_and_course'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def calculate_grade(cls, course, user):
        from . import AssignmentGrade, LTIOutcome, CourseRole

        user_is_student = False

        for course_user in course.user_courses:
            if course_user.user_id != user.id:
                continue
            user_is_student = course_user.course_role == CourseRole.student
            break

        assignment_ids = [assignment.id
            for assignment in course.assignments
            if assignment.active]

        # skip if there aren't any assignments
        if len(assignment_ids) == 0:
            CourseGrade.query \
                .filter_by(course_id=course.id) \
                .filter(CourseGrade.user_id.in_(student_ids)) \
                .delete()
            LTIOutcome.update_course_users_grade(course, student_ids)
            return

        elif not user_is_student:
            return

        # collect all of the students assignment grades
        student_assignment_grades = {
            # default grade of 0 in case assignment_grade record is missing
            assignment_id: 0.0 for assignment_id in assignment_ids
        }

        assignment_grades = AssignmentGrade.query \
            .filter_by(user_id=user.id) \
            .filter(AssignmentGrade.assignment_id.in_(assignment_ids)) \
            .all()
        for assignment_grade in assignment_grades:
            student_assignment_grades[assignment_grade.assignment_id] = assignment_grade.grade

        grade = _calculate_course_grade(course, student_assignment_grades)

        course_grade = CourseGrade.get_user_course_grade(course, user)
        if course_grade == None:
            course_grade = CourseGrade(
                user_id=user.id,
                course_id=course.id
            )

        course_grade.grade = grade

        db.session.add(course_grade)
        db.session.commit()

        LTIOutcome.update_course_user_grade(course, user.id)

    @classmethod
    def calculate_group_grade(cls, course, group):
        from . import CourseRole, AssignmentGrade, LTIOutcome

        student_ids = [course_user.user_id
            for course_user in course.user_courses
            if course_user.course_role == CourseRole.student and \
            course_user.group_id == group.id]

        assignment_ids = [assignment.id
            for assignment in course.assignments
            if assignment.active]

        # skip if there aren't any assignments
        if len(student_ids) == 0:
            return

        if len(assignment_ids) == 0:
            CourseGrade.query \
                .filter_by(course_id=course.id) \
                .filter(CourseGrade.user_id.in_(student_ids)) \
                .delete()
            LTIOutcome.update_course_users_grade(course, student_ids)
            return

        # collect all of the students assignment grades
        student_assignment_grades = {}
        for student_id in student_ids:
            student_assignment_grades[student_id] = {}
            for assignment_id in assignment_ids:
                student_assignment_grades[student_id][assignment_id] = 0.0

        assignment_grades = AssignmentGrade.query \
            .filter(AssignmentGrade.assignment_id.in_(assignment_ids)) \
            .filter(AssignmentGrade.user_id.in_(student_ids)) \
            .all()
        for assignment_grade in assignment_grades:
            student_assignment_grades[assignment_grade.user_id][assignment_grade.assignment_id] = assignment_grade.grade

        course_grades = CourseGrade.query \
            .filter(CourseGrade.user_id.in_(student_ids)) \
            .all()
        new_course_grades = []
        for student_id in student_ids:
            grade = _calculate_course_grade(course, student_assignment_grades[student_id])

            course_grade = next((course_grade for course_grade in course_grades
                if course_grade.user_id == student_id
            ), None)

            if course_grade == None:
                course_grade = CourseGrade(
                    user_id=student_id,
                    course_id=course.id
                )
                new_course_grades.append(course_grade)

            course_grade.grade = grade

        db.session.add_all(course_grades + new_course_grades)
        db.session.commit()

        LTIOutcome.update_course_users_grade(course, student_ids)

    @classmethod
    def calculate_grades(cls, course):
        from . import CourseRole, AssignmentGrade, LTIOutcome

        student_ids = [course_user.user_id
            for course_user in course.user_courses
            if course_user.course_role == CourseRole.student]

        assignment_ids = [assignment.id
            for assignment in course.assignments
            if assignment.active]

        # skip if there aren't any assignments
        if len(student_ids) == 0 or len(assignment_ids) == 0:
            CourseGrade.query \
                .filter_by(course_id=course.id) \
                .delete()
            LTIOutcome.update_course_grades(course)
            return

        # collect all of the students assignment grades
        student_assignment_grades = {}
        for student_id in student_ids:
            student_assignment_grades[student_id] = {}
            for assignment_id in assignment_ids:
                student_assignment_grades[student_id][assignment_id] = 0.0

        assignment_grades = AssignmentGrade.query \
            .filter(AssignmentGrade.assignment_id.in_(assignment_ids)) \
            .filter(AssignmentGrade.user_id.in_(student_ids)) \
            .all()
        for assignment_grade in assignment_grades:
            student_assignment_grades[assignment_grade.user_id][assignment_grade.assignment_id] = assignment_grade.grade

        course_grades = CourseGrade.get_course_grades(course)
        new_course_grades = []
        for student_id in student_ids:
            grade = _calculate_course_grade(course, student_assignment_grades[student_id])

            course_grade = next((course_grade for course_grade in course_grades
                if course_grade.user_id == student_id
            ), None)

            if course_grade == None:
                course_grade = CourseGrade(
                    user_id=student_id,
                    course_id=course.id
                )
                new_course_grades.append(course_grade)

            course_grade.grade = grade

        db.session.add_all(course_grades + new_course_grades)
        db.session.commit()

        LTIOutcome.update_course_grades(course)

def _calculate_course_grade(course, assignment_grades):
    grade = 0.0
    total_grade_weight = 0.0

    # TODO: Assignments should have their own weights
    # for now they all have equal weights
    for assignment_id, assignment_grade in assignment_grades.items():
        grade += float(assignment_grade)
        total_grade_weight += 1.0

    # divide by total_grade_weight to get the final grade in range: [0.0, 1.0]
    return grade / total_grade_weight if total_grade_weight > 0 else 0.0