from flask import Blueprint, current_app, abort
from bouncer.constants import MANAGE, EDIT, CREATE, READ
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from flask_login import login_required, current_user
from sqlalchemy.orm import load_only
from sqlalchemy import exc, asc, or_, and_

from . import dataformat
from acj.authorization import is_user_access_restricted, require, allow
from acj.core import db, event
from .util import new_restful_api, get_model_changes, pagination_parser
from acj.models import User, SystemRole, Course, UserCourse, CourseRole, Assignment

user_api = Blueprint('user_api', __name__)

def non_blank_str(value):
    return None if str(value) == "" else str(value)

new_user_parser = RequestParser()
new_user_parser.add_argument('username', type=str, required=True)
new_user_parser.add_argument('student_number', type=non_blank_str)
new_user_parser.add_argument('system_role', type=str, required=True)
new_user_parser.add_argument('firstname', type=str, required=True)
new_user_parser.add_argument('lastname', type=str, required=True)
new_user_parser.add_argument('displayname', type=str, required=True)
new_user_parser.add_argument('email', type=str)
new_user_parser.add_argument('password', type=str, required=True)

existing_user_parser = RequestParser()
existing_user_parser.add_argument('id', type=int, required=True)
existing_user_parser.add_argument('username', type=str, required=True)
existing_user_parser.add_argument('student_number', type=non_blank_str)
existing_user_parser.add_argument('system_role', type=str, required=True)
existing_user_parser.add_argument('firstname', type=str, required=True)
existing_user_parser.add_argument('lastname', type=str, required=True)
existing_user_parser.add_argument('displayname', type=str, required=True)
existing_user_parser.add_argument('email', type=str)

update_password_parser = RequestParser()
update_password_parser.add_argument('oldpassword', type=str, required=False)
update_password_parser.add_argument('newpassword', type=str, required=True)

user_list_parser = pagination_parser.copy()
user_list_parser.add_argument('search', type=str, required=False, default=None)
user_list_parser.add_argument('ids', type=str, required=False, default=None)

# events
on_user_modified = event.signal('USER_MODIFIED')
on_user_get = event.signal('USER_GET')
on_user_list_get = event.signal('USER_LIST_GET')
on_user_create = event.signal('USER_CREATE')
on_user_course_get = event.signal('USER_COURSE_GET')
on_teaching_course_get = event.signal('USER_TEACHING_COURSE_GET')
on_user_edit_button_get = event.signal('USER_EDIT_BUTTON_GET')
on_user_password_update = event.signal('USER_PASSWORD_UPDATE')

def check_valid_system_role(system_role):
    system_roles = [
        SystemRole.sys_admin.value,
        SystemRole.instructor.value,
        SystemRole.student.value
    ]
    if system_role not in system_roles:
        abort(400)

# /user_id
class UserAPI(Resource):
    @login_required
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        on_user_get.send(
            self,
            event_name=on_user_get.name,
            user=current_user,
            data={'id': user_id}
        )
        return marshal(user, dataformat.get_user(is_user_access_restricted(user)))

    @login_required
    def post(self, user_id):
        user = User.query.get_or_404(user_id)
        if is_user_access_restricted(user):
            return {'error': "Sorry, you don't have permission for this action."}, 403
        params = existing_user_parser.parse_args()
        # make sure the user id in the url and the id matches
        if params['id'] != user_id:
            return {"error": "User id does not match URL."}, 400

        if allow(MANAGE, user):
            username = params.get("username", user.username)
            username_exists = User.query.filter_by(username=username).first()
            if username_exists and username_exists.id != user.id:
                return {"error": "This username already exists. Please pick another."}, 409
            else:
                user.username = username

            student_number = params.get("student_number", user.student_number)
            student_number_exists = User.query.filter_by(student_number=student_number).first()
            if student_number is not None and student_number_exists and student_number_exists.id != user.id:
                return {"error": "This student number already exists. Please pick another."}, 409
            else:
                user.student_number = student_number

            system_role = params.get("system_role", user.system_role.value)
            check_valid_system_role(system_role)
            user.system_role = SystemRole(system_role)

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
        return marshal(user, dataformat.get_user(restrict_user))


# /
class UserListAPI(Resource):
    @login_required
    def get(self):
        restrict_user = not allow(READ, User)

        params = user_list_parser.parse_args()

        query = User.query
        if params['search']:
            search = '%{}%'.format(params['search'])
            query = query.filter(or_(User.firstname.like(search), User.lastname.like(search)))
        page = query.paginate(params['page'], params['perPage'])

        on_user_list_get.send(
            self,
            event_name=on_user_list_get.name,
            user=current_user)

        return {"objects": marshal(page.items, dataformat.get_user(restrict_user)), "page": page.page,
                "pages": page.pages, "total": page.total, "per_page": page.per_page}

    @login_required
    def post(self):
        user = User()
        params = new_user_parser.parse_args()
        user.username = params.get("username")
        user.password = params.get("password")
        user.student_number = params.get("student_number", None)
        user.email = params.get("email")
        user.firstname = params.get("firstname")
        user.lastname = params.get("lastname")
        user.displayname = params.get("displayname")

        system_role = params.get("system_role")
        check_valid_system_role(system_role)
        user.system_role = SystemRole(system_role)

        require(CREATE, user)

        username_exists = User.query.filter_by(username=user.username).first()
        if username_exists:
            return {"error": "This username already exists. Please pick another."}, 409

        student_number_exists = User.query.filter_by(student_number=user.student_number).first()
        # if student_number is not left blank and it exists -> 409 error
        if user.student_number is not None and student_number_exists:
            return {"error": "This student number already exists. Please pick another."}, 409

        try:
            db.session.add(user)
            db.session.commit()
            on_user_create.send(
                self,
                event_name=on_user_create.name,
                user=current_user,
                data=marshal(user, dataformat.get_user(False)))
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to add new user. Duplicate.")
            return {'error': 'A user with the same identifier already exists.'}, 400
        return marshal(user, dataformat.get_user())


# /user_id/courses
class UserCourseListAPI(Resource):
    @login_required
    def get(self, user_id):
        User.query.get_or_404(user_id)
        # we want to list courses only, so only check the association table
        if allow(MANAGE, Course):
            courses = Course.query \
                .filter_by(active=True) \
                .order_by(Course.name) \
                .all()
        else:
            courses = Course.query \
                .join(UserCourse) \
                .filter(and_(
                    UserCourse.user_id == user_id,
                    UserCourse.course_role != CourseRole.dropped,
                    Course.active == True
                )) \
                .order_by(Course.name) \
                .all()

        # TODO REMOVE COURSES WHERE COURSE IS UNAVAILABLE?

        on_user_course_get.send(
            self,
            event_name=on_user_course_get.name,
            user=current_user,
            data={'userid': user_id})

        return {'objects': marshal(courses, dataformat.get_course())}

# courses/teaching
class TeachingUserCourseListAPI(Resource):
    @login_required
    def get(self):
        if allow(MANAGE, Course()):
            courses = Course.query.all()
            course_list = [{'id': c.id, 'name': c.name} for c in courses]
        else:
            course_list = [ {'id': user_course.course_id, 'name': user_course.course.name}
                for user_course in current_user.user_courses
                if allow(MANAGE, Assignment(course_id=user_course.course_id))]

        on_teaching_course_get.send(
            self,
            event_name=on_teaching_course_get.name,
            user=current_user
        )

        return {'courses': course_list}

# /user_id/edit
class UserEditButtonAPI(Resource):
    @login_required
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        available = allow(EDIT, user)
        on_user_edit_button_get.send(
            self,
            event_name=on_user_edit_button_get.name,
            user=current_user,
            data={'userId': user.id, 'available': available})

        return {'available': available}

# /password
class UserUpdatePasswordAPI(Resource):
    @login_required
    def post(self, user_id):
        user = User.query.get_or_404(user_id)
        # anyone who passes checking below should be an instructor or admin
        require(EDIT, user)
        params = update_password_parser.parse_args()
        oldpassword = params.get('oldpassword')
        # if it is not current user changing own password, it must be an instructor or admin
        # because of above check
        if current_user.id != user_id or (oldpassword and user.verify_password(oldpassword)):
            user.password = params.get('newpassword')
            db.session.add(user)
            db.session.commit()
            on_user_password_update.send(
                self,
                event_name=on_user_password_update.name,
                user=current_user)
            return marshal(user, dataformat.get_user(False))
        else:
            return {"error": "The old password is incorrect or you do not have permission to change password."}, 403


api = new_restful_api(user_api)
api.add_resource(UserAPI, '/<int:user_id>')
api.add_resource(UserListAPI, '')
api.add_resource(UserCourseListAPI, '/<int:user_id>/courses')
api.add_resource(TeachingUserCourseListAPI, '/courses/teaching')
api.add_resource(UserEditButtonAPI, '/<int:user_id>/edit')
api.add_resource(UserUpdatePasswordAPI, '/<int:user_id>/password')
