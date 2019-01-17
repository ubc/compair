import dateutil.parser
import datetime
import pytz

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from sqlalchemy import func, select, and_, or_, join
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType
from sqlalchemy.ext.orderinglist import ordering_list

from . import *

from compair.core import db

class Assignment(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    __tablename__ = 'assignment'

    # table columns
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete="SET NULL"), nullable=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    answer_start = db.Column(db.DateTime(timezone=True))
    answer_end = db.Column(db.DateTime(timezone=True))
    compare_start = db.Column(db.DateTime(timezone=True), nullable=True)
    compare_end = db.Column(db.DateTime(timezone=True), nullable=True)
    self_eval_start = db.Column(db.DateTime(timezone=True), nullable=True)
    self_eval_end = db.Column(db.DateTime(timezone=True), nullable=True)
    self_eval_instructions = db.Column(db.Text, nullable=True)
    number_of_comparisons = db.Column(db.Integer, nullable=False)
    students_can_reply = db.Column(db.Boolean(), default=False, nullable=False)
    enable_self_evaluation = db.Column(db.Boolean(), default=False, nullable=False)
    enable_group_answers = db.Column(db.Boolean(), default=False, nullable=False)
    scoring_algorithm = db.Column(EnumType(ScoringAlgorithm), nullable=True, default=ScoringAlgorithm.elo)
    pairing_algorithm = db.Column(EnumType(PairingAlgorithm), nullable=True, default=PairingAlgorithm.random)
    rank_display_limit = db.Column(db.Integer, nullable=True)
    educators_can_compare = db.Column(db.Boolean(), default=False, nullable=False)
    answer_grade_weight = db.Column(db.Integer, default=1, nullable=False)
    comparison_grade_weight = db.Column(db.Integer, default=1, nullable=False)
    self_evaluation_grade_weight = db.Column(db.Integer, default=1, nullable=False)
    peer_feedback_prompt = db.Column(db.Text)

    # relationships
    # user via User Model
    # course via Course Model
    # file via File Model

    # assignment many-to-many criterion with association assignment_criteria
    assignment_criteria = db.relationship("AssignmentCriterion", back_populates="assignment",
        order_by=AssignmentCriterion.position.asc(), collection_class=ordering_list('position', count_from=0))

    answers = db.relationship("Answer", backref="assignment", lazy="dynamic",
        order_by=Answer.submission_date.desc())
    comparisons = db.relationship("Comparison", backref="assignment", lazy="dynamic")
    comparison_examples = db.relationship("ComparisonExample", backref="assignment", lazy="dynamic")
    scores = db.relationship("AnswerScore", backref="assignment", lazy="dynamic")
    criteria_scores = db.relationship("AnswerCriterionScore", backref="assignment", lazy="dynamic")
    grades = db.relationship("AssignmentGrade", backref="assignment", lazy='dynamic')

    # lti
    lti_resource_links = db.relationship("LTIResourceLink", backref="compair_assignment", lazy='dynamic')

    # hybrid and other functions
    course_uuid = association_proxy('course', 'uuid')

    user_avatar = association_proxy('user', 'avatar')
    user_uuid = association_proxy('user', 'uuid')
    user_displayname = association_proxy('user', 'displayname')
    user_student_number = association_proxy('user', 'student_number')
    user_fullname = association_proxy('user', 'fullname')
    user_fullname_sortable = association_proxy('user', 'fullname_sortable')
    user_system_role = association_proxy('user', 'system_role')

    lti_course_linked = association_proxy('course', 'lti_linked')

    @hybrid_property
    def lti_linked(self):
        return self.lti_resource_link_count > 0

    @hybrid_property
    def criteria(self):
        criteria = []
        for assignment_criterion in self.assignment_criteria:
            if assignment_criterion.active and assignment_criterion.criterion.active:
                criterion = assignment_criterion.criterion
                criterion.weight = assignment_criterion.weight
                criteria.append(criterion)
        return criteria

    @hybrid_property
    def compared(self):
        return self.all_compare_count > 0

    @hybrid_property
    def answered(self):
        return self.comparable_answer_count > 0

    def completed_comparison_count_for_user(self, user_id):
        return self.comparisons \
            .filter_by(
                user_id=user_id,
                completed=True
            ) \
            .count()

    def draft_comparison_count_for_user(self, user_id):
        return self.comparisons \
            .filter_by(
                user_id=user_id,
                draft=True
            ) \
            .count()

    def clear_lti_links(self):
        for lti_resource_link in self.lti_resource_links.all():
            lti_resource_link.compair_assignment_id = None

    @hybrid_property
    def available(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now

    @hybrid_property
    def answer_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        return answer_start <= now < answer_end

    @hybrid_property
    def answer_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        grace = self.answer_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now < grace

    @hybrid_property
    def compare_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        if not self.compare_start:
            return now >= answer_end
        else:
            return self.compare_start.replace(tzinfo=pytz.utc) <= now < self.compare_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def compare_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        if self.compare_start and self.compare_end:
            grace = self.compare_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
            compare_start = self.compare_start.replace(tzinfo=pytz.utc)
            return compare_start <= now < grace
        else:
            answer_end = self.answer_end.replace(tzinfo=pytz.utc)
            return now >= answer_end

    @hybrid_property
    def after_comparing(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        # compare period not set
        if not self.compare_start:
            return now >= answer_end
        # compare period is set
        else:
            return now >= self.compare_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def self_eval_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        if not self.enable_self_evaluation:
            return False
        elif self.self_eval_start:
            return self.self_eval_start.replace(tzinfo=pytz.utc) <= now < self.self_eval_end.replace(tzinfo=pytz.utc)
        else:
            if self.compare_start:
                return now >= self.compare_start.replace(tzinfo=pytz.utc)
            else:
                return now >= self.answer_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def self_eval_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        if not self.enable_self_evaluation:
            return False
        elif self.self_eval_start:
            grace = self.self_eval_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
            return self.self_eval_start.replace(tzinfo=pytz.utc) <= now < grace
        else:
            if self.compare_start:
                return now >= self.compare_start.replace(tzinfo=pytz.utc)
            else:
                return now >= self.answer_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def evaluation_count(self):
        return self.compare_count + self.self_evaluation_count

    @hybrid_property
    def total_comparisons_required(self):
        return self.number_of_comparisons + self.comparison_example_count

    @hybrid_property
    def total_steps_required(self):
        return self.total_comparisons_required + (1 if self.enable_self_evaluation else 0)

    def calculate_grade(self, user):
        from . import AssignmentGrade
        AssignmentGrade.calculate_grade(self, user)

    def calculate_group_grade(self, group):
        from . import AssignmentGrade
        AssignmentGrade.calculate_group_grade(self, group)

    def calculate_grades(self):
        from . import AssignmentGrade
        AssignmentGrade.calculate_grades(self)

    @classmethod
    def validate_periods(cls, course_start, course_end, answer_start, answer_end, compare_start, compare_end, self_eval_start, self_eval_end):
        # validate answer period
        if answer_start == None:
            return (False, "No answer period start time provided.")
        elif answer_end == None:
            return (False, "No answer period end time provided.")

        course_start = course_start.replace(tzinfo=pytz.utc) if course_start else None
        course_end = course_end.replace(tzinfo=pytz.utc) if course_end else None
        answer_start = answer_start.replace(tzinfo=pytz.utc)
        answer_end = answer_end.replace(tzinfo=pytz.utc)

        # course start <= answer start < answer end <= course end
        if course_start and course_start > answer_start:
            return (False, "Answer period start time must be after the course start time.")
        elif answer_start >= answer_end:
            return (False, "Answer period end time must be after the answer start time.")
        elif course_end and course_end < answer_end:
            return (False, "Answer period end time must be before the course end time.")

        # validate compare period
        if compare_start == None and compare_end != None:
            return (False, "No compare period start time provided.")
        elif compare_start != None and compare_end == None:
            return (False, "No compare period end time provided.")
        elif compare_start != None and compare_end != None:
            compare_start = compare_start.replace(tzinfo=pytz.utc)
            compare_end = compare_end.replace(tzinfo=pytz.utc)

            # answer start < compare start < compare end <= course end
            if answer_start > compare_start:
                return (False, "Compare period start time must be after the answer start time.")
            elif compare_start > compare_end:
                return (False, "Compare period end time must be after the compare start time.")
            elif course_end and course_end < compare_end:
                return (False, "Compare period end time must be before the course end time.")

        # validate self-eval period
        if self_eval_start == None and self_eval_end != None:
            return (False, "No self-evaluation start time provided.")
        elif self_eval_start != None and self_eval_end == None:
            return (False, "No self-evaluation end time provided.")
        elif self_eval_start != None and self_eval_end != None:
            self_eval_start = self_eval_start.replace(tzinfo=pytz.utc)
            self_eval_end = self_eval_end.replace(tzinfo=pytz.utc)

            # self_eval start < self_eval end <= course end
            if self_eval_start > self_eval_end:
                return (False, "Self-evaluation end time must be after the self-evaluation start time.")
            elif course_end and course_end < self_eval_end:
                return (False, "Self-evaluation end time must be before the course end time.")

            # if comparison period defined: compare start < self_eval start
            if compare_start != None and compare_start > self_eval_start:
                return (False, "Self-evaluation start time must be after the compare start time.")
            # else: answer end < self_eval start
            # elif compare_start == None and answer_end >= self_eval_start:
            #     return (False, "Self-evaluation start time must be after the answer end time.")

        return (True, None)

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Assignment Unavailable"
        if not message:
            message = "Sorry, this assignment was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Assignment Unavailable"
        if not message:
            message = "Sorry, this assignment was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        from . import UserCourse, CourseRole, LTIResourceLink, Group
        super(cls, cls).__declare_last__()

        cls.answer_count = column_property(
            select([func.count(Answer.id)]).
            select_from(
                join(Answer, UserCourse, UserCourse.user_id == Answer.user_id, isouter=True).
                join(Group, Group.id == Answer.group_id, isouter=True)
            ).
            where(and_(
                Answer.assignment_id == cls.id,
                Answer.active == True,
                Answer.draft == False,
                Answer.practice == False,
                or_(
                    and_(
                        UserCourse.course_id == cls.course_id,
                        UserCourse.course_role != CourseRole.dropped,
                        UserCourse.id != None
                    ),
                    and_(
                        Group.course_id == cls.course_id,
                        Group.active == True,
                        Group.id != None
                    ),
                )
            )),
            deferred=True,
            group="counts"
        )

        cls.student_answer_count = column_property(
            select([func.count(Answer.id)]).
            select_from(
                join(Answer, UserCourse, UserCourse.user_id == Answer.user_id, isouter=True).
                join(Group, Group.id == Answer.group_id, isouter=True)
            ).
            where(and_(
                Answer.assignment_id == cls.id,
                Answer.active == True,
                Answer.draft == False,
                Answer.practice == False,
                or_(
                    and_(
                        UserCourse.course_id == cls.course_id,
                        UserCourse.course_role == CourseRole.student,
                        UserCourse.id != None
                    ),
                    and_(
                        Group.course_id == cls.course_id,
                        Group.active == True,
                        Group.id != None
                    ),
                )
            )),
            deferred=True,
            group="counts"
        )

        # Comparable answer count
        # To be consistent with student_answer_count, we are not counting
        # answers from sys admin here
        cls.comparable_answer_count = column_property(
            select([func.count(Answer.id)]).
            select_from(
                join(Answer, UserCourse, UserCourse.user_id == Answer.user_id, isouter=True).
                join(Group, Group.id == Answer.group_id, isouter=True)
            ).
            where(and_(
                Answer.assignment_id == cls.id,
                Answer.active == True,
                Answer.draft == False,
                Answer.practice == False,
                Answer.comparable == True,
                or_(
                    and_(
                        UserCourse.course_id == cls.course_id,
                        UserCourse.course_role != CourseRole.dropped,
                        UserCourse.id != None
                    ),
                    and_(
                        Group.course_id == cls.course_id,
                        Group.active == True,
                        Group.id != None
                    ),
                )
            )),
            deferred=True,
            group="counts"
        )

        cls.comparison_example_count = column_property(
            select([func.count(ComparisonExample.id)]).
            where(and_(
                ComparisonExample.assignment_id == cls.id,
                ComparisonExample.active == True
            )),
            deferred=True,
            group="counts"
        )

        cls.all_compare_count = column_property(
            select([func.count(Comparison.id)]).
            where(and_(
                Comparison.assignment_id == cls.id
            )),
            deferred=True,
            group="counts"
        )

        cls.compare_count = column_property(
            select([func.count(Comparison.id)]).
            where(and_(
                Comparison.assignment_id == cls.id,
                Comparison.completed == True
            )),
            deferred=True,
            group="counts"
        )

        cls.self_evaluation_count = column_property(
            select([func.count(AnswerComment.id)]).
            select_from(join(AnswerComment, Answer, AnswerComment.answer_id == Answer.id)).
            where(and_(
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.active == True,
                AnswerComment.answer_id == Answer.id,
                AnswerComment.draft == False,
                Answer.assignment_id == cls.id
            )),
            deferred=True,
            group="counts"
        )

        cls.lti_resource_link_count = column_property(
            select([func.count(LTIResourceLink.id)]).
            where(LTIResourceLink.compair_assignment_id == cls.id),
            deferred=True,
            group="counts"
        )