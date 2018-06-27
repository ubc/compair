from flask import Blueprint, session as sess
from flask_restful import Resource, reqparse
from flask_login import login_required, current_user

from . import dataformat
from compair.core import db, event, abort
from compair.models import Assignment, Course, SystemRole, CourseRole, Answer
from compair.learning_records import XAPI, XAPIStatement, \
    CaliperSensor, CaliperEvent

from .util import new_restful_api

learning_record_api = Blueprint('learning_record_api', __name__)
api = new_restful_api(learning_record_api)

xapi_statement_parser = reqparse.RequestParser()
xapi_statement_parser.add_argument('course_id', type=str, required=False)
xapi_statement_parser.add_argument('verb', type=dict, location='json', required=True)
xapi_statement_parser.add_argument('object', type=dict, location='json', required=True)
xapi_statement_parser.add_argument('context', type=dict, location='json', required=False)
xapi_statement_parser.add_argument('result', type=dict, location='json', required=False)
xapi_statement_parser.add_argument('timestamp', type=str, required=False)

caliper_event_parser = reqparse.RequestParser()
caliper_event_parser.add_argument('course_id', type=str, required=False)
caliper_event_parser.add_argument('type', type=str, required=True)
caliper_event_parser.add_argument('action', type=str, required=True)
caliper_event_parser.add_argument('object', type=dict, location='json', required=True)
caliper_event_parser.add_argument('eventTime', type=str, required=False)
caliper_event_parser.add_argument('target', type=dict, location='json', required=False)
caliper_event_parser.add_argument('generated', type=dict, location='json', required=False)
caliper_event_parser.add_argument('referrer', type=dict, location='json', required=False)
caliper_event_parser.add_argument('extensions', type=dict, location='json', required=False)

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

        params = xapi_statement_parser.parse_args()
        course_uuid = params.pop('course_id')
        course = _get_valid_course(course_uuid)

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

        params = caliper_event_parser.parse_args()
        course_uuid = params.pop('course_id')
        course = _get_valid_course(course_uuid)

        event = CaliperEvent.generate_from_params(current_user, params, course=course)
        CaliperSensor.emit(event)

        return { 'success': True }

api.add_resource(CaliperEventAPI, '/caliper/events')
