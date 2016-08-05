import datetime

import factory
import factory.fuzzy

from acj.core import db
from acj.models import Course, User, CourseRole, SystemRole, Criterion, \
    UserCourse, AssignmentCriterion, Assignment, Score, Answer, AssignmentComment, \
    AnswerComment, Comparison, AnswerCommentType, ComparisonExample


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    username = factory.Sequence(lambda n: u'user%d' % n)
    firstname = factory.fuzzy.FuzzyText(length=4)
    lastname = factory.fuzzy.FuzzyText(length=4)
    displayname = factory.fuzzy.FuzzyText(length=8)
    email = factory.fuzzy.FuzzyText(length=8)
    student_number = factory.fuzzy.FuzzyText(length=8)
    password = 'password'
    system_role = SystemRole.instructor


class CourseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Course
        sqlalchemy_session = db.session

    name = factory.Sequence(lambda n: u'TestCourse%d' % n)
    year = 2015
    term = "Winter"
    description = factory.fuzzy.FuzzyText(length=36)
    #start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    #end_date = datetime.datetime.now() + datetime.timedelta(days=7)


class UserCourseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserCourse
        sqlalchemy_session = db.session

    course = factory.SubFactory(CourseFactory)
    user = factory.SubFactory(UserFactory)
    course_role = CourseRole.instructor
    group_name = None


class CriterionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Criterion
        sqlalchemy_session = db.session

    name = factory.Sequence(lambda n: u'criterion %d' % n)
    description = factory.Sequence(lambda n: u'This is criterion %d' % n)
    default = True


class AssignmentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Assignment
        sqlalchemy_session = db.session

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
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

class AssignmentCriterionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AssignmentCriterion
        sqlalchemy_session = db.session

    criterion = factory.SubFactory(CriterionFactory)
    assignment = factory.SubFactory(AssignmentFactory)
    active = True


class AnswerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Answer
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    draft = False
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

class ScoreFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Score
        sqlalchemy_session = db.session

    score = 5

    assignment = factory.SubFactory(AssignmentFactory)
    answer = factory.SubFactory(AnswerFactory)
    criterion = factory.SubFactory(CriterionFactory)


class AssignmentCommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AssignmentComment
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class AnswerCommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AnswerComment
        sqlalchemy_session = db.session

    answer = factory.SubFactory(AnswerFactory)
    user = factory.SubFactory(UserFactory)
    comment_type = AnswerCommentType.private
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    draft = False
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ComparisonFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Comparison
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    criterion = factory.SubFactory(CriterionFactory)
    course = factory.SubFactory(CourseFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

class ComparisonExampleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ComparisonExample
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))