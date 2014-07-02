from bouncer.constants import READ, EDIT, CREATE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import desc
from acj import dataformat, db
from acj.authorization import allow, require
from acj.models import PostsForQuestions, Courses, Posts, CoursesAndUsers
from acj.util import new_restful_api

questions_api = Blueprint('questions_api', __name__)
api = new_restful_api(questions_api)

new_question_parser = RequestParser()
new_question_parser.add_argument('title', type=str, required=True, help="Question title is required.")
new_question_parser.add_argument('post', type=dict, default={})

# /id
class QuestionIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		if not question_id:
			question_id = 1
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		return marshal(question, dataformat.getPostsForQuestions())
api.add_resource(QuestionIdAPI, '/<int:question_id>')

# /
class QuestionRootAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		# Get all questions for this course, default order is most recent first
		questions = PostsForQuestions.query.join(Posts).filter(Posts.courses_id==course_id). \
			order_by(desc(Posts.created)).all()

		restrict_users = allow(EDIT, CoursesAndUsers(courses_id=course_id))
		return {"objects":marshal(questions, dataformat.getPostsForQuestions(restrict_users))}
	@login_required
	def post(self, course_id):
		# check permission first before reading parser arguments
		post = Posts(courses_id=course_id)
		require(CREATE, post)
		params = new_question_parser.parse_args()
		post.content = params.get("post").get("content")
		if not post.content:
			return {"error":"The answer content is empty!"}, 400
		post.users_id = current_user.id
		db.session.add(post)
		question = PostsForQuestions(post=post, title=params.get("title"))
		db.session.add(question)
		db.session.commit()
		return marshal(question, dataformat.getPostsForQuestions())
api.add_resource(QuestionRootAPI, '')
