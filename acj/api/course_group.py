import uuid
import os
import csv
import json

from bouncer.constants import READ, CREATE, DELETE, EDIT
from flask import Blueprint, current_app, request, abort
from flask_restful import Resource, marshal
from flask_login import login_required
from werkzeug.utils import secure_filename
from flask_restful.reqparse import RequestParser

from flask_login import current_user
from sqlalchemy import and_, or_

from . import dataformat
from acj.authorization import require
from acj.core import db, event
from acj.models import UserCourse, User, Course, CourseRole
from .util import new_restful_api
from .file import allowed_file

course_group_api = Blueprint('course_group_api', __name__)
api = new_restful_api(course_group_api)

USER_IDENTIFIER = 0
GROUP_NAME = 1

import_parser = RequestParser()
import_parser.add_argument('userIdentifier', type=str, required=True)

# events
on_course_group_get = event.signal('COURSE_GROUP_GET')
on_course_group_import = event.signal('COURSE_GROUP_IMPORT')
on_course_group_members_get = event.signal('COURSE_GROUP_MEMBERS_GET')

def import_members(course, identifier, members):
    # initialize list of users and their statuses
    invalids = []  #invalid entry - eg. no group name
    user_infile = [] # for catching duplicate users
    count = 0 # keep track of active groups

    # require all rows to have two columns if there are a minimum of one entry
    if len(members) > 0 and len(members[0]) != 2:
        return {'success': count}
    elif identifier not in ['username', 'student_number']:
        invalids.append({'member': {}, 'message': 'A valid user identifier is not given.'})
        return {'success': count, 'invalids': invalids}


    # make set all group names to None initially
    user_courses = UserCourse.query.filter_by(course_id=course.id).all()
    for user_course in user_courses:
        user_course.group_name = None
        db.session.add(user_course)
    db.session.commit()

    enroled = UserCourse.query \
        .filter(and_(
            UserCourse.course_id == course.id,
            UserCourse.course_role != CourseRole.dropped
        )) \
        .all()

    # add groups
    groups = set(g[GROUP_NAME] for g in members)
    for group_name in groups:
        # invalid group name
        if not group_name:
            # skip for now - generate errors below
            continue
        count += 1

    enroled = [e.user_id for e in enroled]
    # enrol users to groups
    for member in members:
        if member[USER_IDENTIFIER] in user_infile:
            message = 'This user already exists in the file.'
            invalids.append({'member': json.dumps(member), 'message': message})
            continue
        if not member[GROUP_NAME]:
            message = 'The group name is invalid.'
            invalids.append({'member': json.dumps(member), 'message': message})
            continue

        if identifier == 'username':
            user = User.query.filter_by(username=member[USER_IDENTIFIER]).first()
            value = identifier
        else:
            user = User.query.filter_by(student_number=member[USER_IDENTIFIER]).first()
            value = 'student number'

        if not user:
            invalids.append({'member': json.dumps(member), 'message': 'No user with this '+value+' exists.'})
            continue

        if user.id in enroled:
            # get the user_course instance
            user_course = next(user_course for user_course in user.user_courses if user_course.course_id == course.id)
            user_course.group_name = member[GROUP_NAME]
            db.session.add(user_course)
            user_infile.append(member[USER_IDENTIFIER])
        else:
            message = 'The user is not enroled in the course'
            invalids.append({'member': json.dumps(member), 'message': message})
            continue
    db.session.commit()

    return {
        'success': count,
        'invalids': invalids
    }

# /
class GroupRootAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(READ, user_course)

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

    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(EDIT, user_course)

        params = import_parser.parse_args()
        identifier = params.get('userIdentifier')
        file = request.files['file']
        if file and allowed_file(file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
            unique = str(uuid.uuid4())
            filename = unique + secure_filename(file.filename)
            tmpName = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(tmpName)
            current_app.logger.debug("Import groups for course "+str(course.id)+" with "+ filename)
            with open(tmpName, 'rt') as csvfile:
                spamreader = csv.reader(csvfile)
                members = []
                for row in spamreader:
                    if row:
                        members.append(row)
                results = import_members(course, identifier, members)
            os.remove(tmpName)

            on_course_group_import.send(
                current_app._get_current_object(),
                event_name=on_course_group_import.name,
                user=current_user,
                course_id=course.id,
                data={'filename': tmpName}
            )

            current_app.logger.debug("Group Import for course " + str(course.id) + " is successful. Removed file.")
            return results
        else:
            return {'error': 'Wrong file type'}, 400
api.add_resource(GroupRootAPI, '')

# /:group_name
class GroupNameAPI(Resource):
    @login_required
    def get(self, course_uuid, group_name):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(READ, user_course)

        members = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role != CourseRole.dropped,
                UserCourse.group_name == group_name
            )) \
            .all()

        if len(members) == 0:
            abort(404)

        on_course_group_members_get.send(
            current_app._get_current_object(),
            event_name=on_course_group_members_get.name,
            user=current_user,
            course_id=course.id,
            data={'group_name': group_name})

        return {'students': [{'id': u.uuid, 'name': u.fullname} for u in members]}

api.add_resource(GroupNameAPI, '/<group_name>')