from __future__ import division
import operator
import random
import math

from bouncer.constants import READ, CREATE
from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import func, or_, and_

from . import dataformat
from .core import db
from .authorization import require
from .core import event
from .models import PostsForAnswers, Posts, Judgements, AnswerPairings, Courses, CriteriaAndCourses, \
	PostsForQuestions, Scores, CoursesAndUsers, UserTypesForCourse
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
			return {'error':'Judging Period is not in session.'}, 403
		require(READ, question)
		course_criteria = CriteriaAndCourses.query.filter_by(course=course).all()
		params = new_judgement_parser.parse_args()
		answer_pair = AnswerPairings.query.get(params['answerpair_id'])
		if not answer_pair:
			return {"error":"Invalid Answer Pair ID"}, 404
		# check if number of judgements matches number of criteria
		if len(course_criteria) != len(params['judgements']):
			return {"error":"Not all criteria were evaluated!"}, 400
		# check if each judgement has an courseCriteria Id and a winner id
		for judgement in params['judgements']:
			if not 'course_criterion_id' in judgement:
				return {"error": "Missing course_criterion_id in judgement."}, 400
			if not 'answer_id_winner' in judgement:
				return {"error": "Missing winner for one of criteria."}, 400
			# check that we're using criteria that were assigned to the course and that we didn't
			# get duplicate criteria in judgements
			known_criterion = False
			for course_criterion_entry in course_criteria[:]:
				if judgement['course_criterion_id'] == course_criterion_entry.id:
					known_criterion = True
					course_criteria.remove(course_criterion_entry)
			if not known_criterion:
				return {"error": "Unknown criterion submitted in judgement!"}, 400
			# check that the winner id matches one of the answer pairs
			winner_id = judgement['answer_id_winner']
			if winner_id != answer_pair.answer1.id and winner_id != answer_pair.answer2.id:
				return {"error": "Winner ID does not match the available pair of answers."}, 400
		# check if pair has already been judged by this user
		if Judgements.query.filter_by(users_id = current_user.id,
			answerpairings_id = answer_pair.id).first():
			return {"error": "You've already judged this pair of answers!"}, 400
		judgements = []
		criteria = []
		for judgement_params in params['judgements']:
			criteria.append(judgement_params['course_criterion_id'])
			# need this or hybrid property for courses_id won't work when it checks permissions
			course_criterion = CriteriaAndCourses.query.get(judgement_params['course_criterion_id'])
			judgement = Judgements(answerpairing=answer_pair, users_id=current_user.id,
				course_criterion=course_criterion,
				postsforanswers_id_winner=judgement_params['answer_id_winner'])
			db.session.add(judgement)
			require(CREATE, judgement)
			db.session.commit()
			judgements.append(judgement)

		# update answer scores
		current_app.logger.debug("Doing scoring")
		self._calculate_scores(course_id, question_id)

		on_judgement_create.send(
			current_app._get_current_object(),
			event_name=on_judgement_create.name,
			user=current_user,
			course_id=course_id,
			data=marshal(judgement, dataformat.getJudgements()))

		return {'objects': marshal(judgements, dataformat.getJudgements())}

	def _calculate_scores(self, course_id, question_id):
		# get all judgements for this question
		judgements = Judgements.query.join(AnswerPairings). \
			filter(AnswerPairings.postsforquestions_id == question_id).all()
		answers = set() # stores answers that've been judged
		course_criteria = CriteriaAndCourses.query.filter_by(courses_id=course_id).all()
		# 2D array, keep tracks of wins, e.g.: wins[A][B] is the number of times A won vs B
		wins = WinsTable(course_criteria)
		# keeps track of number of times judged for each answer
		rounds = {}
		for judgement in judgements:
			answer1 = judgement.answerpairing.answer1
			answer2 = judgement.answerpairing.answer2
			winner = judgement.answer_winner
			loser = answer1
			if winner.id == answer1.id:
				loser = answer2
			wins.add(winner, loser, judgement.course_criterion)
			# update number of times judged
			rounds[answer1.id] = rounds.get(answer1.id, 0) + 1
			rounds[answer2.id] = rounds.get(answer2.id, 0) + 1
			answers.add(answer1)
			answers.add(answer2)
		current_app.logger.debug("Wins table: " + str(wins))
		# create scores for each answer
		for answer in answers:
			for course_criterion in course_criteria:
				score = Scores.query.filter_by(answer=answer, course_criterion=course_criterion).first()
				if not score:
					score = Scores(answer=answer, course_criterion=course_criterion)
				score.rounds = rounds.get(answer.id, 0)
				score.score = wins.get_score(answer, course_criterion)
				score.wins = wins.get_total_wins(answer, course_criterion)
				db.session.add(score)
		db.session.commit()
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
			return {'error':'Judging Period is not in session.'}, 403
		pair_generator = AnswerPairGenerator(course_id, question_id)
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
			return {"error":"Insufficient answers available for judgement."}, 400
		except UserHasJudgedAllAnswers:
			return {"error":"You have judged all answers available!"}, 400
		except AnswerMissingScoreCalculation:
			return {"error":"An answer is missing a calculated score!"}, 400
		except MissingScoreFromAnswer:
			return {"error":"A score is missing from an answer!"}, 400
		except UnknownAnswerPairError:
			return {"error":"Generating scored pairs failed, this really shouldn't happen."}, 500
		return {"error":"Answer pair generation failed for an unknown reason."}, 500
api.add_resource(JudgementPairAPI, '/pair')

class UserJudgementCount(Resource):
	def get(self, course_id, question_id, user_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		count = judgement_count(course_id, question_id, user_id)

		return {"count":count}
api.add_resource(UserJudgementCount, '/count/users/<int:user_id>')

# /count
class UserAllJudgementCount(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		questions = PostsForQuestions.query.join(Posts).filter_by(courses_id=course.id).all()
		judgements = {}
		for ques in questions:
			judgements[ques.id] = judgement_count(course_id, ques.id, current_user.id)
		return {'judgements': judgements}
apiAll.add_resource(UserAllJudgementCount, '/count')

def judgement_count(course_id, question_id, user_id):
	# try to get first criteria a user has evaluated in this question
	judge = Judgements.query.join(AnswerPairings).filter(AnswerPairings.postsforquestions_id==question_id).first()
	if not judge:
		# if not judgements are found - grab the first criteria in the course
		criteriaandcourses = CriteriaAndCourses.query.filter_by(courses_id=course_id).first_or_404()
		criteriaandcourses_id = criteriaandcourses.id
	else:
		criteriaandcourses_id = judge.criteriaandcourses_id
	count = Judgements.query.filter_by(users_id=user_id, criteriaandcourses_id=criteriaandcourses_id).count()

	return count

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
class AnswerPairGenerator():
	def __init__(self, course_id, question_id):
		self.course_id = course_id
		self.question_id = question_id
		self.judged_answer_partners = self._generate_judged_answer_partners()
		self.answers = self._get_eligible_answers()

	def get_pair(self):
		# Restrictions:
		# - Non-student answers and your own answer isn't eligible for judgment.
		# - There must be sufficient answers to form at least 1 pair
		# - There must still be at least 1 answer the user hasn't judged
		# - Cannot return a pair that the user has already seen before
		if len(self.answers) < 3:
			raise InsufficientAnswersException
		if self._has_user_judged_all_answers():
			raise UserHasJudgedAllAnswers
		unscored_answers = [answer for answer in self.answers if not answer.scores]
		# if there are any answers that hasn't been scored, we need to judge those first
		pair = None
		if unscored_answers:
			pair = self._get_unscored_pair(unscored_answers)
		if not pair:
			# match by closest score, when we have many criteria, match score on only one criterion
			course_criteria = CriteriaAndCourses.query.filter_by(courses_id=self.course_id).all()
			pair = self._get_scored_pair(random.choice(course_criteria))
		return self._create_or_get_existing_pairing(pair)

	def _create_or_get_existing_pairing(self, pair_array):
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
			)).first()
		if not answerpairing:
			answerpairing = AnswerPairings(postsforquestions_id=self.question_id)
			answerpairing.answer1 = answer1
			answerpairing.answer2 = answer2
			db.session.add(answerpairing)
			db.session.commit()
		return answerpairing

	def _get_scored_pair(self, course_criterion):
		'''
		Create an answer pair by matching them up by score.
		- Sort answers by scores
		- Make pairs with neighbours
		- Calculate difference between pairs, sort into lowest first
		- Return the first pair that the user hasn't judged already, starting from the lowest
			difference one.
		:param course_criterion: The course criteria that we're checking the score on
		:return: An array of 2 answers
		'''
		answer_scores = {}
		for answer in self.answers:
			score = None
			for score_iter in answer.scores:
				if score_iter.criteriaandcourses_id == course_criterion.id:
					score = score_iter
			if score == None:
				raise MissingScoreFromAnswer
			answer_scores[answer] = score.score
		sorted_answers = sorted(answer_scores.items(), key=operator.itemgetter(1))
		pairs = self._pair_with_neighbours(sorted_answers)
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
			random.shuffle(pairs)
			for pair in pairs:
				if not self._has_user_already_judged_pair(pair):
					return pair
		raise UnknownAnswerPairError

	def _get_unscored_pair(self, unscored_answers):
		'''
		Unscored pairs can be matched up randomly.
		:return: A pair of answers [answer1, answer2]
		'''
		random.shuffle(unscored_answers)
		pairs = self._pair_with_neighbours(unscored_answers)
		if not pairs: # edge case where there's insufficient unscored answers to form a pair
			# need to prevent picking the same answer for partner
			answers = [answer for answer in self.answers if answer.id != unscored_answers[0].id]
			answer_ids = [answer.id for answer in answers]
			random_partner = random.choice(answers)
			return [unscored_answers[0], random_partner]
		for pair in pairs:
			if not self._has_user_already_judged_pair(pair):
				return pair
		return None

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
			Judgements.users_id == current_user.id,
			AnswerPairings.postsforquestions_id == self.question_id).all()
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
		excluded_user_ids.append(current_user.id)
		# Get only answers that are made by students
		answers = PostsForAnswers.query.join(Posts).filter(
			PostsForAnswers.postsforquestions_id==self.question_id,
			Posts.users_id.notin_(excluded_user_ids)).all()
		return answers

class WinsTable:
	def __init__(self, course_criteria):
		# 3D array, keep tracks of wins, wins[course_criteria][winner_id][opponent_id]
		self.wins = {}
		for course_criterion in course_criteria:
			self.wins[course_criterion.id] = {}

	def add(self, winner, loser, course_criterion):
		'''
		Update number of wins for the winner
		:param winner: Answer that won
		:param loser: Answer that lost
		:param course_criterion: Criterion that winner won on
		:return: nothing
		'''
		winner_wins_row = self.wins[course_criterion.id].get(winner.id, {})
		winner_wins_row[loser.id] = winner_wins_row.get(loser.id, 0) + 1
		self.wins[course_criterion.id][winner.id] = winner_wins_row

	def get_total_wins(self, winner, course_criterion):
		'''
		Get total number of wins in a criterion for an answer
		:param winner: The answer to get the number of wins for
		:param course_criterion: Criterion for the wins
		:return: Total number of wins that the winner has in the specified criterion
		'''
		winner_row = self.wins.get(course_criterion.id, {}).get(winner.id, {})
		return sum(winner_row.values())

	def get_score(self, answer, course_criterion):
		'''
		Calculate score for an answer
		:param answer:
		:param course_criterion:
		:return:
		'''
		current_app.logger.debug("Calculating score for answer id: " + str(answer.id))
		answer_opponents = self.wins[course_criterion.id].get(answer.id, {})
		current_app.logger.debug("\tThis answer's opponents:" + str(answer_opponents))
		# see ACJ paper equation 3 for what we're doing here
		expected_score = 0
		for opponent_id, answer_wins in answer_opponents.items():
			if opponent_id == answer.id: # skip comparing to self
				continue
			opponent_wins = self.wins[course_criterion.id].get(opponent_id, {}).get(answer.id, 0)
			current_app.logger.debug("\tVa = " + str(answer_wins))
			current_app.logger.debug("\tVi = " + str(opponent_wins))
			prob_answer_wins = (math.exp(answer_wins - opponent_wins)) / \
							   (1 + math.exp(answer_wins - opponent_wins))
			expected_score += prob_answer_wins
			current_app.logger.debug("\tE(S) = " + str(expected_score))
		return expected_score

