from bouncer.constants import ALL, MANAGE, EDIT, READ
from acj.models import Courses, CoursesAndUsers, Users, UserTypesForCourse, UserTypesForSystem

def define_authorization(user, they):
	if not user.is_authenticated():
		return # user isn't logged in

	# sysadmin can do anything
	if user.usertypeforsystem.name == UserTypesForSystem.TYPE_SYSADMIN:
		they.can(MANAGE, ALL)

	# users can edit and read their own user account
	they.can(READ, Users, id=user.id)
	they.can(EDIT, Users, id=user.id)
	# they can also look at their own course enrolments
	they.can(READ, CoursesAndUsers, users_id=user.id)

	# give access to courses the user is enroled in
	for entry in user.coursesandusers:
		course_id = entry.course.id
		they.can(READ, Courses, id=course_id)
		if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR:
			they.can(EDIT, Courses, id=course_id)
			they.can(READ, CoursesAndUsers, courses_id=course_id)
			they.can(EDIT, CoursesAndUsers, courses_id=course_id)
