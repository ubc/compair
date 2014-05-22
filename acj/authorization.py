from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE
from acj.models import Courses, CoursesAndUsers, Users, UserTypesForCourse, UserTypesForSystem

def define_authorization(user, they):
	if not user.is_authenticated():
		return # user isn't logged in

	# Assign permissions based on system roles
	user_system_role = user.usertypeforsystem.name
	if user_system_role == UserTypesForSystem.TYPE_SYSADMIN:
		# sysadmin can do anything
		they.can(MANAGE, ALL)
	elif user_system_role == UserTypesForSystem.TYPE_INSTRUCTOR:
		# instructors can create courses
		they.can(CREATE, Courses)

	# users can edit and read their own user account
	they.can(READ, Users, id=user.id)
	they.can(EDIT, Users, id=user.id)
	# they can also look at their own course enrolments
	they.can(READ, CoursesAndUsers, users_id=user.id)

	# Assign permissions based on course roles
	# give access to courses the user is enroled in
	for entry in user.coursesandusers:
		course_id = entry.course.id
		they.can(READ, Courses, id=course_id)
		if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR:
			they.can(EDIT, Courses, id=course_id)
			they.can(READ, CoursesAndUsers, courses_id=course_id)
			they.can(EDIT, CoursesAndUsers, courses_id=course_id)
