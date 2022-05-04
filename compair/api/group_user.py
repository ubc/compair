from bouncer.constants import EDIT, READ, CREATE, DELETE, MANAGE
from flask import Blueprint, current_app, request
from flask_bouncer import can
from flask_restful import Resource, marshal
from flask_login import login_required
from werkzeug.utils import secure_filename
from flask_restful.reqparse import RequestParser

from flask_login import current_user
from sqlalchemy import and_, or_

from . import dataformat
from compair.authorization import require
from compair.core import db, event, abort
from compair.models import UserCourse, User, Course, CourseRole, \
    Group
from .util import new_restful_api, get_model_changes

user_list_parser = RequestParser()
user_list_parser.add_argument('ids', type=list, required=True, nullable=False, default=[], location='json')

group_user_api = Blueprint('group_user_api', __name__)
api = new_restful_api(group_user_api)

on_group_user_list_get = event.signal('GROUP_USERS_GET')
on_group_user_get = event.signal('GROUP_USER_GET')
on_group_user_create = event.signal('GROUP_USER_CREATE')
on_group_user_list_create = event.signal('GROUP_USER_LIST_CREATE')
on_group_user_delete = event.signal('GROUP_USER_DELETE')
on_group_user_list_delete = event.signal('GROUP_USER_LIST_DELETE')

# /<group_uuid>/users/:user_uuid
class GroupUserIdAPI(Resource):
    @login_required
    def post(self, course_uuid, group_uuid, user_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        group = Group.get_active_by_uuid_or_404(group_uuid)
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

        if course.groups_locked and user_course.group_id != None and user_course.group_id != group.id:
            abort(400, title="Group Not Saved",
                message="The course groups are locked. This user is already assigned to a different group.")

        user_course.group_id = group.id
        db.session.commit()

        on_group_user_create.send(
            current_app._get_current_object(),
            event_name=on_group_user_create.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return marshal(group, dataformat.get_group())

api.add_resource(GroupUserIdAPI, '/<group_uuid>/users/<user_uuid>')


# /<group_uuid>/users
class GroupUserListAPI(Resource):
    @login_required
    def get(self, course_uuid, group_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        group = Group.get_active_by_uuid_or_404(group_uuid)

        require(READ, UserCourse(course_id=course.id),
            title="Group Members Unavailable",
            message="Group membership can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        members = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role != CourseRole.dropped,
                UserCourse.group_id == group.id
            )) \
            .order_by(User.lastname, User.firstname) \
            .all()

        on_group_user_list_get.send(
            current_app._get_current_object(),
            event_name=on_group_user_list_get.name,
            user=current_user,
            course_id=course.id,
            data={'group_id': group.id})

        return {'objects': [{'id': u.uuid, 'name': u.fullname_sortable} for u in members]}

    @login_required
    def post(self, course_uuid, group_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        group = Group.get_active_by_uuid_or_404(group_uuid)

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
            if course.groups_locked and user_course.group_id != None and user_course.group_id != group.id:
                abort(400, title="Group Not Saved",
                    message="The course groups are locked. One or more users are already assigned to a different group.")

        for user_course in user_courses:
            user_course.group_id = group.id

        db.session.commit()

        on_group_user_list_create.send(
            current_app._get_current_object(),
            event_name=on_group_user_list_create.name,
            user=current_user,
            course_id=course.id,
            data={'user_ids': [user_course.user_id for user_course in user_courses] }
        )

        return marshal(group, dataformat.get_group())

api.add_resource(GroupUserListAPI, '/<group_uuid>/users')

class GroupUserDeleteAPI(Resource):
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

        if course.groups_locked and user_course.group_id != None:
            abort(400, title="Group Not Saved",
                message="The course groups are locked. You may not remove users from the group they are already assigned to.")

        user_course.group_id = None
        db.session.commit()

        on_group_user_delete.send(
            current_app._get_current_object(),
            event_name=on_group_user_delete.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return {'success': True}

api.add_resource(GroupUserDeleteAPI, '/users/<user_uuid>')

class GroupUserListDeleteAPI(Resource):
    @login_required
    def post(self, course_uuid):
        # delete multiple (DELETE request cannot use params in angular)
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
            if course.groups_locked and user_course.group_id != None:
                abort(400, title="Group Not Saved",
                    message="The course groups are locked. You may not remove users from the group they are already assigned to.")

        for user_course in user_courses:
            user_course.group_id = None

        db.session.commit()

        on_group_user_list_delete.send(
            current_app._get_current_object(),
            event_name=on_group_user_list_delete.name,
            user=current_user,
            course_id=course.id,
            data={'user_ids': [user_course.user_id for user_course in user_courses] }
        )

        return { 'success': True }

api.add_resource(GroupUserListDeleteAPI, '/users')


class GroupCurrentUserAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)

        require(READ, course,
            title="Group Unavailable",
            message="Groups can be seen those enrolled in the course. Please double-check your enrollment in this course.")

        user_course = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.user_id == current_user.id,
                UserCourse.course_role != CourseRole.dropped
            )) \
            .one_or_none()

        if not user_course:
            # return none for admins who aren't enrolled in the course
            if can(MANAGE, course):
                return None
            abort(400, title="Group Unavailable",
                message="You are not currently enrolled in the course. Please double-check your enrollment in this course.")

        group = user_course.group

        on_group_user_get.send(
            current_app._get_current_object(),
            event_name=on_group_user_get.name,
            user=current_user,
            course_id=course.id
        )

        if group:
            return marshal(group, dataformat.get_group())
        else:
            return None

api.add_resource(GroupCurrentUserAPI, '/user')
