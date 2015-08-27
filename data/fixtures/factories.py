import datetime

import factory
import factory.fuzzy

from factory.alchemy import SQLAlchemyModelFactory

from acj.core import db
from acj.models import Courses, Users, UserTypesForCourse, UserTypesForSystem, Criteria, CoursesAndUsers, Posts, \
    PostsForQuestions, PostsForAnswers, PostsForComments, \
    PostsForQuestionsAndPostsForComments, PostsForAnswersAndPostsForComments, CriteriaAndCourses, AnswerPairings, \
    Judgements, PostsForJudgements, Groups, GroupsAndUsers, CriteriaAndPostsForQuestions, SelfEvaluationTypes, Scores


class UsersFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Users
    FACTORY_SESSION = db.session

    username = factory.Sequence(lambda n: u'user%d' % n)
    firstname = factory.fuzzy.FuzzyText(length=4)
    lastname = factory.fuzzy.FuzzyText(length=4)
    displayname = factory.fuzzy.FuzzyText(length=8)
    email = factory.fuzzy.FuzzyText(length=8)
    student_no = factory.fuzzy.FuzzyText(length=8)
    password = 'password'
    usertypesforsystem_id = 2


class UserTypesForCourseFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = UserTypesForCourse
    FACTORY_SESSION = db.session

    name = factory.Iterator([
        UserTypesForCourse.TYPE_DROPPED,
        UserTypesForCourse.TYPE_INSTRUCTOR,
        UserTypesForCourse.TYPE_TA,
        UserTypesForCourse.TYPE_STUDENT
    ])


class UserTypesForSystemFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = UserTypesForSystem
    FACTORY_SESSION = db.session

    name = factory.Iterator([
        UserTypesForSystem.TYPE_NORMAL,
        UserTypesForSystem.TYPE_INSTRUCTOR,
        UserTypesForSystem.TYPE_SYSADMIN,
    ])


class CoursesFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Courses
    FACTORY_SESSION = db.session

    name = factory.Sequence(lambda n: u'TestCourse%d' % n)
    description = factory.fuzzy.FuzzyText(length=36)
    available = True


class CoursesAndUsersFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = CoursesAndUsers
    FACTORY_SESSION = db.session

    courses_id = 1
    users_id = 1
    usertypesforcourse_id = 2


class CriteriaFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Criteria
    FACTORY_SESSION = db.session
    name = factory.Sequence(lambda n: u'criteria %d' % n)
    description = factory.Sequence(lambda n: u'This is criteria %d' % n)


class CriteriaAndCoursesFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = CriteriaAndCourses
    FACTORY_SESSION = db.session


class CriteriaAndPostsForQuestionsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = CriteriaAndPostsForQuestions
    FACTORY_SESSION = db.session
    active = True


class PostsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Posts
    FACTORY_SESSION = db.session
    courses_id = 1
    users_id = 1
    content = factory.Sequence(lambda n: u'this is some content for post %d' % n)
    # Make sure created dates are unique. Created dates are used to sort posts, if we rely on
    # current time as the created date, most posts will be created at the same moment.
    created = factory.Sequence(lambda n: datetime.datetime.fromtimestamp(1404768528 - n))


class PostsForQuestionsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForQuestions
    FACTORY_SESSION = db.session
    posts_id = 1
    title = factory.Sequence(lambda n: u'this is a title for question %d' % n)
    answer_start = datetime.datetime.now() - datetime.timedelta(days=7)
    answer_end = datetime.datetime.now() + datetime.timedelta(days=7)
    num_judgement_req = 3


class ScoreFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Scores
    FACTORY_SESSION = db.session
    score = 5


class PostsForAnswersFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForAnswers
    FACTORY_SESSION = db.session
    posts_id = 1
    questions_id = 1


class PostsForCommentsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForComments
    FACTORY_SESSION = db.session
    posts_id = 1


class PostsForQuestionsAndPostsForCommentsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForQuestionsAndPostsForComments
    FACTORY_SESSION = db.session
    questions_id = 1
    comments_id = 1


class PostsForAnswersAndPostsForCommentsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForAnswersAndPostsForComments
    FACTORY_SESSION = db.session
    answers_id = 1
    comments_id = 1


class AnswerPairingsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = AnswerPairings
    FACTORY_SESSION = db.session


class JudgementsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Judgements
    FACTORY_SESSION = db.session


class PostsForJudgementsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = PostsForJudgements
    FACTORY_SESSION = db.session


class GroupsFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Groups
    FACTORY_SESSION = db.session
    name = factory.fuzzy.FuzzyText(length=6)


class GroupsAndUsersFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = GroupsAndUsers
    FACTORY_SESSION = db.session


class SelfEvaluationTypesFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = SelfEvaluationTypes
    FACTORY_SESSION = db.session
