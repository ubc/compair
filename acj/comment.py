from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy.orm import load_only

from . import dataformat
from .core import db
from .authorization import require, allow
from .core import event
from .models import Posts, PostsForComments, PostsForAnswers, \
	PostsForQuestions, Courses, PostsForQuestionsAndPostsForComments, \
	PostsForAnswersAndPostsForComments
from .util import new_restful_api, get_model_changes

commentsforquestions_api = Blueprint('commentsforquestions_api', __name__)
apiQ = new_restful_api(commentsforquestions_api)

commentsforanswers_api = Blueprint('commentsforanswers_api', __name__)
apiA = new_restful_api(commentsforanswers_api)

usercommentsforanswers_api = Blueprint('usercommentsforanswers_api', __name__)
apiU = new_restful_api(usercommentsforanswers_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('content', type=str, required=True)
new_comment_parser.add_argument('selfeval', type=bool, required=False, default=False)
new_comment_parser.add_argument('evaluation', type=bool, required=False, default=False)
new_comment_parser.add_argument('type', type=int, default=0)

existing_comment_parser = RequestParser()
existing_comment_parser.add_argument('id', type=int, required=True, help="Comment id is required.")
existing_comment_parser.add_argument('content', type=str, required=True)
existing_comment_parser.add_argument('type', type=int, default=0)

# events
on_comment_modified = event.signal('COMMENT_MODIFIED')
on_comment_get = event.signal('COMMENT_GET')
on_comment_list_get = event.signal('COMMENT_LIST_GET')
on_comment_create = event.signal('COMMENT_CREATE')
on_comment_delete = event.signal('COMMENT_DELETE')

on_answer_comment_modified = event.signal('ANSWER_COMMENT_MODIFIED')
on_answer_comment_get = event.signal('ANSWER_COMMENT_GET')
on_answer_comment_list_get = event.signal('ANSWER_COMMENT_LIST_GET')
on_answer_comment_create = event.signal('ANSWER_COMMENT_CREATE')
on_answer_comment_delete = event.signal('ANSWER_COMMENT_DELETE')
on_answer_comment_user_get = event.signal('ANSWER_COMMENT_USER_GET')


# /
class QuestionCommentRootAPI(Resource):
	# TODO pagination
	@login_required
	def get(self, course_id, question_id):
		Courses.query.options(load_only('id')).get_or_404(course_id)
		question = PostsForQuestions.query. \
			options(load_only('id', 'criteria_count', 'posts_id')). \
			get_or_404(question_id)
		require(READ, question)
		restrict_users = not allow(MANAGE, question)
		comments = PostsForQuestionsAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForQuestionsAndPostsForComments.questions_id == question.id, Posts.courses_id == course_id).\
			order_by(Posts.created.asc()).all()

		on_comment_list_get.send(
			self,
			event_name=on_comment_list_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id})

		return {"objects": marshal(comments, dataformat.get_posts_for_questions_and_posts_for_comments(restrict_users))}

	@login_required
	def post(self, course_id, question_id):
		Courses.query.options(load_only('id')).get_or_404(course_id)
		PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		comment_for_question = PostsForQuestionsAndPostsForComments(postsforcomments=comment, questions_id=question_id)
		require(CREATE, comment_for_question)
		params = new_comment_parser.parse_args()
		post.content = params.get("content")
		if not post.content:
			return {"error": "The comment content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		db.session.add(comment)
		db.session.add(comment_for_question)

		on_comment_create.send(
			self,
			event_name=on_comment_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(comment_for_question, dataformat.get_posts_for_questions_and_posts_for_comments(False)))

		db.session.commit()
		return marshal(comment_for_question, dataformat.get_posts_for_questions_and_posts_for_comments())

apiQ.add_resource(QuestionCommentRootAPI, '')


# / id
class QuestionCommentIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, comment_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(READ, comment)

		on_comment_get.send(
			self,
			event_name=on_comment_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'comment_id': comment_id})

		return marshal(comment, dataformat.get_posts_for_questions_and_posts_for_comments())

	@login_required
	def post(self, course_id, question_id, comment_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(EDIT, comment)
		params = existing_comment_parser.parse_args()
		# make sure the comment id in the rul and the id matches
		if params['id'] != comment.id:
			return {"error": "Comment id does not match URL."}, 400
		# modify comment according to new values, preserve original values if values not passed
		comment.postsforcomments.post.content = params.get("content")
		if not comment.postsforcomments.post.content:
			return {"error": "The comment content is empty!"}, 400
		db.session.add(comment.postsforcomments.post)

		on_comment_modified.send(
			self,
			event_name=on_comment_modified.name,
			user=current_user,
			course_id=course_id,
			data=get_model_changes(comment.postsforcomments.post))

		db.session.commit()
		return marshal(comment, dataformat.get_posts_for_questions_and_posts_for_comments())

	@login_required
	def delete(self, course_id, question_id, comment_id):
		comment = PostsForQuestionsAndPostsForComments.query.get_or_404(comment_id)
		require(DELETE, comment)
		data = marshal(comment, dataformat.get_posts_for_questions_and_posts_for_comments(False))
		db.session.delete(comment)
		db.session.commit()

		on_comment_delete.send(
			self,
			event_name=on_comment_delete.name,
			user=current_user,
			course_id=course_id,
			data=data)

		return {'id': comment.id}
apiQ.add_resource(QuestionCommentIdAPI, '/<int:comment_id>')


# /
class AnswerCommentRootAPI(Resource):
	# TODO pagination
	@login_required
	def get(self, course_id, question_id, answer_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		comments = PostsForAnswersAndPostsForComments.query.\
			join(PostsForComments, Posts).\
			filter(PostsForAnswersAndPostsForComments.answers_id == answer.id, Posts.courses_id == course_id).\
			order_by(Posts.created.desc()).all()

		on_answer_comment_list_get.send(
			self,
			event_name=on_answer_comment_list_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'answer_id': answer_id})

		return {"objects": marshal(comments, dataformat.get_posts_for_answers_and_posts_for_comments())}

	@login_required
	def post(self, course_id, question_id, answer_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		comment_for_answer = PostsForAnswersAndPostsForComments(postsforcomments=comment, answers_id=answer.id)
		require(CREATE, comment_for_answer)
		params = new_comment_parser.parse_args()
		post.content = params.get("content")
		if not post.content:
			return {"error": "The comment content is empty!"}, 400
		post.users_id = current_user.id
		comment_for_answer.selfeval = params.get("selfeval", False)
		comment_for_answer.evaluation = params.get("evaluation", False)
		comment_for_answer.type = params.get("type", 0)
		db.session.add(post)
		db.session.add(comment)
		db.session.add(comment_for_answer)

		on_answer_comment_create.send(
			self,
			event_name=on_answer_comment_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(comment_for_answer, dataformat.get_posts_for_answers_and_posts_for_comments(False)))

		db.session.commit()
		return marshal(comment_for_answer, dataformat.get_posts_for_answers_and_posts_for_comments())

apiA.add_resource(AnswerCommentRootAPI, '')


# / id
class AnswerCommentIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, answer_id, comment_id):
		Courses.query.get_or_404(course_id)
		PostsForAnswers.query.get_or_404(answer_id)
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(READ, comment)

		on_answer_comment_get.send(
			self,
			event_name=on_answer_comment_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'answer_id': answer_id, 'comment_id': comment_id})

		return marshal(comment, dataformat.get_posts_for_answers_and_posts_for_comments())

	@login_required
	def post(self, course_id, question_id, answer_id, comment_id):
		Courses.query.get_or_404(course_id)
		PostsForAnswers.query.get_or_404(answer_id)
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(EDIT, comment)
		params = existing_comment_parser.parse_args()
		# make sure the comment id in the rul and the id matches
		if params['id'] != comment.id:
			return {"error": "Comment id does not match URL."}, 400
		# modify comment according to new values, preserve original values if values not passed
		comment.postsforcomments.post.content = params.get("content")
		if not comment.postsforcomments.post.content:
			return {"error": "The comment content is empty!"}, 400
		comment.type = params.get("type")
		db.session.add(comment.postsforcomments.post)

		on_answer_comment_modified.send(
			self,
			event_name=on_answer_comment_modified.name,
			user=current_user,
			course_id=course_id,
			data=get_model_changes(comment.postsforcomments))

		db.session.commit()
		return marshal(comment, dataformat.get_posts_for_answers_and_posts_for_comments())

	@login_required
	def delete(self, course_id, question_id, answer_id, comment_id):
		comment = PostsForAnswersAndPostsForComments.query.get_or_404(comment_id)
		require(DELETE, comment)
		data = marshal(comment, dataformat.get_posts_for_answers_and_posts_for_comments(False))
		db.session.delete(comment)
		db.session.commit()

		on_answer_comment_delete.send(
			self,
			event_name=on_answer_comment_delete.name,
			user=current_user,
			course_id=course_id,
			data=data)

		return {'id': comment.id}

apiA.add_resource(AnswerCommentIdAPI, '/<int:comment_id>')


# /
class UserAnswerCommentIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, answer_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		PostsForAnswers.query.get_or_404(answer_id)
		comments = PostsForAnswersAndPostsForComments.query.filter_by(answers_id=answer_id)\
			.join(PostsForComments, Posts).filter(Posts.users_id == current_user.id).all()

		on_answer_comment_user_get.send(
			self,
			event_name=on_answer_comment_user_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'answer_id': answer_id})

		return {'object': marshal(comments, dataformat.get_posts_for_answers_and_posts_for_comments())}

apiU.add_resource(UserAnswerCommentIdAPI, '')
