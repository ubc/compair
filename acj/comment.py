from bouncer.constants import CREATE, READ, EDIT, DELETE
from flask import Blueprint
from flask.ext.bouncer import ensure
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from acj import dataformat, db
from acj.authorization import require, allow
from acj.models import Posts, PostsForComments, PostsForAnswers, PostsForQuestions, Courses, PostsForQuestionsAndPostsForComments, PostsForAnswersAndPostsForComments, CoursesAndUsers
from acj.util import new_restful_api

commentsforquestions_api = Blueprint('commentsforquestions_api', __name__)
apiQ = new_restful_api(commentsforquestions_api)

commentsforanswers_api = Blueprint('commentsforanswers_api', __name__)
apiA = new_restful_api(commentsforanswers_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('content', type=str, required=True)

existing_comment_parser = RequestParser()
existing_comment_parser.add_argument('id', type=int, required=True, help="Comment id is required.")
existing_comment_parser.add_argument('content', type=str, required=True)

# /
class QuestionCommentRootAPI(Resource):
	#TODO pagination
	@login_required
	def get(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course_id))
		comments = PostsForQuestionsAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForQuestionsAndPostsForComments.postsforquestions_id==question.id, Posts.courses_id==course_id).\
			order_by(Posts.created.desc()).all()
		return {"objects":marshal(comments, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments(restrict_users))}
	@login_required
	def post(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		commentForQuestion = PostsForQuestionsAndPostsForComments(postsforcomments=comment, postsforquestions_id=question_id)
		require(CREATE, commentForQuestion)
		params = new_comment_parser.parse_args()
		post.content = params.get("content")
		if not post.content:
			return {"error":"The comment content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		db.session.add(comment)
		db.session.add(commentForQuestion)
		db.session.commit()
		return marshal(commentForQuestion, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
apiQ.add_resource(QuestionCommentRootAPI, '')

# / id
class QuestionCommentIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, comment_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(READ, comment)
		return marshal(comment, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
	@login_required
	def post(self, course_id, question_id, comment_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(EDIT, comment)
		params = existing_comment_parser.parse_args()
		# make sure the comment id in the rul and the id matches
		if params['id'] != comment.id:
			return {"error":"Comment id does not match URL."}, 400
		# modify comment according to new values, preserve original values if values not passed
		comment.postsforcomments.post.content = params.get("content")
		if not comment.postsforcomments.post.content:
			return {"error":"The comment content is empty!"}, 400
		db.session.add(comment.postsforcomments.post)
		db.session.commit()
		return marshal(comment, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
	@login_required
	def delete(self, course_id, question_id, comment_id):
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(DELETE, comment)
		db.session.delete(comment)
		db.session.commit()
		return {'id': comment.id}
apiQ.add_resource(QuestionCommentIdAPI, '/<int:comment_id>')

# /
class AnswerCommentRootAPI(Resource):
	#TODO pagination
	@login_required
	def get(self, course_id, question_id, answer_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		comments = PostsForAnswersAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForAnswersAndPostsForComments.postsforanswers_id==answer.id, Posts.courses_id==course_id).\
			order_by(Posts.created.desc()).all()
		return {"objects":marshal(comments, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())}

	@login_required
	def post(self, course_id, question_id, answer_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		commentForAnswer = PostsForAnswersAndPostsForComments(postsforcomments=comment, postsforanswers_id=answer.id)
		require(CREATE, commentForAnswer)
		params = new_comment_parser.parse_args()
		post.content = params.get("content")
		if not post.content:
			return {"error":"The comment content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		db.session.add(comment)
		db.session.add(commentForAnswer)
		db.session.commit()
		return marshal(commentForAnswer, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
apiA.add_resource(AnswerCommentRootAPI, '')

# / id
class AnswerCommentIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, answer_id, comment_id):
		course = Courses.query.get_or_404(course_id)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(READ, comment)
		return marshal(comment, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
	@login_required
	def post(self, course_id, question_id, answer_id, comment_id):
		course = Courses.query.get_or_404(course_id)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(EDIT, comment)
		params = existing_comment_parser.parse_args()
		# make sure the comment id in the rul and the id matches
		if params['id'] != comment.id:
			return {"error":"Comment id does not match URL."}, 400
		# modify comment according to new values, preserve original values if values not passed
		comment.postsforcomments.post.content = params.get("content")
		if not comment.postsforcomments.post.content:
			return {"error":"The comment content is empty!"}, 400
		db.session.add(comment.postsforcomments.post)
		db.session.commit()
		return marshal(comment, dataformat.getPostsForQuestionsOrAnswersAndPostsForComments())
	@login_required
	def delete(self, course_id, question_id, answer_id, comment_id):
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(DELETE, comment)
		db.session.delete(comment)
		db.session.commit()
		return {'id': comment.id}
apiA.add_resource(AnswerCommentIdAPI, '/<int:comment_id>')
