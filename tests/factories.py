import datetime
import factory
from factory.alchemy import SQLAlchemyModelFactory
from acj.core import db
from acj.models import Courses, Users, UserTypesForCourse, UserTypesForSystem, Criteria, CoursesAndUsers, Posts, \
	PostsForQuestions, PostsForAnswers

__author__ = 'compass'


class UsersFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = Users
	FACTORY_SESSION = db.session

	username = factory.Sequence(lambda n: u'user%d' % n)
	firstname = 'John'
	lastname = 'Smith'
	displayname = factory.Sequence(lambda n: u'John Smith %d' % n)
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

	name = factory.Sequence(lambda n: u'course%d' % n)
	description = "Some Course Description"
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
	name = "Which is better?"
	description = "<p>Choose the response that you think is the better of the two.</p>"

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

class PostsForAnswersFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = PostsForAnswers
	FACTORY_SESSION = db.session
	posts_id = 1
	postsforquestions_id = 1
