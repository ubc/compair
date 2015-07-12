from operator import itemgetter
from itertools import groupby

from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser

from bouncer.constants import READ, EDIT, CREATE, MANAGE

from . import dataformat
from .core import db, event
from .models import Judgements, PostsForComments, PostsForJudgements, Courses, PostsForQuestions, Posts, \
	AnswerPairings, CoursesAndUsers, CriteriaAndPostsForQuestions, Users, \
	PostsForAnswersAndPostsForComments, PostsForAnswers
from .util import new_restful_api
from .authorization import allow, require

evalcomments_api = Blueprint('evalcomments_api', __name__)
api = new_restful_api(evalcomments_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('judgements', type=list, required=True)
new_comment_parser.add_argument('selfeval', type=bool, required=False, default=False)

# events
on_evalcomment_create = event.signal('EVALCOMMENT_CREATE')
on_evalcomment_get = event.signal('EVALCOMMENT_GET')
on_evalcomment_view = event.signal('EVALCOMMENT_VIEW')
on_evalcomment_view_my = event.signal('EVALCOMMENT_VIEW_MY')


# /
class EvalCommentRootAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		post = Posts(courses_id=course_id)
		comment = PostsForComments(post=post)
		judgement_comment = PostsForJudgements(postsforcomments=comment)
		require(MANAGE, judgement_comment)
		comments = PostsForJudgements.query \
			.join(Judgements, AnswerPairings).filter_by(questions_id=question.id) \
			.join(PostsForComments, Posts, Users).order_by(Users.firstname, Users.lastname, Users.id).all()
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course.id))

		on_evalcomment_get.send(
			self,
			event_name=on_evalcomment_get.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id}
		)

		return {'comments': marshal(comments, dataformat.get_posts_for_judgements(restrict_users))}

	@login_required
	def post(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		criteria_and_questions = CriteriaAndPostsForQuestions(question=question)
		judgements = Judgements(question_criterion=criteria_and_questions)
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
			self,
			event_name=on_evalcomment_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(results, dataformat.get_posts_for_judgements(False)))

		return {'objects': marshal(results, dataformat.get_posts_for_judgements())}


api.add_resource(EvalCommentRootAPI, '')


# /view
class EvalCommentViewAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		comment = PostsForComments(post=Posts(courses_id=course_id))
		can_manage = allow(MANAGE, PostsForJudgements(postsforcomments=comment))

		if can_manage:
			evalcomments = PostsForJudgements.query \
				.join(Judgements, AnswerPairings).filter_by(questions_id=question.id) \
				.join(PostsForComments, Posts, Users).order_by(Users.firstname, Users.lastname, Users.id).all()

			feedback = PostsForAnswersAndPostsForComments.query.join(PostsForAnswers) \
				.filter_by(questions_id=question.id) \
				.order_by(PostsForAnswersAndPostsForComments.evaluation).all()
		else:
			evalcomments = PostsForJudgements.query \
				.join(Judgements, AnswerPairings).filter_by(questions_id=question.id) \
				.join(PostsForComments, Posts).filter_by(users_id=current_user.id).all()

			feedback = PostsForAnswersAndPostsForComments.query \
				.join(PostsForAnswers).filter_by(questions_id=question.id) \
				.join(PostsForComments, Posts).filter_by(users_id=current_user.id) \
				.order_by(PostsForAnswersAndPostsForComments.evaluation).all()

		replies = {}
		selfeval = [f for f in feedback if f.selfeval]
		for f in feedback:
			replies.setdefault(f.users_id, {}).setdefault(f.answers_id, f.content)

		results = []
		deleted = '<i>(This feedback has been deleted)</i>'
		for comment in evalcomments:
			com = comment.postsforcomments.post
			judge = comment.judgement
			user_id = com.users_id
			fullname = com.user.fullname
			if user_id in replies and judge.answerpairing.answers_id1 in replies[user_id]:
				feedback1 = replies[user_id][judge.answerpairing.answers_id1]
			else:
				feedback1 = deleted
			if user_id in replies and judge.answerpairing.answers_id2 in replies[user_id]:
				feedback2 = replies[user_id][judge.answerpairing.answers_id2]
			else:
				feedback2 = deleted
			temp_comment = {
				'answer1': {'id': judge.answerpairing.answers_id1, 'feedback': feedback1},
				'answer2': {'id': judge.answerpairing.answers_id2, 'feedback': feedback2},
				'user_id': user_id,
				'selfeval': False,
				'name': fullname if fullname else com.user.displayname,
				'avatar': com.user.avatar,
				'criteriaandquestions_id': judge.criteriaandquestions_id,
				'answerpairings_id': judge.answerpairings_id,
				'content': com.content,
				'created': com.created,
				'winner': judge.answers_id_winner
			}
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
				'created': s.postsforcomments.post.created
			}
			results.append(comment)

		# sort by criteria id to keep the evaluation results in a constant order
		results.sort(key=itemgetter('criteriaandquestions_id'))
		# sort by answerpairings_id in descending order first
		# group by answerpairing and keep the selfevaluation as the last comment
		results.sort(key=itemgetter('answerpairings_id'), reverse=True)
		# then sort by name and user_id to group the comments by author
		if can_manage:
			results.sort(key=itemgetter('name', 'user_id'))

		comparisons = []
		for k, g in groupby(results, itemgetter('name', 'user_id', 'answerpairings_id')):
			comparisons.append(list(g))

		on_evalcomment_view.send(
			self,
			event_name=on_evalcomment_view.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id}
		)

		return {'comparisons': marshal(comparisons, dataformat.get_eval_comments())}


api.add_resource(EvalCommentViewAPI, '/view')
