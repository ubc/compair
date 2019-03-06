# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import logging

import factory
import factory.fuzzy

from compair.core import db
from compair.models import Course, User, CourseRole, SystemRole, Criterion, File, \
    UserCourse, AssignmentCriterion, Assignment, AnswerScore, AnswerCriterionScore, \
    Answer, AnswerComment, Comparison, ComparisonCriterion, \
    AnswerCommentType, ComparisonExample, EmailNotificationMethod, \
    LTIConsumer, LTIContext, LTIResourceLink, LTIMembership, LTIUser, LTIUserResourceLink, \
    ThirdPartyUser, ThirdPartyType, PairingAlgorithm, Group

# suppress factory_boy debug logging (spits out a lot of text)
# comment out/set log level to debug to see the messages
logging.getLogger("factory").setLevel(logging.WARN)

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    username = factory.Sequence(lambda n: 'userü%d' % n)
    firstname = factory.fuzzy.FuzzyText(length=4, suffix='ü')
    lastname = factory.fuzzy.FuzzyText(length=4, suffix='ü')
    displayname = factory.fuzzy.FuzzyText(length=8, suffix='ü')
    email = factory.fuzzy.FuzzyText(length=8, suffix='ü')
    student_number = factory.fuzzy.FuzzyText(length=8, suffix='ü')
    password = 'password'
    system_role = SystemRole.instructor
    email_notification_method = EmailNotificationMethod.enable


class CourseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Course
        sqlalchemy_session = db.session

    name = factory.Sequence(lambda n: 'TestCourseü%d' % n)
    year = 2015
    term = 'Winterü'
    #start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    #end_date = datetime.datetime.now() + datetime.timedelta(days=7)


class UserCourseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserCourse
        sqlalchemy_session = db.session

    course = factory.SubFactory(CourseFactory)
    user = factory.SubFactory(UserFactory)
    course_role = CourseRole.instructor
    #group = None

class CriterionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Criterion
        sqlalchemy_session = db.session

    name = factory.Sequence(lambda n: 'criterion ü %d' % n)
    description = factory.Sequence(lambda n: 'This is criterion ü %d' % n)
    default = True


class AssignmentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Assignment
        sqlalchemy_session = db.session

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    name = factory.Sequence(lambda n: 'this is a name for assignment ü %d' % n)
    description = factory.Sequence(lambda n: 'this is some content for post ü %d' % n)
    answer_start = datetime.datetime.now() - datetime.timedelta(days=7)
    answer_end = datetime.datetime.now() + datetime.timedelta(days=7)
    compare_start = None
    compare_end = None
    number_of_comparisons = 3
    rank_display_limit = 10
    pairing_algorithm = PairingAlgorithm.adaptive_min_delta
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
    #user = factory.SubFactory(UserFactory)
    #group = factory.SubFactory(GroupFactory)
    content = factory.Sequence(lambda n: 'this is some content for post ü %d' % n)
    draft = False
    # Make sure created / submission dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))
    submission_date = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

    attempt_started = datetime.datetime.now() - datetime.timedelta(minutes=10)
    attempt_ended = datetime.datetime.now() - datetime.timedelta(minutes=5)

class AnswerScoreFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AnswerScore
        sqlalchemy_session = db.session

    score = 5

    assignment = factory.SubFactory(AssignmentFactory)
    answer = factory.SubFactory(AnswerFactory)

class AnswerCriterionScoreFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AnswerCriterionScore
        sqlalchemy_session = db.session

    score = 5

    assignment = factory.SubFactory(AssignmentFactory)
    answer = factory.SubFactory(AnswerFactory)
    criterion = factory.SubFactory(CriterionFactory)

class AnswerCommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AnswerComment
        sqlalchemy_session = db.session

    answer = factory.SubFactory(AnswerFactory)
    user = factory.SubFactory(UserFactory)
    comment_type = AnswerCommentType.private
    content = factory.Sequence(lambda n: 'this is some content for post ü %d' % n)
    draft = False
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

    attempt_started = datetime.datetime.now() - datetime.timedelta(minutes=10)
    attempt_ended = datetime.datetime.now() - datetime.timedelta(minutes=5)


class ComparisonFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Comparison
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    user = factory.SubFactory(UserFactory)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))

    attempt_started = datetime.datetime.now() - datetime.timedelta(minutes=10)
    attempt_ended = datetime.datetime.now() - datetime.timedelta(minutes=5)


class ComparisonCriterionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ComparisonCriterion
        sqlalchemy_session = db.session

    comparison = factory.SubFactory(ComparisonFactory)
    criterion = factory.SubFactory(CriterionFactory)
    content = factory.Sequence(lambda n: 'this is some content for post ü %d' % n)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class ComparisonExampleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ComparisonExample
        sqlalchemy_session = db.session

    assignment = factory.SubFactory(AssignmentFactory)
    # Make sure created dates are unique.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class FileFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = File
        sqlalchemy_session = db.session

    user = factory.SubFactory(UserFactory)

    alias = factory.Sequence(lambda n: 'file ü %d' % n)
    name = factory.Sequence(lambda n: 'file_%d.pdf' % n)

class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Group
        sqlalchemy_session = db.session

    course = factory.SubFactory(CourseFactory)

    name = factory.Sequence(lambda n: 'Group ü %d' % n)

class LTIConsumerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIConsumer
        sqlalchemy_session = db.session

    oauth_consumer_key = factory.Sequence(lambda n: 'oauth_consumer_key_%d' % n)
    oauth_consumer_secret = factory.Sequence(lambda n: 'oauth_consumer_secret_%d' % n)

    lti_version = "LTI-1p0"

class LTIContextFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIContext
        sqlalchemy_session = db.session

    lti_consumer_id = 1
    context_id = factory.Sequence(lambda n: 'course-v1:LTI_%d' % n)
    context_title = factory.Sequence(lambda n: 'this is a title for lti context ü %d' % n)

class LTIResourceLinkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIResourceLink
        sqlalchemy_session = db.session

    lti_consumer_id = 1
    resource_link_id = factory.Sequence(lambda n: 'unique_resourse_link_id_%d' % n)

class LTIUserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIUser
        sqlalchemy_session = db.session

    lti_consumer_id = 1
    user_id = factory.Sequence(lambda n: 'unique_user_id_%d' % n)
    system_role = SystemRole.student

class LTIMembershipFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIMembership
        sqlalchemy_session = db.session

    lti_context_id = 1
    lti_user_id = 1
    roles = 'Student'
    course_role = CourseRole.student

class LTIUserResourceLinkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LTIUserResourceLink
        sqlalchemy_session = db.session

    lti_resource_link_id = 1
    lti_user_id = 1
    roles = 'Student'
    course_role = CourseRole.student

class ThirdPartyUserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ThirdPartyUser
        sqlalchemy_session = db.session

    user = factory.SubFactory(UserFactory)

    unique_identifier = factory.Sequence(lambda n: 'unique_identifier_%d' % n)
    third_party_type = ThirdPartyType.saml