import datetime

import factory
import factory.fuzzy

from factory.alchemy import SQLAlchemyModelFactory

from acj.core import db
from acj.models import Course, User, CourseRole, SystemRole, Criteria, \
    UserCourse, AssignmentCriteria, Assignment, Score, Answer, AssignmentComment, \
    AnswerComment, Comparison, AnswerCommentType


class UserFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = User
    FACTORY_SESSION = db.session

    username = factory.Sequence(lambda n: u'user%d' % n)
    firstname = factory.fuzzy.FuzzyText(length=4)
    lastname = factory.fuzzy.FuzzyText(length=4)
    displayname = factory.fuzzy.FuzzyText(length=8)
    email = factory.fuzzy.FuzzyText(length=8)
    student_number = factory.fuzzy.FuzzyText(length=8)
    password = 'password'
    system_role = SystemRole.instructor


class CourseFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Course
    FACTORY_SESSION = db.session

    name = factory.Sequence(lambda n: u'TestCourse%d' % n)
    description = factory.fuzzy.FuzzyText(length=36)
    #start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    #end_date = datetime.datetime.now() + datetime.timedelta(days=7)


class UserCourseFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = UserCourse
    FACTORY_SESSION = db.session

    course_id = 1
    user_id = 1
    course_role = CourseRole.instructor
    group_name = None


class CriteriaFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Criteria
    FACTORY_SESSION = db.session
    name = factory.Sequence(lambda n: u'criteria %d' % n)
    description = factory.Sequence(lambda n: u'This is criteria %d' % n)
    default = True

class AssignmentCriteriaFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = AssignmentCriteria
    FACTORY_SESSION = db.session
    active = True


class AssignmentFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Assignment
    FACTORY_SESSION = db.session

    user_id = 1
    course_id = 1
    name = factory.Sequence(lambda n: u'this is a name for assignment %d' % n)
    description = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    answer_start = datetime.datetime.now() - datetime.timedelta(days=7)
    answer_end = datetime.datetime.now() + datetime.timedelta(days=7)
    compare_start = None
    compare_end = None
    number_of_comparisons = 3
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ScoreFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Score
    FACTORY_SESSION = db.session
    score = 5

    assignment_id = 1
    answer_id = 1
    criteria_id = 1


class AnswerFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Answer
    FACTORY_SESSION = db.session
    assignment_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class AssignmentCommentFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = AssignmentComment
    FACTORY_SESSION = db.session
    assignment_id = 1

    course_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class AnswerCommentFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = AnswerComment
    FACTORY_SESSION = db.session
    answer_id = 1
    comment_type = AnswerCommentType.private

    course_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ComparisonFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Comparison
    FACTORY_SESSION = db.session

    assignment_id = 1
    criteria_id = 1
    course_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))
