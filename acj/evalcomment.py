from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser

from . import dataformat
from .core import db
from .models import Judgements, PostsForComments, PostsForJudgements, Courses, PostsForQuestions, Posts
from .util import new_restful_api


evalcomments_api = Blueprint('evalcomments_api', __name__)
api = new_restful_api(evalcomments_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('judgements', type=list, required=True)

# /
class EvalCommentRootAPI(Resource):
	@login_required
	def post(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		params = new_comment_parser.parse_args()
		judgements = params['judgements']
		results = []
		for judgement in params['judgements']:
			judge = Judgements.query.get_or_404(judgement['id'])
			post = Posts(courses_id=course_id)
			post.content = judgement['comment'];
			post.users_id = current_user.id
			comment = PostsForComments(post=post)
			evalcomment = PostsForJudgements(postsforcomments=comment, judgements_id=judge.id)
			db.session.add(post)
			db.session.add(comment)
			db.session.add(evalcomment)
			db.session.commit()
			results.append(evalcomment)
		return {'objects': marshal(results, dataformat.getPostsForJudgements())}
api.add_resource(EvalCommentRootAPI, '')
