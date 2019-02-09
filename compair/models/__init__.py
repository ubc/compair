# mixins
from .mixins import ActiveMixin, AttemptMixin, DefaultTableMixin, \
    WriteTrackingMixin, UUIDMixin

# enums
from .custom_types import AnswerCommentType, CourseRole, PairingAlgorithm, \
    ScoringAlgorithm, SystemRole, ThirdPartyType, WinningAnswer, \
    EmailNotificationMethod, AssignmentNotificationType

# models
from .activity_log import ActivityLog
from .answer_comment import AnswerComment
from .answer import Answer
from .assignment_criterion import AssignmentCriterion
from .comparison import Comparison
from .comparison_criterion import ComparisonCriterion
from .comparison_example import ComparisonExample
from .assignment_grade import AssignmentGrade
from .assignment import Assignment
from .assignment_notification import AssignmentNotification
from .course_grade import CourseGrade
from .course import Course
from .criterion import Criterion
from .file import File
from .group import Group
from .answer_score import AnswerScore
from .answer_criterion_score import AnswerCriterionScore
from .user import User
from .user_course import UserCourse
from .third_party_user import ThirdPartyUser

# learning record models
from .learning_records import CaliperLog, XAPILog

# LTI models
from .lti_models import LTIConsumer, LTIContext, LTIMembership, \
    LTIResourceLink, LTIUser, LTIUserResourceLink, LTINonce, LTIOutcome

from .kaltura_models import KalturaMedia

from compair.core import db
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db.metadata.naming_convention = convention