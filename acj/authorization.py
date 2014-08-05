from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE, DELETE
from flask_bouncer import ensure
from flask_login import current_user
from werkzeug.exceptions import Unauthorized, Forbidden
from .models import Courses, CoursesAndUsers, Users, UserTypesForCourse, UserTypesForSystem, Posts, \
	PostsForQuestions, PostsForAnswers, PostsForComments, \
	PostsForAnswersAndPostsForComments, PostsForQuestionsAndPostsForComments, Judgements


def define_authorization(user, they):
	"""
	Sets up user permissions for Flask-Bouncer
	"""
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
		they.can(CREATE, Users)

	# users can edit and read their own user account
	they.can(READ, Users, id=user.id)
	they.can(EDIT, Users, id=user.id)
	# they can also look at their own course enrolments
	they.can(READ, CoursesAndUsers, users_id=user.id)

	# Assign permissions based on course roles
	# give access to courses the user is enroled in
	for entry in user.coursesandusers:
		course = entry.course
		they.can(READ, Courses, id=course.id)
		they.can(READ, PostsForQuestions, courses_id=course.id)
		they.can((READ, CREATE), PostsForAnswers, courses_id=course.id)
		they.can((EDIT, DELETE), PostsForAnswers, users_id=user.id)
		they.can((READ, CREATE), PostsForQuestionsAndPostsForComments, courses_id=course.id)
		they.can((EDIT, DELETE), PostsForQuestionsAndPostsForComments, users_id=user.id)
		they.can((READ, CREATE), PostsForAnswersAndPostsForComments, courses_id=course.id)
		they.can((EDIT, DELETE), PostsForAnswersAndPostsForComments, users_id=user.id)
		# instructors can modify the course and enrolment
		if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR:
			they.can(EDIT, Courses, id=course.id)
			they.can((READ, EDIT), CoursesAndUsers, courses_id=course.id)
		# instructors and ta can do anything they want to posts
		if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR or \
			entry.usertypeforcourse.name == UserTypesForCourse.TYPE_TA:
			they.can(MANAGE, PostsForQuestions, courses_id=course.id)
			they.can(MANAGE, PostsForAnswers, courses_id=course.id)
			they.can(MANAGE, PostsForQuestionsAndPostsForComments, courses_id=course.id)
			they.can(MANAGE, PostsForAnswersAndPostsForComments, courses_id=course.id)
		# only students can submit judgements for now
		if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_STUDENT:
			they.can(CREATE, Judgements, courses_id=course.id)

# Tell the client side about a user's permissions.
# This is necessarily more simplified than Flask-Bouncer's implementation.
# I'm hoping that we don't need fine grained permission checking to the
# level of individual entries. This is only going to be at a coarse level
# of models.
# Note that it looks like Flask-Bouncer judges a user to have permission
# on an model if they're allowed to operate on one instance of it.
# E.g.: A user who can only EDIT their own User object would have
# ensure(READ, Users) return True
def get_logged_in_user_permissions():
	user = Users.query.get(current_user.id)
	require(READ, user)
	permissions = {}
	models = {
		Courses.__name__ : Courses,
		Users.__name__ : Users,
		PostsForQuestions.__name__: PostsForQuestions
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

	return permissions

def allow(operation, target):
	"""
	This duplicates bouncer's can() operation since flask-bouncer doesn't implement it.
	Named allow() to avoid namespace confusion with bouncer.
	"""
	try:
		ensure(operation, target)
		return True
	except Unauthorized:
		return False

def require(operation, target):
	"""
	This is basically Flask-Bouncer's ensure except it throws a 403 instead of a 401
	if the permission check fails. A 403 is more accurate since authentication would
	not help and it would prevent the login box from showing up. Named require() to avoid
	confusion with Flask-Bouncer
	:param action: same as Flask-Bouncer's ensure
	:param subject: same as Flask-Bouncer's ensure
	:return:same as Flask-Bouncer's ensure
	"""
	try:
		ensure(operation,target)
	except Unauthorized as e:
		raise Forbidden(e.get_description())

def is_user_access_restricted(user):
	"""
	determine if the current user has full view of another user
	This provides a measure of anonymity among students, while instructors and above can see real names.
	"""
	# Determine if the logged in user can view full info on the target user
	access_restricted = not allow(READ, user)
	if access_restricted:
		enrolments = CoursesAndUsers.query.filter_by(users_id=user.id).all()
		# if the logged in user can edit the target user's enrolments, then we let them see full info
		for enrolment in enrolments:
			if allow(EDIT, enrolment):
				access_restricted = False
				break

	return access_restricted

