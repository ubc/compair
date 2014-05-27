import factory
from factory.alchemy import SQLAlchemyModelFactory
from acj.core import db
from acj.models import Users, UserTypesForCourse, UserTypesForSystem

__author__ = 'compass'


class UserFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = Users
	FACTORY_SESSION = db.session

	id = factory.Sequence(lambda n: n)
	username = factory.Sequence(lambda n: u'user%d' % n)
	firstname = 'John'
	lastname = 'Smith'
	displayname = factory.Sequence(lambda n: u'John Smith %d' % n)
	password = 'password'
	usertypesforsystem_id = 2

class UserTypesForCourseFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = UserTypesForCourse
	FACTORY_SESSION = db.session

	id = factory.Sequence(lambda n: n)
	name = factory.Iterator([
		UserTypesForCourse.TYPE_DROPPED,
		UserTypesForCourse.TYPE_INSTRUCTOR,
		UserTypesForCourse.TYPE_TA,
		UserTypesForCourse.TYPE_STUDENT
	])


class UserTypesForSystemFactory(SQLAlchemyModelFactory):
	FACTORY_FOR = UserTypesForSystem
	FACTORY_SESSION = db.session

	id = factory.Sequence(lambda n: n)
	name = factory.Iterator([
		UserTypesForSystem.TYPE_NORMAL,
		UserTypesForSystem.TYPE_INSTRUCTOR,
		UserTypesForSystem.TYPE_SYSADMIN,
	])