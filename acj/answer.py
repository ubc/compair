from bouncer.constants import CREATE, READ, EDIT, MANAGE, DELETE
from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import func

from . import dataformat
from .core import db
from .authorization import require, allow, is_user_access_restricted
from .models import Posts, PostsForAnswers, PostsForQuestions, Courses, Users, \
	Judgements, AnswerPairings
from .util import new_restful_api, get_model_changes
from .attachment import addNewFile, deleteFile
from .core import event


answers_api = Blueprint('answers_api', __name__)
api = new_restful_api(answers_api)

all_answers_api = Blueprint('all_answers_api', __name__)
apiAll = new_restful_api(all_answers_api)

new_answer_parser = RequestParser()
new_answer_parser.add_argument('user', type=int, default=None)
new_answer_parser.add_argument('post', type=dict, default={})
new_answer_parser.add_argument('name', type=str, default=None)
new_answer_parser.add_argument('alias', type=str, default=None)

existing_answer_parser = RequestParser()
existing_answer_parser.add_argument('id', type=int, required=True, help="Answer id is required.")
existing_answer_parser.add_argument('post', type=dict, default={})
existing_answer_parser.add_argument('name', type=str, default=None)
existing_answer_parser.add_argument('alias', type=str, default=None)
existing_answer_parser.add_argument('uploadedFile', type=bool, default=False)

flag_parser = RequestParser()
flag_parser.add_argument('flagged', type=bool, required=True,
	help="Expected boolean value 'flagged' is missing.")


# events
on_answer_modified = event.signal('ANSWER_MODIFIED')
on_answer_get = event.signal('ANSWER_GET')
on_answer_list_get = event.signal('ANSWER_LIST_GET')
on_answer_create = event.signal('ANSWER_CREATE')
on_answer_delete = event.signal('ANSWER_DELETE')
on_answer_flag = event.signal('ANSWER_FLAG')
on_user_question_answer_get = event.signal('USER_QUESTION_ANSWER_GET')
on_user_question_answered_count = event.signal('USER_QUESTION_ANSWERED_COUNT')
on_user_course_answered_count = event.signal('USER_COURSE_ANSWERED_COUNT')
on_answer_view_count = event.signal('ANSWER_VIEW_COUNT')

answer_deadline_message = 'Answer deadline has passed.'

# /
class AnswerRootAPI(Resource):
	#TODO pagination
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		restrict_users = not allow(MANAGE, question)

		answers = PostsForAnswers.query.filter_by(questions_id=question.id) \
			.join(Posts).order_by(Posts.created.desc()).all()

		on_answer_list_get.send(
			current_app._get_current_object(),
			event_name=on_answer_list_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id})

		return {"objects": marshal(answers, dataformat.getPostsForAnswers(restrict_users))}

	@login_required
	def post(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		if not question.answer_grace and not allow(MANAGE, question):
			return {'error':answer_deadline_message}, 403
		post = Posts(courses_id=course_id)
		answer = PostsForAnswers(post=post, questions_id=question_id)
		require(CREATE, answer)
		params = new_answer_parser.parse_args()
		post.content = params.get("post").get("content")
		name = params.get('name')
		if not (post.content or name):
			return {"error":"The answer content is empty!"}, 400
		prev_answer = PostsForAnswers.query.filter_by(questions_id=question_id).join(Posts).filter(Posts.users_id==current_user.id).first()
		if prev_answer:
			return {"error":"An answer has already been submitted"}, 400
		user = params.get("user")
		post.users_id = user if user else current_user.id
		db.session.add(post)
		db.session.add(answer)

		on_answer_create.send(
			current_app._get_current_object(),
			event_name=on_answer_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(answer, dataformat.getPostsForAnswers(False)))

		db.session.commit()
		if name:
			addNewFile(params.get('alias'), name, course_id, question_id, post.id)
		return marshal(answer, dataformat.getPostsForAnswers())
api.add_resource(AnswerRootAPI, '')

# /id
class AnswerIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id, answer_id):
		course = Courses.query.get_or_404(course_id)
		answer = PostsForAnswers.query.get_or_404(answer_id)
		require(READ, answer)

		on_answer_get.send(
			current_app._get_current_object(),
			event_name=on_answer_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'answer_id': answer_id})

		return marshal(answer, dataformat.getPostsForAnswers(True, False))

	@login_required
	def post(self, course_id, question_id, answer_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		if not question.answer_grace and not allow(MANAGE, question):
			return {'error':answer_deadline_message}, 403
		answer = PostsForAnswers.query.get_or_404(answer_id)
		require(EDIT, answer)
		params = existing_answer_parser.parse_args()
		# make sure the answer id in the url and the id matches
		if params['id'] != answer_id:
			return {"error":"Answer id does not match the URL."}, 400
		# modify answer according to new values, preserve original values if values not passed
		answer.post.content = params.get("post").get("content")
		uploaded = params.get('uploadFile')
		name = params.get('name')
		if not (answer.post.content or uploaded or name):
			return {"error":"The answer content is empty!"}, 400
		db.session.add(answer.post)
		db.session.add(answer)

		on_answer_modified.send(
			current_app._get_current_object(),
			event_name=on_answer_modified.name,
			user=current_user,
			course_id=course_id,
			data=get_model_changes(answer))

		db.session.commit()
		if name:
			addNewFile(params.get('alias'), name, course_id, question_id, answer.post.id)
		return marshal(answer, dataformat.getPostsForAnswers())
	@login_required
	def delete(self, course_id, question_id, answer_id):
		answer = PostsForAnswers.query.get_or_404(answer_id)
		require(DELETE, answer)
		deleteFile(answer.post.id)
		db.session.delete(answer)
		db.session.commit()

		on_answer_delete.send(
			current_app._get_current_object(),
			event_name=on_answer_delete.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'answer_id': answer_id})

		return {'id': answer.id}
api.add_resource(AnswerIdAPI, '/<int:answer_id>')

# /user
class AnswerUserIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		answer = PostsForAnswers.query.filter_by(questions_id=question_id).join(Posts).\
			filter_by(courses_id=course_id, users_id=current_user.id).all()

		on_user_question_answer_get.send(
			current_app._get_current_object(),
			event_name=on_user_question_answer_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id':question_id})

		return {'answer': marshal(answer, dataformat.getPostsForAnswers(True, False))}
api.add_resource(AnswerUserIdAPI, '/user')

# /flag, mark an answer as inappropriate or incomplete to instructors
class AnswerFlagAPI(Resource):
	@login_required
	def post(self, course_id, question_id, answer_id):
		answer = PostsForAnswers.query.get_or_404(answer_id)
		require(READ, answer)
		# anyone can flag an answer, but only the original flagger or someone who can manage
		# the answer can unflag it
		if answer.flagged and \
			answer.flagger.id != current_user.id and \
			not allow(MANAGE, answer):
			return {"error":"You do not have permission to unflag this answer."}, 400
		params = flag_parser.parse_args()
		answer.flagged = params['flagged']
		answer.users_id_flagger = current_user.id
		db.session.add(answer)

		on_answer_flag.send(
			current_app._get_current_object(),
			event_name=on_answer_flag.name,
			user=current_user,
			course_id=course_id,
			question_id=question_id,
			data={'answer_id': answer_id, 'flag': answer.flagged})

		db.session.commit()
		return marshal(answer,
			dataformat.getPostsForAnswers(restrict_users=is_user_access_restricted(current_user)))
api.add_resource(AnswerFlagAPI, '/<int:answer_id>/flagged')

# /count, return number of answers submitted for the question
class AnswerCountAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		PostsForQuestions.query.get_or_404(question_id)
		post = Posts(courses_id=course_id)
		answer = PostsForAnswers(post=post)
		require(READ, answer)
		answered = PostsForAnswers.query.filter_by(questions_id=question_id).join(Posts)\
			.filter(Posts.users_id==current_user.id).count()

		on_user_question_answered_count.send(
			current_app._get_current_object(),
			event_name=on_user_question_answered_count.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id})

		return {'answered': answered }
api.add_resource(AnswerCountAPI, '/count')

# /view
class AnswerViewAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)

		if allow(MANAGE, question):
			answers = PostsForAnswers.query.join(Posts).\
				filter(PostsForAnswers.questions_id==question.id).\
				order_by(Posts.created.desc()).all()
		else:
			judgements = Judgements.query \
				.filter_by(users_id=current_user.id) \
				.join(AnswerPairings).filter_by(questions_id=question.id).all()
			myanswers = PostsForAnswers.query.filter_by(questions_id=question.id) \
				.join(Posts).filter_by(users_id=current_user.id).all()
			answerIds = set(j.answerpairing.answers_id1 for j in judgements)
			answerIds.update(set(j.answerpairing.answers_id2 for j in judgements))
			answers = []
			if len(answerIds) > 0:
				answers = PostsForAnswers.query.filter(PostsForAnswers.id.in_(answerIds)).all()
			answers.extend(myanswers)

		results = {}
		canManage = allow(MANAGE, question)
		for ans in answers:
			tmp_answer = results.setdefault(ans.id, {})
			tmp_answer['id'] = ans.id
			tmp_answer['content'] = ans.post.content
			tmp_answer['file'] = marshal(ans.post.files, dataformat.getFilesForPosts())
			if canManage:
				tmp_answer['scores'] = {s.criteriaandquestions_id: round(s.normalized_score, 3)
										for s in ans._scores if s.question_criterion.active}

		on_answer_view_count.send(
			current_app._get_current_object(),
			event_name=on_answer_view_count.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id}
		)

		return {'answers': results}
api.add_resource(AnswerViewAPI, '/view')

class AnsweredAPI(Resource):
	@login_required
	def get(self, course_id):
		Courses.query.get_or_404(course_id)
		post = Posts(courses_id=course_id)
		answer = PostsForAnswers(post=post)
		require(READ, answer)
		answered = PostsForAnswers.query.with_entities(PostsForAnswers.questions_id, func.count(PostsForAnswers.id)).join(Posts)\
			.filter_by(courses_id=course_id).join(Users).filter_by(id=current_user.id).group_by(PostsForAnswers.questions_id).all()
		answered = {qId: count for (qId, count) in answered}

		on_user_course_answered_count.send(
			current_app._get_current_object(),
			event_name=on_user_course_answered_count.name,
			user=current_user,
			course_id=course_id)

		return {'answered': answered}
apiAll.add_resource(AnsweredAPI, '/answered')