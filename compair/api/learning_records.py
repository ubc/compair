from flask import Blueprint, session as sess, request
from flask_restful import Resource
from flask_login import login_required, current_user

from . import dataformat
from compair.core import db, event, abort
from compair.models import Assignment, Course, SystemRole, CourseRole, Answer
from compair.learning_records import XAPI, XAPIStatement, \
    CaliperSensor, CaliperEvent

from .util import new_restful_api

learning_record_api = Blueprint('learning_record_api', __name__)
api = new_restful_api(learning_record_api)

def _get_valid_course(course_uuid):
    if not course_uuid:
        return None

    course = Course.query.filter_by(uuid=course_uuid).first()
    if not course:
        return None

    if current_user.system_role == SystemRole.sys_admin:
        return course

    course_role = current_user.get_course_role(course.id)
    if not course_role or course_role == CourseRole.dropped:
        return None

    return course

class xAPIStatementAPI(Resource):
    @login_required
    def post(self):
        if not XAPI.enabled():
            # this should silently fail
            abort(404)

        raw_params = request.get_json(force=True)
        params = {}

        course_uuid = raw_params.get('course_id')
        course = _get_valid_course(course_uuid)

        # add required params
        for param in ['verb', 'object']:
            if not raw_params.get(param):
                abort(400)
            params[param] = raw_params.get(param)

        # add optional params
        for param in ['context', 'result', 'timestamp']:
            if raw_params.get(param):
                params[param] = raw_params.get(param)

        statement = XAPIStatement.generate_from_params(current_user, params, course=course)
        XAPI.emit(statement)

        return { 'success': True }

api.add_resource(xAPIStatementAPI, '/xapi/statements')

class CaliperEventAPI(Resource):
    @login_required
    def post(self):
        if not CaliperSensor.enabled():
            # this should silently fail
            abort(404)

        raw_params = request.get_json(force=True)
        params = {}

        course_uuid = raw_params.get('course_id')
        course = _get_valid_course(course_uuid)

        # add required params
        for param in ['type', 'action', 'object']:
            if not raw_params.get(param):
                abort(400)
            params[param] = raw_params.get(param)

        # add optional params
        for param in ['eventTime', 'target', 'generated', 'referrer', 'extensions', 'profile']:
            if raw_params.get(param):
                params[param] = raw_params.get(param)

        event = CaliperEvent.generate_from_params(current_user, params, course=course)
        CaliperSensor.emit(event)

        return { 'success': True }

api.add_resource(CaliperEventAPI, '/caliper/events')
