# mixins
from .mixins import ActiveMixin, DefaultTableMixin, WriteTrackingMixin

# models & enums
from .activity_log import ActivityLog
from .answer_comment import AnswerComment
from .answer import Answer
from .assignment_criteria import AssignmentCriteria
from .assignment_comment import AssignmentComment
from .comparison import Comparison
from .assignment import Assignment
from .course import Course
from .course_role import CourseRole
from .criteria import Criteria
from .file import File
from .score import Score
from .system_role import SystemRole
from .user import User
from .user_course import UserCourse


from acj.core import db
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db.metadata.naming_convention = convention