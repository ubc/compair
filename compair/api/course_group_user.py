from bouncer.constants import EDIT, READ, CREATE, DELETE
from flask import Blueprint, current_app, request
from flask_restful import Resource, marshal
from flask_login import login_required
from werkzeug.utils import secure_filename
from flask_restful.reqparse import RequestParser

from flask_login import current_user
from sqlalchemy import and_, or_

from . import dataformat
from compair.authorization import require
from compair.core import db, event, abort
from compair.models import UserCourse, User, Course, CourseRole
from .util import new_restful_api

user_list_parser = RequestParser()
user_list_parser.add_argument('ids', type=list, required=True, default=[], location='json')

course_group_user_api = Blueprint('course_group_user_api', __name__)
api = new_restful_api(course_group_user_api)

on_course_group_user_create = event.signal('COURSE_GROUP_USER_CREATE')
on_course_group_user_list_create = event.signal('COURSE_GROUP_USER_LIST_CREATE')
on_course_group_user_delete = event.signal('COURSE_GROUP_USER_DELETE')
on_course_group_user_list_delete = event.signal('COURSE_GROUP_USER_LIST_CREATE')

# /:user_uuid/groups/:group_name
class GroupUserIdAPI(Resource):
    @login_required
    def post(self, course_uuid, user_uuid, group_name):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user = User.get_by_uuid_or_404(user_uuid)

        user_course = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.user_id == user.id,
                UserCourse.course_role != CourseRole.dropped
            )) \
            .first_or_404()

        require(EDIT, user_course,
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        user_course.group_name = group_name
        db.session.commit()

        on_course_group_user_create.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_create.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return {'group_name': group_name}
api.add_resource(GroupUserIdAPI, '/<user_uuid>/groups/<group_name>')

# /:user_uuid/groups
class GroupUserAPI(Resource):
    @login_required
    def delete(self, course_uuid, user_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user = User.get_by_uuid_or_404(user_uuid)
        user_course = UserCourse.query \
            .filter_by(
                course_id=course.id,
                user_id=user.id
            ) \
            .first_or_404()
        require(EDIT, user_course,
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        user_course.group_name = None
        db.session.commit()

        on_course_group_user_delete.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_delete.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return {'user_id': user.uuid, 'course_id': course.uuid}
api.add_resource(GroupUserAPI, '/<user_uuid>/groups')


# /groups/:group_name
class GroupUserListGroupNameAPI(Resource):
    @login_required
    def post(self, course_uuid, group_name):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, UserCourse(course_id=course.id),
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        params = user_list_parser.parse_args()

        if len(params.get('ids')) == 0:
            abort(400, title="Group Not Saved", message="Please select at least one user below and then try to apply the group again.")

        user_courses = UserCourse.query \
            .join(User, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                User.uuid.in_(params.get('ids')),
                UserCourse.course_role != CourseRole.dropped
            )) \
            .all()

        if len(params.get('ids')) != len(user_courses):
            abort(400, title="Group Not Saved", message="One or more users selected are not enrolled in the course yet.")

        for user_course in user_courses:
            user_course.group_name = group_name

        db.session.commit()

        on_course_group_user_list_create.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_list_create.name,
            user=current_user,
            course_id=course.id,
            data={'user_uuids': params.get('ids')})

        return {'group_name': group_name}

api.add_resource(GroupUserListGroupNameAPI, '/groups/<group_name>')

class GroupUserListAPI(Resource):
    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, UserCourse(course_id=course.id),
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        params = user_list_parser.parse_args()

        if len(params.get('ids')) == 0:
            abort(400, title="Group Not Saved", message="Please select at least one user below and then try to apply the group again.")

        user_courses = UserCourse.query \
            .join(User, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                User.uuid.in_(params.get('ids')),
                UserCourse.course_role != CourseRole.dropped
            )) \
            .all()

        if len(params.get('ids')) != len(user_courses):
            abort(400, title="Group Not Saved", message="One or more users selected are not enrolled in the course yet.")

        for user_course in user_courses:
            user_course.group_name = None

        db.session.commit()

        on_course_group_user_list_delete.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_list_delete.name,
            user=current_user,
            course_id=course.id,
            data={'user_uuids': params.get('ids')})

        return {'course_id': course.uuid}

api.add_resource(GroupUserListAPI, '/groups')