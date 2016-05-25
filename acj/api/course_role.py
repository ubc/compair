from flask import Blueprint
from flask.ext.restful import Resource
from flask_login import login_required, current_user

from acj.core import event
from .util import new_restful_api
from acj.models import CourseRole

user_course_role_api = Blueprint('user_course_role_api', __name__)

# events
on_course_roles_all_get = event.signal('COURSE_ROLES_ALL_GET')

class UserCourseRolesAPI(Resource):
    @login_required
    def get(self):
        course_roles = [
            CourseRole.student.value,
            CourseRole.teaching_assistant.value,
            CourseRole.instructor.value
        ]

        on_course_roles_all_get.send(
            self,
            event_name=on_course_roles_all_get.name,
            user=current_user
        )

        return course_roles
        
api = new_restful_api(user_course_role_api)
api.add_resource(UserCourseRolesAPI, '')