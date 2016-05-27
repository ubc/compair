from bouncer.constants import EDIT, READ, CREATE, DELETE
from flask import Blueprint, current_app, request
from flask.ext.restful import Resource, marshal
from flask_login import login_required
from werkzeug.utils import secure_filename
from flask.ext.restful.reqparse import RequestParser

from flask.ext.login import current_user
from sqlalchemy import and_, or_

from . import dataformat
from acj.authorization import require
from acj.core import db, event
from acj.models import UserCourse, User, Course, CourseRole
from .util import new_restful_api

course_group_user_api = Blueprint('course_group_user_api', __name__)
api = new_restful_api(course_group_user_api)

on_course_group_user_create = event.signal('COURSE_GROUP_USER_CREATE')
on_course_group_user_delete = event.signal('COURSE_GROUP_USER_DELETE')

# /users/:user_id/groups/:group_name
class GroupUserIdAPI(Resource):
    @login_required
    def post(self, course_id, user_id, group_name):
        Course.get_active_or_404(course_id)
        User.query.get_or_404(user_id)

        user_course = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == course_id,
                UserCourse.user_id == user_id,
                UserCourse.course_role != CourseRole.dropped
            )) \
            .first_or_404()

        require(EDIT, user_course)

        user_course.group_name = group_name
        db.session.add(user_course)
        db.session.commit()

        on_course_group_user_create.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_create.name,
            user=current_user,
            course_id=course_id,
            data={'user_id': user_id})

        return {'group_name': group_name}
api.add_resource(GroupUserIdAPI, '/<group_name>')

# /users/:user_id/groups
class GroupUserAPI(Resource):
    @login_required
    def delete(self, course_id, user_id):
        Course.get_active_or_404(course_id)
        User.query.get_or_404(user_id)
        user_course = UserCourse.query \
            .filter_by(
                course_id=course_id,
                user_id=user_id
            ) \
            .first_or_404()

        require(EDIT, user_course)
        user_course.group_name = None
        db.session.add(user_course)
        db.session.commit()

        on_course_group_user_delete.send(
            current_app._get_current_object(),
            event_name=on_course_group_user_delete.name,
            user=current_user,
            course_id=course_id,
            data={'user_id': user_id})

        return {'user_id': user_id, 'course_id': course_id}
api.add_resource(GroupUserAPI, '')
