"""
	Fixture package, also contain default seed data to be populated
"""

from fixture import SQLAlchemyFixture, DataSet, NamedDataStyle
from acj.models import Users, UserTypesForCourse, UserTypesForSystem


def get_dbfixture(db):
	return SQLAlchemyFixture(engine=db.engine, env=globals(), style=NamedDataStyle())


class UserTypesForCourseData(DataSet):
	class Dropped:
		name = UserTypesForCourse.TYPE_DROPPED

	class Student:
		name = UserTypesForCourse.TYPE_STUDENT

	class Ta:
		name = UserTypesForCourse.TYPE_TA

	class Instructor:
		name = UserTypesForCourse.TYPE_INSTRUCTOR


class UserTypesForSystemData(DataSet):
	class Normal:
		name = UserTypesForSystem.TYPE_NORMAL

	class Instructor:
		name = UserTypesForSystem.TYPE_INSTRUCTOR

	class SysAdmin:
		name = UserTypesForSystem.TYPE_SYSADMIN


class UsersData(DataSet):
	class Root:
		username = 'root'
		password = 'password'
		displayname = 'root'
		usertypeforsystem = UserTypesForSystemData.SysAdmin


all_data = (UserTypesForSystemData, UserTypesForCourseData, UsersData)