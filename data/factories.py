import datetime

import factory
import factory.fuzzy

from factory.alchemy import SQLAlchemyModelFactory

from acj.core import db
from acj.models import Course, User, CourseRole, SystemRole, Criterion, \
    UserCourse, AssignmentCriterion, Assignment, Score, Answer, AssignmentComment, \
    AnswerComment, Comparison, AnswerCommentType, ComparisonExample, \
    LTIConsumer, LTIContext, LTIResourceLink, LTIMembership, LTIUser, LTIUserResourceLink

from oauthlib.common import generate_token


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
    year = 2015
    term = "Winter"
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


class CriterionFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Criterion
    FACTORY_SESSION = db.session
    name = factory.Sequence(lambda n: u'criterion %d' % n)
    description = factory.Sequence(lambda n: u'This is criterion %d' % n)
    default = True

class AssignmentCriterionFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = AssignmentCriterion
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
    rank_display_limit = 10
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ScoreFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Score
    FACTORY_SESSION = db.session
    score = 5

    assignment_id = 1
    answer_id = 1
    criterion_id = 1


class AnswerFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Answer
    FACTORY_SESSION = db.session
    assignment_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    draft = False
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
    draft = False
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ComparisonFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Comparison
    FACTORY_SESSION = db.session

    assignment_id = 1
    criterion_id = 1
    course_id = 1
    user_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

class ComparisonExampleFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = ComparisonExample
    FACTORY_SESSION = db.session

    assignment_id = 1
    course_id = 1
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

class LTIConsumerFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIConsumer
    FACTORY_SESSION = db.session

    oauth_consumer_key = generate_token()
    oauth_consumer_secret = generate_token()

    lti_version = "LTI-1p0"

class LTIContextFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIContext
    FACTORY_SESSION = db.session

    lti_consumer_id = 1
    context_id = factory.Sequence(lambda n: u'course-v1:LTI%d' % n)

class LTIResourceLinkFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIResourceLink
    FACTORY_SESSION = db.session

    lti_consumer_id = 1
    resource_link_id = factory.Sequence(lambda n: u'unique_resourse_link_id_%d' % n)

class LTIUserFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIUser
    FACTORY_SESSION = db.session

    lti_consumer_id = 1
    user_id = factory.Sequence(lambda n: u'unique_user_id_%d' % n)
    system_role = SystemRole.student

class LTIMembershipFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIMembership
    FACTORY_SESSION = db.session

    lti_context_id = 1
    lti_user_id = 1
    roles = "Student"
    course_role = CourseRole.student

class LTIUserResourceLinkFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = LTIUserResourceLink
    FACTORY_SESSION = db.session

    lti_resource_link_id = 1
    lti_user_id = 1
    roles = "Student"
    course_role = CourseRole.student