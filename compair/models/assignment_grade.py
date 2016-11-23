import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from . import *

from compair.core import db

class AssignmentGrade(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'assignment_grade'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    grade = db.Column(db.Float, default=0, nullable=False)

    # relationships
    # user via User Model
    # assignment via Course Model


    # hyprid and other functions
    @classmethod
    def get_assignment_grades(cls, assignment):
        return AssignmentGrade.query \
            .filter_by(assignment_id=assignment.id) \
            .all()

    @classmethod
    def get_user_assignment_grade(cls, assignment, user):
        return AssignmentGrade.query \
            .filter_by(
                user_id=user.id,
                assignment_id=assignment.id
            ) \
            .one_or_none()

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('assignment_id', 'user_id', name='_unique_user_and_assignment'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def calculate_grade(cls, assignment, user):
        from . import Answer, Comparison, CourseRole, \
            AnswerComment, AnswerCommentType, LTIOutcome

        student_ids = [course_user.user_id
            for course_user in assignment.course.user_courses
            if course_user.course_role == CourseRole.student]

        if user.id not in student_ids:
            return

        answer_count = Answer.query \
            .filter_by(
                assignment_id=assignment.id,
                user_id=user.id,
                active=True,
                practice=False,
                draft=False
            ) \
            .count()

        comparison_count = Comparison.query \
            .filter_by(
                user_id=user.id,
                assignment_id=assignment.id,
                completed=True
            ) \
            .count()
        comparison_count = comparison_count / assignment.criteria_count if assignment.criteria_count > 0 else 0

        self_evaluation_count = AnswerComment.query \
            .join("answer") \
            .filter(and_(
                AnswerComment.user_id == user.id,
                AnswerComment.active == True,
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.draft == False,
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False
            )) \
            .count()

        grade = _calculate_assignment_grade(assignment,
            answer_count, comparison_count, self_evaluation_count)

        assignment_grade = AssignmentGrade.get_user_assignment_grade(assignment, user)
        if assignment_grade == None:
            assignment_grade = AssignmentGrade(
                user_id=user.id,
                assignment_id=assignment.id
            )

        assignment_grade.grade = grade
        db.session.add(assignment_grade)
        db.session.commit()

        LTIOutcome.update_user_assignment_grade(assignment, user)

    @classmethod
    def calculate_grades(cls, assignment):
        from . import Answer, CourseRole, Comparison, \
            AnswerComment, AnswerCommentType, LTIOutcome

        student_ids = [course_user.user_id
            for course_user in assignment.course.user_courses
            if course_user.course_role == CourseRole.student]

        # skip if there aren't any students
        if len(student_ids) == 0:
            AssignmentGrade.query \
                .filter_by(assignment_id=assignment.id) \
                .delete()
            LTIOutcome.update_assignment_grades(assignment)
            return

        answer_counts = Answer.query \
            .with_entities(
                Answer.user_id,
                func.count(Answer.user_id).label('answer_count')
            ) \
            .filter_by(
                assignment_id=assignment.id,
                active=True,
                practice=False,
                draft=False
            ) \
            .filter(
                Answer.user_id.in_(student_ids)
            ) \
            .group_by(Answer.user_id) \
            .all()

        comparison_counts = Comparison.query \
            .with_entities(
                Comparison.user_id,
                func.count(Comparison.user_id).label('comparison_count')
            ) \
            .filter_by(
                assignment_id=assignment.id,
                completed=True
            ) \
            .filter(
                Comparison.user_id.in_(student_ids)
            ) \
            .group_by(Comparison.user_id) \
            .all()

        self_evaluation_counts = AnswerComment.query \
            .with_entities(
                AnswerComment.user_id,
                func.count(AnswerComment.user_id).label('self_evaluation_count')
            ) \
            .join("answer") \
            .filter(and_(
                AnswerComment.active == True,
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.draft == False,
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                AnswerComment.user_id.in_(student_ids)
            )) \
            .group_by(AnswerComment.user_id) \
            .all()

        assignment_grades = AssignmentGrade.get_assignment_grades(assignment)
        new_assignment_grades = []
        for student_id in student_ids:
            answer_count = next((result.answer_count for result in answer_counts
                if result.user_id == student_id
            ), 0)

            comparison_count = next((result.comparison_count for result in comparison_counts
                if result.user_id == student_id
            ), 0)
            comparison_count = comparison_count / assignment.criteria_count if assignment.criteria_count > 0 else 0

            self_evaluation_count = next((result.self_evaluation_count for result in self_evaluation_counts
                if result.user_id == student_id
            ), 0)

            grade = _calculate_assignment_grade(assignment,
                answer_count, comparison_count, self_evaluation_count)

            assignment_grade = next((assignment_grade for assignment_grade in assignment_grades
                if assignment_grade.user_id == student_id
            ), None)

            if assignment_grade == None:
                assignment_grade = AssignmentGrade(
                    user_id=student_id,
                    assignment_id=assignment.id
                )
                new_assignment_grades.append(assignment_grade)

            assignment_grade.grade = grade

        db.session.add_all(assignment_grades + new_assignment_grades)
        db.session.commit()

        LTIOutcome.update_assignment_grades(assignment)

def _calculate_assignment_grade(assignment, answer_count, comparison_count, self_evaulation_count):
    grade = 0.0
    total_grade_weight = 0.0

    # calculate answer portion of grade
    answer_grade = 1.0 if answer_count >= 1 else 0.0
    grade += answer_grade * float(assignment.answer_grade_weight)
    total_grade_weight += float(assignment.answer_grade_weight)

    # calculate comparison portion of grade
    if comparison_count > assignment.total_comparisons_required:
        comparison_count = assignment.total_comparisons_required
    comparison_grade = float(comparison_count) / float(assignment.total_comparisons_required) if assignment.number_of_comparisons > 0 else 1.0
    grade += comparison_grade * float(assignment.comparison_grade_weight)
    total_grade_weight += float(assignment.comparison_grade_weight)

    # calculate self evaluation portion of grade if enabled
    if assignment.enable_self_evaluation:
        self_evaulation_grade = 1.0 if self_evaulation_count >= 1 else 0.0
        grade += self_evaulation_grade * float(assignment.self_evaluation_grade_weight)
        total_grade_weight += float(assignment.self_evaluation_grade_weight)

    # divide by total_grade_weight to get the final grade in range: [0.0, 1.0]
    return grade / total_grade_weight if total_grade_weight > 0 else 0.0