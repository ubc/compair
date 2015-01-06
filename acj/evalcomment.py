from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from bouncer.constants import EDIT, CREATE, MANAGE

from . import dataformat
from .core import db, event
from .models import Judgements, PostsForComments, PostsForJudgements, Courses, PostsForQuestions, Posts, \
	AnswerPairings, CoursesAndUsers, CriteriaAndCourses, CriteriaAndPostsForQuestions, Users, \
	PostsForAnswersAndPostsForComments, PostsForAnswers
from .util import new_restful_api
from .authorization import allow, require

from operator import itemgetter
from itertools import groupby

evalcomments_api = Blueprint('evalcomments_api', __name__)
api = new_restful_api(evalcomments_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('judgements', type=list, required=True)
new_comment_parser.add_argument('selfeval', type=bool, required=False, default=False)

# events
on_evalcomment_create = event.signal('EVALCOMMENT_CREATE')
on_evalcomment_get = event.signal('EVALCOMMENT_GET')
on_evalcomment_view = event.signal('EVALCOMMENT_VIEW')

# /
class EvalCommentRootAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		judgementComment = PostsForJudgements(postsforcomments=comment)
		require(MANAGE, judgementComment)
		comments = PostsForJudgements.query\
			.join(Judgements, AnswerPairings).filter_by(questions_id=question.id)\
			.join(PostsForComments, Posts, Users).order_by(Users.firstname, Users.lastname, Users.id).all()
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course.id))

		on_evalcomment_get.send(
			current_app._get_current_object(),
			event_name=on_evalcomment_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id}
		)

		return {'comments': marshal(comments, dataformat.getPostsForJudgements(restrict_users))}
	@login_required
	def post(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		criteriaAndQuestions = CriteriaAndPostsForQuestions(question=question)
		judgements = Judgements(question_criterion=criteriaAndQuestions)
		require(CREATE, judgements)
		params = new_comment_parser.parse_args()
		results = []
		for judgement in params['judgements']:
			judge = Judgements.query.get_or_404(judgement['id'])
			post = Posts(courses_id=course_id)
			post.content = judgement['comment']
			post.users_id = current_user.id
			comment = PostsForComments(post=post)
			selfeval = params.get('selfeval', False)
			evalcomment = PostsForJudgements(postsforcomments=comment, judgements_id=judge.id, selfeval=selfeval)
			db.session.add(post)
			db.session.add(comment)
			db.session.add(evalcomment)
			db.session.commit()
			results.append(evalcomment)

		on_evalcomment_create.send(
			current_app._get_current_object(),
			event_name=on_evalcomment_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(results, dataformat.getPostsForJudgements(False)))

		return {'objects': marshal(results, dataformat.getPostsForJudgements())}
api.add_resource(EvalCommentRootAPI, '')

# /view
class EvalCommentViewAPI(Resource):
	@login_required
	def get(selfself, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		judgementComment = PostsForJudgements(postsforcomments=comment)
		require(MANAGE, judgementComment)

		evalcomments = PostsForJudgements.query\
			.join(Judgements, AnswerPairings).filter_by(questions_id=question.id)\
			.join(PostsForComments, Posts, Users).order_by(Users.firstname, Users.lastname, Users.id).all()

		feedback = PostsForAnswersAndPostsForComments.query.join(PostsForAnswers) \
			.filter_by(questions_id=question.id)\
			.order_by(PostsForAnswersAndPostsForComments.evaluation).all()

		replies = {}
		for f in feedback:
			if f.users_id not in replies:
				replies[f.users_id] = {}
			replies[f.users_id][f.postsforanswers_id] = f.content

		selfeval = []
		if question.selfevaltype_id:
			# assume no comparison self evaluation
			selfeval = PostsForAnswersAndPostsForComments.query.filter_by(selfeval=True)\
				.join(PostsForAnswers).filter_by(questions_id=question.id).all()

		results = []
		for comment in evalcomments:
			user_id = comment.postsforcomments.post.users_id
			fullname = comment.postsforcomments.post.user.fullname
			temp_comment = {'answer1': {}, 'answer2': {}, 'user_id': user_id}
			temp_comment['name'] = fullname if fullname else comment.postsforcomments.post.user.displayname
			temp_comment['avatar'] = comment.postsforcomments.post.user.avatar
			temp_comment['criteriaandquestions_id'] = comment.judgement.criteriaandquestions_id
			temp_comment['answerpairings_id'] = comment.judgement.answerpairings_id
			temp_comment['content'] = comment.postsforcomments.post.content
			temp_comment['selfeval'] = False
			temp_comment['created'] = str(comment.postsforcomments.post.created)
			temp_comment['answer1']['id'] = comment.judgement.answerpairing.postsforanswers_id1
			temp_comment['answer1']['feedback'] = replies[user_id][temp_comment['answer1']['id']]
			temp_comment['answer2']['id'] = comment.judgement.answerpairing.postsforanswers_id2
			temp_comment['answer2']['feedback'] = replies[user_id][temp_comment['answer2']['id']]
			temp_comment['winner'] = comment.judgement.postsforanswers_id_winner
			results.append(temp_comment)

		for s in selfeval:
			fullname = s.postsforcomments.post.user.fullname
			name = fullname if fullname else comment.postsforcomments.post.user.displayname
			comment = {
				'user_id': s.users_id,
				'name': name,
				'avatar': s.postsforcomments.post.user.avatar,
				'answerpairings_id': 0,
				'criteriaandquestions_id': 0,
				'content': s.content,
				'selfeval': True,
				'created': str(s.postsforcomments.post.created)
			}
			results.append(comment)

		# sort by criteria id to keep the evaluation results in a constant order
		results.sort(key = itemgetter('criteriaandquestions_id'))
		# sort by answerpairings_id in descending order first
		# group by answerpairing and keep the selfevaluation as the last comment
		results.sort(key = itemgetter('answerpairings_id'), reverse=True)
		# then sort by name and user_id to group the comments by author
		results.sort(key = itemgetter('name', 'user_id'))

		comparisons = []
		for k, g in groupby(results, itemgetter('name', 'user_id', 'answerpairings_id')):
			comparisons.append(list(g))

		on_evalcomment_view.send(
			current_app._get_current_object(),
			event_name=on_evalcomment_view.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id}
		)
		return {'comparisons': comparisons}

api.add_resource(EvalCommentViewAPI, '/view')
