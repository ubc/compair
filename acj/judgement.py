from __future__ import division
import operator
import random

from bouncer.constants import READ, CREATE
from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import or_, and_

from . import dataformat
from .core import db
from acj.authorization import require
from .core import event
from .models import PostsForAnswers, Posts, Judgements, AnswerPairings, Courses, \
	PostsForQuestions, Scores, CoursesAndUsers, UserTypesForCourse, CriteriaAndPostsForQuestions
from .util import new_restful_api

# First declare a Flask Blueprint for this module
judgements_api = Blueprint('judgements_api', __name__)
# Then pack the blueprint into a Flask-Restful API
api = new_restful_api(judgements_api)

all_judgements_api = Blueprint('all_judgements_api', __name__)
apiAll = new_restful_api(all_judgements_api)

new_judgement_parser = RequestParser()
new_judgement_parser.add_argument('answerpair_id', type=int, required=True,
								  help="Missing answer pair id.")
new_judgement_parser.add_argument('judgements', type=list, required=True, help="Missing judgements.")


# events
on_answer_pair_get = event.signal('ANSWER_PAIR_GET')
on_judgement_create = event.signal('JUDGEMENT_CREATE')

on_judgement_question_count = event.signal('JUDGEMENT_QUESTION_COUNT')
on_judgement_course_count = event.signal('JUDGEMENT_COURSE_COUNT')

# /
class JudgementRootAPI(Resource):
	@login_required
	def post(self, course_id, question_id):
		'''
		Stores a judgement into the database.
		'''
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		if not question.judging_period:
			return {'error':'Evaluation period is not active.'}, 403
		require(READ, question)
		require(CREATE, Judgements)
		question_criteria = CriteriaAndPostsForQuestions.query.\
			filter_by(question=question, active=True).all()
		params = new_judgement_parser.parse_args()
		answer_pair = AnswerPairings.query.get(params['answerpair_id'])
		if not answer_pair:
			return {"error":"Invalid Answer Pair ID"}, 404
		# check if number of judgements matches number of criteria
		if len(question_criteria) != len(params['judgements']):
			return {"error":"Not all criteria were evaluated."}, 400
		# check if each judgement has an questionCriteria Id and a winner id
		for judgement in params['judgements']:
			if not 'question_criterion_id' in judgement:
				return {"error": "Missing question_criterion_id in evaluation."}, 400
			if not 'answer_id_winner' in judgement:
				return {"error": "Missing selected answer for one of the criteria."}, 400
			# check that we're using criteria that were assigned to the course and that we didn't
			# get duplicate criteria in judgements
			known_criterion = False
			for question_criterion_entry in question_criteria[:]:
				if judgement['question_criterion_id'] == question_criterion_entry.id:
					known_criterion = True
					question_criteria.remove(question_criterion_entry)
			if not known_criterion:
				return {"error": "Unknown criterion submitted in judgement!"}, 400
			# check that the winner id matches one of the answer pairs
			winner_id = judgement['answer_id_winner']
			if winner_id != answer_pair.answer1.id and winner_id != answer_pair.answer2.id:
				return {"error": "Selected answer ID does not match the available pair of answers."}, 400
		# check if pair has already been judged by this user
		if Judgements.query.filter_by(users_id = current_user.id).join(AnswerPairings) \
			.filter(
				or_(
					and_(AnswerPairings.answers_id1 == answer_pair.answers_id1,
						AnswerPairings.answers_id2 == answer_pair.answers_id2),
					and_(AnswerPairings.answers_id1 == answer_pair.answers_id2,
						 AnswerPairings.answers_id2 == answer_pair.answers_id1)
				)
			).first():
			return {"error": "You've already evaluated this pair of answers."}, 400

		# now the real deal, creating the judgement
		judgements = Judgements.create_judgement(params, answer_pair, current_user.id)

		# update answer scores
		current_app.logger.debug("Doing scoring")
		Judgements._calculate_scores(question_id)

		on_judgement_create.send(
			current_app._get_current_object(),
			event_name=on_judgement_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(judgements, dataformat.getJudgements()))

		return {'objects': marshal(judgements, dataformat.getJudgements())}

api.add_resource(JudgementRootAPI, '')

# /pair
class JudgementPairAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		'''
		Get an answer pair for judgement.
		'''
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		if not question.judging_period:
			return {'error':'Evaluation period is not active.'}, 403
		pair_generator = AnswerPairGenerator(course.id, question, current_user.id)

		try:
			answerpairing = pair_generator.get_pair()

			on_answer_pair_get.send(
				current_app._get_current_object(),
				event_name=on_answer_pair_get.name,
				user=current_user,
				course_id=course_id,
				data={'question_id': question_id, 'answer_pair': marshal(answerpairing, dataformat.getAnswerPairings(include_answers=True))})
			return marshal(answerpairing, dataformat.getAnswerPairings(include_answers=True))
		except InsufficientAnswersException:
			return {"error":"Not enough answers are available for an evaluation."}, 400
		except UserHasJudgedAllAnswers:
			return {"error":"You have judged all the currently available answers."}, 400
		except AnswerMissingScoreCalculation:
			return {"error":"An answer is missing a calculated score."}, 400
		except MissingScoreFromAnswer:
			return {"error":"A score is missing from an answer."}, 400
		except UnknownAnswerPairError:
			return {"error":"Generating scored pairs failed, this really shouldn't happen."}, 500
		return {"error":"Answer pair generation failed for an unknown reason."}, 500
api.add_resource(JudgementPairAPI, '/pair')

# /users/:userId/count
class UserJudgementCount(Resource):
	@login_required
	def get(self, course_id, question_id, user_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		count = judgement_count(question, user_id)

		on_judgement_question_count.send(
			current_app._get_current_object(),
			event_name=on_judgement_question_count.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'user_id': user_id, 'count': count}
		)

		return {"count":count}
api.add_resource(UserJudgementCount, '/users/<int:user_id>/count')

# /count
class UserAllJudgementCount(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		questions = PostsForQuestions.query.join(Posts).filter_by(courses_id=course.id).all()
		judgements = {ques.id:judgement_count(ques, current_user.id) for ques in questions}

		on_judgement_course_count.send(
			current_app._get_current_object(),
			event_name=on_judgement_course_count.name,
			user=current_user,
			course_id=course_id,
			data={'user_id': current_user.id, 'counts': judgements}
		)

		return {'judgements': judgements}
apiAll.add_resource(UserAllJudgementCount, '/count')

# /availpair
# returns True if there are enough eligible answers to generate at least one pair to evaluate
# for each question in the course
class AvailPairAll(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		questions = PostsForQuestions.query.join(Posts).filter_by(courses_id=course.id).all()

		# ineligible authors - eg. instructors, TAs, dropped student, current user
		student = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first_or_404()
		ineligible_users = CoursesAndUsers.query.filter_by(courses_id=course_id) \
			.filter(CoursesAndUsers.usertypesforcourse_id!=student.id) \
			.values(CoursesAndUsers.users_id)
		ineligible_userIds_base = [u[0] for u in ineligible_users]
		ineligible_userIds_base.append(current_user.id)

		availPairs = {}
		for ques in questions:
			# ineligible authors (potentially) - eg. authors for answers that the user has seen
			judged = Judgements.query.filter_by(users_id=current_user.id).join(AnswerPairings)\
				.filter_by(questions_id=ques.id).all()
			judged_authors1 = [j.answerpairing.answer1.post.users_id for j in judged]
			judged_authors2 = [j.answerpairing.answer2.post.users_id for j in judged]
			ineligible_userIds = ineligible_userIds_base + judged_authors1 + judged_authors2

			eligible_answers = PostsForAnswers.query.filter_by(questions_id=ques.id)\
				.join(Posts).filter(Posts.users_id.notin_(ineligible_userIds)).count()
			availPairs[ques.id] = eligible_answers / 2 >= 1 # min 1 pair required

		return {'availPairsLogic': availPairs}
apiAll.add_resource(AvailPairAll, '/availpair')

# /users/:userId/availpair
# returns True if there are enough eligible answers to generate at least one pair to evaluate
class AvailPair(Resource):
	@login_required
	def get(self, course_id, question_id, user_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)

		question = PostsForQuestions.query.get_or_404(question_id)
		# ineligible authors - eg. instructors, TAs, dropped student, current user
		student = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first_or_404()
		ineligible_users = CoursesAndUsers.query.filter_by(courses_id=course_id) \
			.filter(CoursesAndUsers.usertypesforcourse_id!=student.id) \
			.values(CoursesAndUsers.users_id)
		ineligible_userIds_base = [u[0] for u in ineligible_users]
		ineligible_userIds_base.append(user_id)

		# ineligible authors (potentially) - eg. authors for answers that the user has seen
		judged = Judgements.query.filter_by(users_id=current_user.id).join(AnswerPairings)\
			.filter_by(questions_id=question.id).all()
		judged_authors1 = [j.answerpairing.answer1.post.users_id for j in judged]
		judged_authors2 = [j.answerpairing.answer2.post.users_id for j in judged]
		ineligible_userIds = ineligible_userIds_base + judged_authors1 + judged_authors2

		eligible_answers = PostsForAnswers.query.filter_by(questions_id=question.id)\
			.join(Posts).filter(Posts.users_id.notin_(ineligible_userIds)).count()
		availPairs = eligible_answers / 2 >= 1 # min 1 pair required

		return {'availPairsLogic': availPairs}
api.add_resource(AvailPair, '/users/<int:user_id>/availpair')

def judgement_count(question, user_id):
	judgement_count_by_user = Judgements.query.filter_by(users_id=user_id).join(AnswerPairings) \
		.filter_by(questions_id=question.id).count()

	return judgement_count_by_user / question.criteria_count if question.criteria_count else 0


class InsufficientAnswersException(Exception):
	pass
class UserHasJudgedAllAnswers(Exception):
	pass
class MissingScoreFromAnswer(Exception):
	pass
class AnswerMissingScoreCalculation(Exception):
	pass
class UnknownAnswerPairError(Exception):
	pass


class AnswerPairGenerator:
	def __init__(self, course_id, question, user_id):
		self.course_id = course_id
		self.question_id = question.id
		self.user_id = user_id
		self.judged_answer_partners = self._generate_judged_answer_partners()
		self.answers = self._get_eligible_answers()
		self.rounds = self._get_existing_rounds()
		self.seed = user_id * (judgement_count(question, user_id) + 1)

	def get_pair(self):
		# Restrictions:
		# - Non-student answers and your own answer isn't eligible for judgment.
		# - There must be sufficient answers to form at least 1 pair
		# - There must still be at least 1 answer the user hasn't judged
		# - Cannot return a pair that the user has already seen before

		# - minimum number of answers is 2 --> 0 or 1 is not enough
		if len(self.answers) < 2:
			raise InsufficientAnswersException
		if self._has_user_judged_all_answers():
			raise UserHasJudgedAllAnswers
		self.answer_in_rounds = {r: [] for r in self.rounds}
		for answer in self.answers:
			self.answer_in_rounds[answer.round].append(answer)
		# if there are any answers that hasn't been scored, we need to judge those first
		pair = None
		criteriaId = None
		# if the lowest round is 0, that means there are unscored answers
		if self.rounds[0] == 0:
			#pair = self._get_unscored_pair(unscored_answers)
			pair = self._get_unscored_pair()
		if not pair:
			# match by closest score, when we have many criteria, match score on only one criterion
			question_criteria = CriteriaAndPostsForQuestions.query.\
				filter_by(questions_id=self.question_id, active=True).all()
			random.seed(self.seed)
			criteria = random.choice(question_criteria)
			pair = self._get_scored_pair(criteria)
			criteriaId = criteria.id
		return self._create_or_get_existing_pairing(pair, criteriaId)

	def _create_or_get_existing_pairing(self, pair_array, criteriaId):
		'''
		If there is an exisiting AnswerPairing already in the database, we should return that
		instead of making a new entry. If there's not existing one, then create one.
		:param pair_array: An array of 2 answers
		:return: the AnswerPairing entry in the database
		'''
		answer1 = pair_array[0]
		answer2 = pair_array[1]
		answerpairing = AnswerPairings.query.filter(
			or_(
				and_(AnswerPairings.answer1 == answer1, AnswerPairings.answer2 == answer2),
				and_(AnswerPairings.answer1 == answer2, AnswerPairings.answer2 == answer1)
			),
			AnswerPairings.criteriaandquestions_id == criteriaId
			).first()
		if not answerpairing:
			answerpairing = AnswerPairings(questions_id=self.question_id)
			answerpairing.answer1 = answer1
			answerpairing.answer2 = answer2
			answerpairing.criteriaandquestions_id = criteriaId
			db.session.add(answerpairing)
			db.session.commit()
		return answerpairing

	def _get_scored_pair(self, question_criterion):
		'''
		Create an answer pair by matching them up by score.
		- Sort answers by scores
		- Make pairs with neighbours
		- Calculate difference between pairs, sort into lowest first
		- Return the first pair that the user hasn't judged already, starting from the lowest
			difference one.
		:param question_criterion: The question criteria that we're checking the score on
		:return: An array of 2 answers
		'''
		round_count = len(self.rounds)
		valid_pair = None
		for key, r in enumerate(self.rounds):
			answers = self.answer_in_rounds[r]

			# try to pair up answers within the lowest round group if more than one answer exist
			if len(answers) > 1:
				sorted_answers = self._sort_answers_and_get_scores(answers, question_criterion.id)
				pairs = self._pair_with_neighbours(sorted_answers)
				valid_pair = self._get_valid_pair(pairs)
				if valid_pair:
					return valid_pair

			# if a valid pair is not found within the 'r' round and a next round exists
			if not valid_pair and (key+1) < round_count:
				# for round 'r'
				ans_sorted = self._sort_answers_and_get_scores(answers, question_criterion.id)

				for index, s in enumerate(self.rounds[key+1:]):
					answers = self.answer_in_rounds[s]
					sorted_answers = self._sort_answers_and_get_scores(answers, question_criterion.id)

					#pairs = [(ans, a) for a in sorted_answers]
					pairs = []
					for ans in ans_sorted:
						for a in sorted_answers:
							pairs.append((ans, a))

					valid_pair = self._get_valid_pair(pairs)
					if valid_pair:
						return valid_pair

		raise UnknownAnswerPairError

	def _get_unscored_pair(self):
		'''
		Unscored pairs can be matched up randomly.
		:return: A pair of answers [answer1, answer2]
		'''
		answers = self.answer_in_rounds[0]
		# if there are not enough unscored answers to form a pair, merge with next lowest score
		if len(answers) < 2:
			# assumng only one answer in the lowest group
			answer = answers[0]
			answers = self.answer_in_rounds[self.rounds[1]]
			random.seed(self.seed)
			random.shuffle(answers)
			for ans in answers:
				if not self._has_user_already_judged_pair([answer, ans]):
					return [answer, ans]
			return None
		random.seed(self.seed)
		random.shuffle(answers)
		pairs = self._pair_with_neighbours(answers)
		for pair in pairs:
			if not self._has_user_already_judged_pair(pair):
				return pair
		return None

	def _sort_answers_and_get_scores(self, answers, quesCriterionId):
		'''
		:return: sorted list of answers by score (for quesCriterionId)
		'''
		answer_scores = {}
		for answer in answers:
			score = None
			for score_iter in answer.scores:
				if score_iter.criteriaandquestions_id == quesCriterionId:
					score = score_iter
			if score == None:
				raise MissingScoreFromAnswer
			answer_scores[answer] = score.score
		sorted_answers = sorted(answer_scores.items(), key=operator.itemgetter(1))

		return sorted_answers

	def _get_valid_pair(self, pairs):
		'''
		find a valid pair with lowest score differ
		:param pairs:
		:return: valid pair OR None if one is not found
		'''
		valid = None
		pair_score_differences = {}
		# group together pairs that have the same score differences
		for pair in pairs:
			answer1 = pair[0][0]
			answer1_score = pair[0][1]
			answer2 = pair[1][0]
			answer2_score = pair[1][1]
			difference = abs(answer1_score - answer2_score)
			pair_score_differences.setdefault(difference, []).append([answer1, answer2])
		# check the pairs with the smallest differences first
		for score_difference in sorted(pair_score_differences):
			pairs = pair_score_differences[score_difference]
			random.seed(self.seed)
			random.shuffle(pairs)
			for pair in pairs:
				if not self._has_user_already_judged_pair(pair):
					valid = pair
					break
			if valid:	# if a valid pair
				break

		return valid

	def _has_user_already_judged_pair(self, pair):
		'''
		Check if the user has already judged this pair of answers
		:param pair: an array of 2 answers
		:return: True if the user has already judged the pair, False otherwise
		'''
		answer1 = pair[0]
		answer2 = pair[1]
		if answer1.id in self.judged_answer_partners:
			return answer2.id in self.judged_answer_partners[answer1.id]
		return False

	def _pair_with_neighbours(self, answers):
		'''
		For each answer, pair it up with the next answer in the list. Return a list of such pairs.
		:param answers:
		:return:
		'''
		return [[answer, answers[i+1]] for i,answer in enumerate(answers) if i+1 < len(answers)]

	def _has_user_judged_all_answers(self):
		'''
		Returns True if the user has already judged all answers, False otherwise.
		:param answers:
		:return:
		'''
		judged_answer_ids = set(self.judged_answer_partners.keys())
		# since we plan to allow soft delete of answers, there might be judgements in here on
		# 'deleted' answers, hence the set subtract instead of the simpler size comparison
		all_answer_ids = set([answer.id for answer in self.answers])
		# remove all judged answers ids from the list of known answers
		all_answer_ids -= judged_answer_ids
		if not all_answer_ids:
			return True
		return False

	def _generate_judged_answer_partners(self):
		'''
		Maps every answer id that has been judged to a set of answer ids that they've paired up with.
		Used to quickly check if an answer pair has already been seen by a user.
		:return:
		'''
		answer_partners = {}
		user_judgements = Judgements.query.join(AnswerPairings).filter(
			Judgements.users_id == self.user_id,
			AnswerPairings.questions_id == self.question_id).all()
		for user_judgement in user_judgements:
			answer1 = user_judgement.answerpairing.answer1
			answer2 = user_judgement.answerpairing.answer2
			answer1_partners = answer_partners.setdefault(answer1.id, set())
			answer1_partners.add(answer2.id)
			answer2_partners = answer_partners.setdefault(answer2.id, set())
			answer2_partners.add(answer1.id)
		return answer_partners

	def _get_eligible_answers(self):
		'''
		Some answers cannot be used in judgement. E.g.: Instructor/TA answers and the logged in user's
		own answer. This method retrieves only answers that can be used in judgement.
		'''
		# Exclude non-student users
		student_type = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first()
		excluded_user_ids = CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==self.course_id,
														 CoursesAndUsers.usertypeforcourse!=student_type).values(CoursesAndUsers.users_id)
		excluded_user_ids = [excluded_user_id[0] for excluded_user_id in excluded_user_ids]
		# Exclude currently logged in user
		excluded_user_ids.append(self.user_id)
		# Get only answers that are made by students
		answers = PostsForAnswers.query.join(Posts).filter(
			PostsForAnswers.questions_id==self.question_id,
			Posts.users_id.notin_(excluded_user_ids)).all()
		return answers

	def _get_existing_rounds(self):
		'''
		Creating a list of sorted rounds that existing answers are at for cases where
		we have to merge multiple levels
		'''
		rounds = [a.round for a in self.answers]
		rounds = set(rounds)
		rounds = list(rounds)
		rounds.sort()
		return rounds

