import datetime
import dateutil.parser
import sqlalchemy as db1
from sqlalchemy import create_engine
import json
from flask import jsonify
import pytz

from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint, current_app
from flask_bouncer import can
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import desc, or_, func, and_
from sqlalchemy.orm import joinedload, undefer_group, load_only
from six import text_type

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require, is_user_access_restricted
from compair.models import Assignment, Course, Criterion, AssignmentCriterion, Answer, Comparison, \
    AnswerComment, AnswerCommentType, PairingAlgorithm, Criterion, File, User, UserCourse, \
    CourseRole, Group
from .util import new_restful_api, get_model_changes, pagination_parser

from datetime import datetime
import time

assignment_search_enddate_api = Blueprint('assignment_search_enddate_api', __name__)
api = new_restful_api(assignment_search_enddate_api)

def validate(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False
# /
class AssignmentRootAPI1(Resource):
    @login_required
    def get(self):

        # get app timezone in settings
        appTimeZone = current_app.config.get('APP_TIMEZONE', time.strftime('%Z') )

        search_date_assignment_parser = RequestParser()
        search_date_assignment_parser.add_argument('compare_start', default=datetime.now().strftime("%Y-%m-%d"))
        search_date_assignment_parser.add_argument('compare_end', default=datetime.now().strftime("%Y-%m-%d"))
        search_date_assignment_parser.add_argument('compare_localTimeZone', default=appTimeZone)

        args = search_date_assignment_parser.parse_args()

        end_date = datetime.now().strftime("%Y-%m-%d 00:00:00")
        start_date = datetime.now().strftime("%Y-%m-%d")
        compare_localTimeZone = appTimeZone

        if (args['compare_localTimeZone']):
            compare_localTimeZone = str(args['compare_localTimeZone'])

        if validate(args['compare_end']):
            end_date = str(args['compare_end']) + ' 00:00:00'

            ##convert this to System TZ
            local = pytz.timezone(compare_localTimeZone)
            naive = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            systemTZ_dt = local_dt.astimezone(pytz.timezone(appTimeZone))
            end_date = str(systemTZ_dt)

        if validate(args['compare_start']):
            start_date = str(args['compare_start'])

        db_url = str(current_app.config['SQLALCHEMY_DATABASE_URI'])
        engine = create_engine(db_url, pool_size=5, pool_recycle=3600)
        conn = engine.connect()

        sql_text = str("SELECT JSON_OBJECT('course_name', t1.name,'name', t2.name,'answer_start', date_format(CONVERT_TZ(t2.answer_start, '" + appTimeZone + "','" + compare_localTimeZone + "'), '%%b %%d, %%Y'),'answer_end', date_format(CONVERT_TZ(t2.answer_end, '" + appTimeZone + "','" + compare_localTimeZone + "'),  '%%b %%d, %%Y'),'compare_start', date_format(CONVERT_TZ(t2.compare_start, '" + appTimeZone + "','" + compare_localTimeZone + "'),  '%%b %%d, %%Y'), 'compare_end', date_format(CONVERT_TZ(t2.compare_end, '" + appTimeZone + "','" + compare_localTimeZone + "'),  '%%b %%d, %%Y'), 'self_eval_end', date_format(CONVERT_TZ(t2.self_eval_end, '" + appTimeZone + "','" + compare_localTimeZone + "'),  '%%b %%d, %%Y'), 'self_eval_start', date_format(CONVERT_TZ(t2.self_eval_start, '" + appTimeZone + "','" + compare_localTimeZone + "'), '%%b %%d, %%Y')) FROM course as t1, assignment as t2 WHERE (t1.id = t2.course_id) AND (t2.active=TRUE AND t1.active=TRUE) AND (t2.compare_end >=  '" + end_date + "' OR answer_end >= '" + end_date + "' OR self_eval_end >= '" + end_date +  "');");

        result = conn.execute(sql_text)

        final_result = [list(i) for i in result]
        conn.close()

        return jsonify(final_result)

api.add_resource(AssignmentRootAPI1, '')
