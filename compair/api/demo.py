import string

from flask import Blueprint, current_app, session as sess
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from flask_login import current_user
from sqlalchemy import exc, asc, or_, and_, func

from . import dataformat
from compair.core import db, event, abort
from .util import new_restful_api, get_model_changes, pagination_parser
from compair.models import User, SystemRole, UserCourse, CourseRole
from compair.api.login import authenticate

from .classlist import display_name_generator
from .file import random_generator

demo_api = Blueprint('demo_api', __name__)
api = new_restful_api(demo_api)

new_user_demo_parser = RequestParser()
new_user_demo_parser.add_argument('system_role', type=str, required=True)

# events
on_user_demo_create = event.signal('USER_DEMO_CREATE')

def check_valid_system_role(system_role):
    system_roles = [
        SystemRole.sys_admin.value,
        SystemRole.instructor.value,
        SystemRole.student.value
    ]
    if system_role not in system_roles:
        abort(400, title="Demo Account Not Saved", message="Please try again with a system role from the list of roles provided.")

# /
class DemoListAPI(Resource):
    def post(self):
        if not current_app.config.get('DEMO_INSTALLATION', False):
            abort(404, title="Demo Accounts Unavailable", message="Sorry, the system settings do now allow the use of demo accounts.")

        params = new_user_demo_parser.parse_args()

        user = User()
        user.password = "demo"

        system_role = params.get("system_role")
        check_valid_system_role(system_role)
        user.system_role = SystemRole(system_role)

        user_count = User.query \
            .filter_by(system_role=user.system_role) \
            .count()
        user_count += 1

        # username
        while True:
            if user.system_role == SystemRole.sys_admin:
                user.username="admin"+str(user_count)
            elif user.system_role == SystemRole.instructor:
                user.username="instructor"+str(user_count)
            else:
                user.username="student"+str(user_count)

            username_exists = User.query.filter_by(username=user.username).first()
            if not username_exists:
                break
            else:
                user_count+=1

        if user.system_role == SystemRole.sys_admin:
            user.firstname = "Admin"
            user.lastname = str(user_count)
            user.displayname = "Admin "+str(user_count)
        elif user.system_role == SystemRole.instructor:
            user.firstname = "Instructor"
            user.lastname = str(user_count)
            user.displayname = "Instructor "+str(user_count)

            # create new enrollment
            new_user_course = UserCourse(
                user=user,
                course_id=1,
                course_role=CourseRole.instructor
            )
            db.session.add(new_user_course)
        else:
            user.firstname = "Student"
            user.lastname = str(user_count)
            user.displayname = display_name_generator()

            while True:
                user.student_number = random_generator(8, string.digits)
                student_number_exists = User.query.filter_by(student_number=user.student_number).first()
                if not student_number_exists:
                    break

            # create new enrollment
            new_user_course = UserCourse(
                user=user,
                course_id=1,
                course_role=CourseRole.student
            )
            db.session.add(new_user_course)

        try:
            db.session.add(user)
            db.session.commit()
            on_user_demo_create.send(
                self,
                event_name=on_user_demo_create.name,
                user=current_user,
                data=marshal(user, dataformat.get_full_user()))

        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to add new user. Duplicate.")
            return {'error': 'A user with the same identifier already exists.'}, 400

        authenticate(user, login_method="Demo")

        return marshal(user, dataformat.get_full_user())

api.add_resource(DemoListAPI, '')