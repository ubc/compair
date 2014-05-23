from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE, DELETE
from flask import Blueprint, jsonify
from flask_bouncer import ensure
from flask_login import login_required, current_user
from werkzeug.exceptions import Unauthorized
from acj.models import Courses, CoursesAndUsers, Users, UserTypesForCourse, UserTypesForSystem

# Server side permissions is taken care of by Flask-Bouncer, which leaves the client side.
# We have to set up an API for the client side to get information about a user's permissions.
authorization_api = Blueprint('authorization_api', __name__)

# Sets up user permissions for Flask-Bouncer
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

# Tell the client side about a user's permissions.
# This is necessarily more simplified than Flask-Bouncer's implementation.
# I'm hoping that we don't need fine grained permission checking to the
# level of individual entries. This is only going to be at a coarse level
# of models.
# Note that it looks like Flask-Bouncer judges a user to have permission
# on an model if they're allowed to operate on one instance of it.
# E.g.: A user who can only EDIT their own User object would have
# ensure(READ, Users) return True
@authorization_api.route('/')
@login_required
def get_logged_in_user_permissions():
	user = Users.query.get(current_user.id)
	ensure(READ, user)
	permissions = {}
	models = {
		"Courses" : Courses,
		"Users" : Users
	}
	operations = {
		MANAGE,
		READ,
		EDIT,
		CREATE,
		DELETE
	}
	for model_name, model in models.items():
		# create entry if not already exists
		if not model_name in permissions:
			permissions[model_name] = {}
		# obtain permission values for each operation
		for operation in operations:
			permissions[model_name][operation] = True
			try:
				ensure(operation, model)
			except Unauthorized:
				permissions[model_name][operation] = False

	return jsonify(permissions)

