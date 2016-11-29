# mixins
from .mixins import ActiveMixin, DefaultTableMixin, WriteTrackingMixin, UUIDMixin

# enums
from .custom_types import AnswerCommentType, CourseRole, PairingAlgorithm, \
    ScoringAlgorithm, SystemRole, ThirdPartyType

# models
from .activity_log import ActivityLog
from .answer_comment import AnswerComment
from .answer import Answer
from .assignment_criterion import AssignmentCriterion
from .assignment_comment import AssignmentComment
from .comparison import Comparison
from .comparison_example import ComparisonExample
from .assignment_grade import AssignmentGrade
from .assignment import Assignment
from .course_grade import CourseGrade
from .course import Course
from .criterion import Criterion
from .file import File
from .score import Score
from .user import User
from .user_course import UserCourse
from .third_party_user import ThirdPartyUser
from .xapi_log import XAPILog

# LTI models
from .lti_models import LTIConsumer, LTIContext, LTIMembership, \
    LTIResourceLink, LTIUser, LTIUserResourceLink, LTINonce, LTIOutcome

from compair.core import db
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db.metadata.naming_convention = convention