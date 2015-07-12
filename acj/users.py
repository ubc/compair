from flask import Blueprint, current_app
from bouncer.constants import MANAGE, EDIT, CREATE
from flask.ext.restful import Resource, marshal_with, marshal
from flask.ext.restful.reqparse import RequestParser
from flask_login import login_required, current_user
from sqlalchemy.orm import load_only

from sqlalchemy import exc, asc

from . import dataformat
from .authorization import is_user_access_restricted, require, allow
from .core import db, event
from .util import pagination, new_restful_api, get_model_changes
from .models import Users, UserTypesForSystem, Courses, UserTypesForCourse, CoursesAndUsers, \
	PostsForQuestions, Posts

users_api = Blueprint('users_api', __name__)
user_types_api = Blueprint('user_types_api', __name__)
user_course_types_api = Blueprint('user_course_types_api', __name__)

new_user_parser = RequestParser()
new_user_parser.add_argument('username', type=str, required=True)
new_user_parser.add_argument('student_no', type=str)
new_user_parser.add_argument('usertypesforsystem_id', type=int, required=True)
new_user_parser.add_argument('firstname', type=str, required=True)
new_user_parser.add_argument('lastname', type=str, required=True)
new_user_parser.add_argument('displayname', type=str, required=True)
new_user_parser.add_argument('email', type=str)
new_user_parser.add_argument('password', type=str, required=True)

existing_user_parser = RequestParser()
existing_user_parser.add_argument('id', type=int, required=True)
existing_user_parser.add_argument('username', type=str, required=True)
existing_user_parser.add_argument('student_no', type=str)
existing_user_parser.add_argument('usertypesforsystem_id', type=int, required=True)
existing_user_parser.add_argument('firstname', type=str, required=True)
existing_user_parser.add_argument('lastname', type=str, required=True)
existing_user_parser.add_argument('displayname', type=str, required=True)
existing_user_parser.add_argument('email', type=str)

update_password_parser = RequestParser()
update_password_parser.add_argument('oldpassword', type=str, required=True)
update_password_parser.add_argument('newpassword', type=str, required=True)

# events
on_user_modified = event.signal('USER_MODIFIED')
on_user_get = event.signal('USER_GET')
on_user_list_get = event.signal('USER_LIST_GET')
on_user_create = event.signal('USER_CREATE')
on_user_course_get = event.signal('USER_COURSE_GET')
on_user_edit_button_get = event.signal('USER_EDIT_BUTTON_GET')
on_user_password_update = event.signal('USER_PASSWORD_UPDATE')
on_teaching_course_get = event.signal('TEACHING_COURSE_GET')

on_user_types_all_get = event.signal('USER_TYPES_ALL_GET')
on_instructors_get = event.signal('INSTRUCTORS_GET')

on_course_roles_all_get = event.signal('COURSE_ROLES_ALL_GET')
on_users_display_get = event.signal('USER_ALL_GET')


# /user_id
class UserAPI(Resource):
	@login_required
	def get(self, user_id):
		user = Users.query.get_or_404(user_id)
		on_user_get.send(
			self,
			event_name=on_user_get.name,
			user=current_user,
			data={'id': user_id}
		)
		return marshal(user, dataformat.get_users(is_user_access_restricted(user)))

	@login_required
	def post(self, user_id):
		user = Users.query.get_or_404(user_id)
		if is_user_access_restricted(user):
			return {'error': "Sorry, you don't have permission for this action."}, 403
		params = existing_user_parser.parse_args()
		# make sure the user id in the url and the id matches
		if params['id'] != user_id:
			return {"error": "User id does not match URL."}, 400

		if allow(MANAGE, user):
			username = params.get("username", user.username)
			username_exists = Users.query.filter_by(username=username).first()
			if username_exists and username_exists.id != user.id:
				return {"error": "This username already exists. Please pick another."}, 409
			else:
				user.username = username

			student_no = params.get("student_no", user.student_no)
			student_no_exists = Users.query.filter_by(student_no=student_no).first()
			if student_no is not None and student_no_exists and student_no_exists.id != user.id:
				return {"error": "This student number already exists. Please pick another."}, 409
			else:
				user.student_no = student_no

			user.usertypesforsystem_id = params.get("usertypesforsystem_id", user.usertypesforsystem_id)

		user.firstname = params.get("firstname", user.firstname)
		user.lastname = params.get("lastname", user.lastname)
		user.displayname = params.get("displayname", user.displayname)

		user.email = params.get("email", user.email)
		changes = get_model_changes(user)

		restrict_user = not allow(EDIT, user)

		try:
			db.session.commit()
			on_user_modified.send(
				self,
				event_name=on_user_modified.name,
				user=current_user,
				data={'id': user_id, 'changes': changes})
		except exc.IntegrityError:
			db.session.rollback()
			current_app.logger.error("Failed to edit user. Duplicate.")
			return {'error': 'A user with the same identifier already exists.'}, 409
		return marshal(user, dataformat.get_users(restrict_user))


# /
class UserListAPI(Resource):
	@login_required
	@pagination(Users)
	@marshal_with(dataformat.get_users(False))
	def get(self, objects):
		require(MANAGE, Users)
		on_user_list_get.send(
			self,
			event_name=on_user_list_get.name,
			user=current_user)
		return objects

	@login_required
	def post(self):
		user = Users()
		require(CREATE, user)
		params = new_user_parser.parse_args()

		user.username = params.get("username")
		username_exists = Users.query.filter_by(username=user.username).first()
		if username_exists:
			return {"error": "This username already exists. Please pick another."}, 409

		user.student_no = params.get("student_no", None)
		student_no_exists = Users.query.filter_by(student_no=user.student_no).first()
		# if student_no is not left blank and it exists -> 409 error
		if user.student_no is not None and student_no_exists:
			return {"error": "This student number already exists. Please pick another."}, 409

		user.password = params.get("password")
		user.usertypesforsystem_id = params.get("usertypesforsystem_id")
		user.email = params.get("email")
		user.firstname = params.get("firstname")
		user.lastname = params.get("lastname")
		user.displayname = params.get("displayname")

		try:
			db.session.add(user)
			db.session.commit()
			on_user_create.send(
				self,
				event_name=on_user_create.name,
				user=current_user,
				data=marshal(user, dataformat.get_users(False)))
		except exc.IntegrityError:
			db.session.rollback()
			current_app.logger.error("Failed to add new user. Duplicate.")
			return {'error': 'A user with the same identifier already exists.'}, 400
		return marshal(user, dataformat.get_users())


# /user_id/courses
class UserCourseListAPI(Resource):
	@login_required
	def get(self, user_id):
		Users.query.get_or_404(user_id)
		# we want to list courses only, so only check the association table
		keys = dataformat.get_courses(include_details=False).keys()
		if allow(MANAGE, Courses):
			courses = Courses.query.order_by(asc(Courses.name)).options(load_only(*keys)).all()
		else:
			courses = Courses.get_by_user(user_id, fields=keys)

		# TODO REMOVE COURSES WHERE COURSE IS UNAVAILABLE?

		on_user_course_get.send(
			self,
			event_name=on_user_course_get.name,
			user=current_user,
			data={'userid': user_id})

		return {'objects': marshal(courses, dataformat.get_courses(include_details=False))}


# /user_id/edit
class UserEditButtonAPI(Resource):
	@login_required
	def get(self, user_id):
		user = Users.query.get_or_404(user_id)
		instructor = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).first().id
		dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id
		courses = CoursesAndUsers.query.filter_by(users_id=current_user.id, usertypesforcourse_id=instructor).all()
		available = False
		if len(courses) > 0:
			course_ids = [c.courses_id for c in courses]
			enrolled = CoursesAndUsers.query.filter_by(users_id=user.id) \
				.filter(
					CoursesAndUsers.courses_id.in_(course_ids),
					CoursesAndUsers.usertypesforcourse_id != dropped).\
				count()
			available = enrolled > 0

		on_user_edit_button_get.send(
			self,
			event_name=on_user_edit_button_get.name,
			user=current_user,
			data={'userId': user.id, 'available': available})

		return {'available': available}


# courses/teaching
class TeachingUserCourseListAPI(Resource):
	@login_required
	def get(self):
		if allow(MANAGE, Courses()):
			courses = Courses.query.all()
			course_list = [{'id': c.id, 'name': c.name} for c in courses]
		else:
			course_list = [
				{'id': c.course.id, 'name': c.course.name} for c in current_user.coursesandusers
				if allow(MANAGE, PostsForQuestions(post=Posts(courses_id=c.course.id)))]

		on_teaching_course_get.send(
			self,
			event_name=on_teaching_course_get.name,
			user=current_user
		)

		return {'courses': course_list}


# /
class UserTypesAPI(Resource):
	@login_required
	def get(self):
		admin = UserTypesForSystem.TYPE_SYSADMIN
		if current_user.usertypeforsystem.name == admin:
			types = UserTypesForSystem.query. \
				order_by("id").all()
		else:
			types = UserTypesForSystem.query.filter(UserTypesForSystem.name != admin). \
				order_by("id").all()

		on_user_types_all_get.send(
			self,
			event_name=on_user_types_all_get.name,
			user=current_user
		)

		return marshal(types, dataformat.get_user_types_for_system())


# /instructors
class UserTypesInstructorsAPI(Resource):
	@login_required
	def get(self):
		user_type_id = UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_INSTRUCTOR).first().id
		instructors = Users.query.filter_by(usertypesforsystem_id=user_type_id).order_by(Users.firstname).all()
		instructors = [{
			'id': i.id,
			'display': (i.fullname or '') + ' (' + i.displayname + ') - ' + i.usertypeforsystem.name,
			'name': i.fullname} for i in instructors]

		on_instructors_get.send(
			self,
			event_name=on_instructors_get.name,
			user=current_user
		)

		return {'instructors': instructors}


# /all
class UserTypesAllAPI(Resource):
	@login_required
	def get(self):
		users = Users.query.order_by(Users.firstname).all()
		require(EDIT, CoursesAndUsers)
		users = [{
			'id': i.id,
			'display': (i.fullname or '') + ' (' + i.displayname + ') - ' + i.usertypeforsystem.name,
			'name': i.fullname} for i in users]

		on_users_display_get.send(
			self,
			event_name=on_users_display_get.name,
			user=current_user
		)

		return {'users': users}


class UserCourseRolesAPI(Resource):
	@login_required
	def get(self):
		roles = UserTypesForCourse.query.order_by("id"). \
			filter(UserTypesForCourse.name != UserTypesForCourse.TYPE_DROPPED).all()

		on_course_roles_all_get.send(
			self,
			event_name=on_course_roles_all_get.name,
			user=current_user
		)

		return marshal(roles, dataformat.get_user_types_for_course())


# /password
class UserUpdatePasswordAPI(Resource):
	@login_required
	def post(self, user_id):
		user = Users.query.get_or_404(user_id)
		require(EDIT, user)
		params = update_password_parser.parse_args()
		oldpassword = params.get('oldpassword')
		if user.verify_password(oldpassword):
			user.password = params.get('newpassword')
			db.session.add(user)
			db.session.commit()
			on_user_password_update.send(
				self,
				event_name=on_user_password_update.name,
				user=current_user)
			return marshal(user, dataformat.get_users(False))
		else:
			return {"error": "The old password is incorrect."}, 403


api = new_restful_api(users_api)
api.add_resource(UserAPI, '/<int:user_id>')
api.add_resource(UserListAPI, '')
api.add_resource(UserCourseListAPI, '/<int:user_id>/courses')
api.add_resource(UserEditButtonAPI, '/<int:user_id>/edit')
api.add_resource(TeachingUserCourseListAPI, '/courses/teaching')
api.add_resource(UserUpdatePasswordAPI, '/password/<int:user_id>')
apiT = new_restful_api(user_types_api)
apiT.add_resource(UserTypesAPI, '')
apiT.add_resource(UserTypesInstructorsAPI, '/instructors')
apiT.add_resource(UserTypesAllAPI, '/all')
apiC = new_restful_api(user_course_types_api)
apiC.add_resource(UserCourseRolesAPI, '')
