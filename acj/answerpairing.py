from flask import Blueprint, current_app
from flask.ext.restful import Resource
from flask_login import login_required

from . import dataformat
from .core import event
from .models import AnswerPairings, Courses, PostsForQuestions
from .util import new_restful_api

answerpairing_api = Blueprint('answerpairing_api', __name__)
api = new_restful_api(answerpairing_api)

# TODO: events

# /
# return : {1: {2,3}, 2:{1}, 3:{1}} - postsforanswers_id
class AnswerPairingListAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		answerpairing = AnswerPairings.query.filter_by(postsforquestions_id=question.id).all()
		result = {}
		for ap in answerpairing:
			if not (ap.postsforanswers_id1 in result):
				result[ap.postsforanswers_id1] = []
			if not (ap.postsforanswers_id2 in result):
				result[ap.postsforanswers_id2] = []
			result[ap.postsforanswers_id1].append(ap.postsforanswers_id2)
			result[ap.postsforanswers_id2].append(ap.postsforanswers_id1)
		return {'answerpairings': result}
api.add_resource(AnswerPairingListAPI, '/list')