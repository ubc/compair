import factory
from factory.alchemy import SQLAlchemyModelFactory
from acj.core import db
from acj.models import Courses, Users, UserTypesForCourse, UserTypesForSystem, Criteria

__author__ = 'compass'


class UserFactory(SQLAlchemyModelFactory):
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

class CourseFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = Courses
	FACTORY_SESSION = db.session

	name = factory.Sequence(lambda n: u'course%d' % n)
	description = "Some Course Description"
	available = True

class CriteriaFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = Criteria
	FACTORY_SESSION = db.session
	name = "Which is better?"
	description = "<p>Choose the response that you think is the better of the two.</p>"
