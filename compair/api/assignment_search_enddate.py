import datetime
import dateutil.parser
import sqlalchemy as db1
from sqlalchemy import create_engine
import json
from flask import jsonify

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

assignment_search_enddate_api = Blueprint('assignment_search_enddate_api', __name__)
api = new_restful_api(assignment_search_enddate_api)

##event
on_assignment_get = event.signal('ASSIGNMENT_GET')

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

        search_date_assignment_parser = RequestParser()
        search_date_assignment_parser.add_argument('compare_start', default=datetime.now().strftime("%Y-%m-%d"))
        search_date_assignment_parser.add_argument('compare_end', default=datetime.now().strftime("%Y-%m-%d"))
        args = search_date_assignment_parser.parse_args()

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = datetime.now().strftime("%Y-%m-%d")


        if validate(args['compare_end']):
            end_date = str(args['compare_end'])
        if validate(args['compare_start']):
            start_date = str(args['compare_start'])

        db_url = str(current_app.config['SQLALCHEMY_DATABASE_URI'])
        engine = create_engine(db_url, pool_size=5, pool_recycle=3600)
        conn = engine.connect()
        ##sql_text = str("SELECT JSON_OBJECT('uuid', uuid,'name', name,'compare_start', compare_start, 'compare_end', compare_end) FROM assignment;");
        ##sql_text = str("SELECT JSON_OBJECT('uuid', uuid,'name', name,'compare_start', compare_start, 'compare_end', compare_end) FROM assignment WHERE compare_end >= '" + end_date + "';");
        ##sql_text = str("SELECT JSON_OBJECT('uuid', uuid,'name', name,'answer_start', answer_start,'answer_end', answer_end,'compare_start', compare_start, 'compare_end', compare_end) FROM assignment WHERE compare_end >= '" + end_date + "' OR answer_end >= '" + end_date + "';");
        sql_text = str("SELECT JSON_OBJECT('uuid', uuid,'name', name,'answer_start', date_format(answer_start, '%%M %%d, %%Y'),'answer_end', date_format(answer_end, '%%M %%d, %%Y'),'compare_start', date_format(compare_start, '%%M %%d, %%Y'), 'compare_end', date_format(compare_end, '%%M %%d, %%Y')) FROM assignment WHERE compare_end >= '" + end_date + "' OR answer_end >= '" + end_date + "';");

        print(sql_text)

        result = conn.execute(sql_text)

        final_result = [list(i) for i in result]
        conn.close()

        return jsonify(final_result)

api.add_resource(AssignmentRootAPI1, '')
