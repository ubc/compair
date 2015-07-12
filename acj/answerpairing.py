from flask import Blueprint
from flask.ext.restful import Resource
from flask_login import login_required

from .util import new_restful_api

answerpairing_api = Blueprint('answerpairing_api', __name__)
api = new_restful_api(answerpairing_api)

# TODO: events


# /
class AnswerPairingListAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		return {"error": "The function is currently unavailable"}, 404

api.add_resource(AnswerPairingListAPI, '')
