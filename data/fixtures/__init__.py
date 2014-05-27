"""
	Fixture package, also contain default seed data to be populated
"""
from acj.models import UserTypesForCourse, UserTypesForSystem
from tests.factories import UserFactory, UserTypesForCourseFactory, UserTypesForSystemFactory


class DefaultFixture(object):
	COURSE_ROLE_DROP = None
	COURSE_ROLE_INSTRUCTOR = None
	COURSE_ROLE_TA = None
	COURSE_ROLE_STUDENT = None

	SYS_ROLE_NORMAL = None
	SYS_ROLE_INSTRUCTOR = None
	SYS_ROLE_ADMIN = None
	ROOT_USER = None

	def __init__(self):
		DefaultFixture.COURSE_ROLE_DROP = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_DROPPED)
		DefaultFixture.COURSE_ROLE_INSTRUCTOR = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_INSTRUCTOR)
		DefaultFixture.COURSE_ROLE_TA = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_TA)
		DefaultFixture.COURSE_ROLE_STUDENT = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_STUDENT)

		DefaultFixture.SYS_ROLE_NORMAL = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_NORMAL)
		DefaultFixture.SYS_ROLE_INSTRUCTOR = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_INSTRUCTOR)
		DefaultFixture.SYS_ROLE_ADMIN = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_SYSADMIN)
		DefaultFixture.ROOT_USER = UserFactory(
			username='root', password='password', displayname='root',
			usertypeforsystem=DefaultFixture.SYS_ROLE_ADMIN)
