from bouncer.constants import READ, CREATE, DELETE, EDIT
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
from compair.models import UserCourse, User, Course, CourseRole, \
    ThirdPartyUser, ThirdPartyType
from .util import new_restful_api

course_group_api = Blueprint('course_group_api', __name__)
api = new_restful_api(course_group_api)

# events
on_course_group_get = event.signal('COURSE_GROUP_GET')
on_course_group_members_get = event.signal('COURSE_GROUP_MEMBERS_GET')

# /
class GroupRootAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(READ, user_course,
            title="Groups Unavailable",
            message="Groups can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        group_names = UserCourse.query \
            .with_entities(UserCourse.group_name) \
            .distinct() \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role != CourseRole.dropped,
                UserCourse.group_name != None
            )) \
            .order_by(UserCourse.group_name) \
            .all()

        on_course_group_get.send(
            current_app._get_current_object(),
            event_name=on_course_group_get.name,
            user=current_user,
            course_id=course.id
        )

        return {'objects': [group.group_name for group in group_names] }

api.add_resource(GroupRootAPI, '')

# /:group_name
class GroupNameAPI(Resource):
    @login_required
    def get(self, course_uuid, group_name):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(READ, user_course,
            title="Group Members Unavailable",
            message="Group membership can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        members = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role != CourseRole.dropped,
                UserCourse.group_name == group_name
            )) \
            .all()

        if len(members) == 0:
            abort(404, title="Group Unavailable", message="Group "+group_name+" was deleted or is no longer available.")

        on_course_group_members_get.send(
            current_app._get_current_object(),
            event_name=on_course_group_members_get.name,
            user=current_user,
            course_id=course.id,
            data={'group_name': group_name})

        return {'students': [{'id': u.uuid, 'name': u.fullname_sortable} for u in members]}

api.add_resource(GroupNameAPI, '/<group_name>')