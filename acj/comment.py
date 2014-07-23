from bouncer.constants import CREATE, READ, EDIT
from flask import Blueprint
from flask.ext.bouncer import ensure
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from acj import dataformat, db
from acj.authorization import require
from acj.models import Posts, PostsForComments, PostsForAnswers, PostsForQuestions, Courses, PostsForQuestionsAndPostsForComments, PostsForAnswersAndPostsForComments
from acj.util import new_restful_api

commentsforquestions_api = Blueprint('commentsforquestions_api', __name__)
apiQ = new_restful_api(commentsforquestions_api)

commentsforanswers_api = Blueprint('commentsforanswers_api', __name__)
apiA = new_restful_api(commentsforanswers_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('post', type=dict, default={})

# /
class QuestionCommentRootAPI(Resource):
	#TODO pagination
	@login_required
	def get(self, course_id, question_id):
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		comments = PostsForQuestionsAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForQuestionsAndPostsForComments.postsforquestions_id==question.id, Posts.courses_id==course_id).\
			order_by(Posts.created.desc()).all()
		return {"objects":marshal(comments, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())}
	@login_required
	def post(self, course_id, question_id):
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		commentForQuestion = PostsForQuestionsAndPostsForComments(postsforcomments=comment, postsforquestions_id=question_id)
		require(CREATE, commentForQuestion)
		params = new_comment_parser.parse_args()
		post.content = params.get("post").get("content")
		if not post.content:
			return {"error":"The comment content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		db.session.add(comment)
		db.session.add(commentForQuestion)
		db.session.commit()
		return marshal(commentForQuestion, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
apiQ.add_resource(QuestionCommentRootAPI, '')

# /
class AnswerCommentRootAPI(Resource):
	#TODO pagination
	@login_required
	def get(self, course_id, question_id, answer_id):
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		comments = PostsForQuestionsAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForQuestionsAndPostsForComments.postsforquestions_id==question.id, Posts.courses_id==course_id).\
			order_by(Posts.created.desc()).all()
		return {"objects":marshal(comments, dataformat.getPostsforQuestionsOrAnswersAndPostsForComments())}

	@login_required
	def post(self, course_id, question_id, answer_id):
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		commentForAnswer = PostsForAnswersAndPostsForComments(postsforcomments=comment, postsforanswers_id=answer_id)
		require(CREATE, commentForAnswer)
		params = new_comment_parser.parse_args()
		post.content = params.get("post").get("content")
		if not post.content:
			return {"error":"The comment content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		db.session.add(comment)
		db.session.add(commentForAnswer)
		db.session.commit()
		return marshal(commentForAnswer, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
apiA.add_resource(AnswerCommentRootAPI, '')

