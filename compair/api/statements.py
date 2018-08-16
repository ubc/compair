from flask import Blueprint
from flask_restful import Resource, reqparse
from flask_login import login_required, current_user

from compair.core import db, event, abort
from compair.xapi import XAPI, XAPIStatement

from .util import new_restful_api

statement_api = Blueprint('statement_api', __name__)
api = new_restful_api(statement_api)


statement_parser = reqparse.RequestParser()
statement_parser.add_argument('verb', type=dict, location='json', required=True, nullable=False)
statement_parser.add_argument('object', type=dict, location='json', required=True, nullable=False)
statement_parser.add_argument('context', type=dict, location='json', required=False)
statement_parser.add_argument('result', type=dict, location='json', required=False)
statement_parser.add_argument('timestamp', required=False)

class StatementAPI(Resource):
    @login_required
    def post(self):
        if not XAPI.enabled():
            # this should silently fail
            abort(404)

        params = statement_parser.parse_args()

        statement = XAPIStatement.generate_from_params(current_user, params)
        XAPI.send_statement(statement)

        return { 'success': True }

api.add_resource(StatementAPI, '')