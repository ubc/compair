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
    ThirdPartyUser, ThirdPartyType, Group, Answer
from .util import new_restful_api, get_model_changes

group_api = Blueprint('group_api', __name__)
api = new_restful_api(group_api)

new_group_parser = RequestParser()
new_group_parser.add_argument('name', required=True, nullable=False, help="Group name is required.")

existing_group_parser = new_group_parser.copy()
existing_group_parser.add_argument('id', required=True, nullable=False, help="Group id is required.")

# events
on_group_create = event.signal('GROUP_CREATE')
on_group_edit = event.signal('GROUP_EDIT')
on_group_get = event.signal('GROUP_GET')
on_group_delete = event.signal('GROUP_DELETE')

# /
class GroupRootAPI(Resource):
    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        new_group = Group(course_id=course.id)

        require(CREATE, new_group,
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        params = new_group_parser.parse_args()

        new_group.name = params.get("name")

        # check if group name is unique
        group_name_exists = Group.query \
            .filter(
                Group.course_id == course.id,
                Group.name == new_group.name,
                Group.active == True
            ) \
            .first()

        if group_name_exists:
            abort(400, title="Group Not Added",
                message="Sorry, the group name you have entered already exists. Please choose a different name.")

        db.session.add(new_group)
        db.session.commit()

        on_group_create.send(
            current_app._get_current_object(),
            event_name=on_group_create.name,
            user=current_user,
            course_id=course.id,
            data=marshal(new_group, dataformat.get_group())
        )

        return marshal(new_group, dataformat.get_group())

    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, Group(course_id=course.id),
            title="Groups Unavailable",
            message="Groups can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        groups = Group.query \
            .filter_by(
                course_id=course.id,
                active=True
            ) \
            .order_by(Group.name) \
            .all()

        on_group_get.send(
            current_app._get_current_object(),
            event_name=on_group_get.name,
            user=current_user,
            course_id=course.id
        )

        return {'objects': marshal(groups, dataformat.get_group()) }

api.add_resource(GroupRootAPI, '')

# /:group_uuid
class GroupIdAPI(Resource):
    @login_required
    def post(self, course_uuid, group_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        group = Group.get_active_by_uuid_or_404(group_uuid)

        require(EDIT, group,
            title="Group Not Saved",
            message="Sorry, your role in this course does not allow you to save groups.")

        params = existing_group_parser.parse_args()

        # check if group name is unique. a race condition may cause duplicate group name,
        # but assuming the chance is small and impact is minimal
        group_name_exists = Group.query \
            .filter(
                Group.id != group.id,
                Group.course_id == group.course_id,
                Group.name == params.get("name", group.name),
                Group.active == True
            ) \
            .first()

        if group_name_exists:
            abort(400, title="Group Not Saved",
                message="Sorry, the group name you have entered already exists. Please choose a different name.")

        group.name = params.get("name", group.name)

        model_changes = get_model_changes(group)
        db.session.commit()

        on_group_edit.send(
            current_app._get_current_object(),
            event_name=on_group_edit.name,
            user=current_user,
            course_id=course.id,
            data=model_changes
        )

        return marshal(group, dataformat.get_group())

    @login_required
    def delete(self, course_uuid, group_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        group = Group.get_active_by_uuid_or_404(group_uuid)

        require(DELETE, group,
            title="Group Not Deleted",
            message="Sorry, your role in this course does not allow you to delete groups.")

        # check if group has submitted any answers
        if group.group_answer_exists:
            abort(400, title="Group Not Deleted",
                message="Sorry, you cannot remove groups that have submitted answers.")

        group.active = False

        # remove members from the group
        user_courses = UserCourse.query \
            .filter_by(group_id=group.id) \
            .all()
        for user_course in user_courses:
            user_course.group_id = None

        db.session.commit()

        on_group_delete.send(
            current_app._get_current_object(),
            event_name=on_group_delete.name,
            user=current_user,
            course_id=course.id
        )

        return {'id': group.uuid }

api.add_resource(GroupIdAPI, '/<group_uuid>')