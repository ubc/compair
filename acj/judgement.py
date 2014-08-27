from __future__ import division
import random
from bouncer.constants import READ, CREATE

from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
import math
from sqlalchemy import and_, func
from acj import dataformat, db
from acj.authorization import require
from acj.models import PostsForAnswers, Posts, Judgements, AnswerPairings, Courses, CriteriaAndCourses, \
	PostsForQuestions, Scores
from acj.util import new_restful_api
from itertools import chain

# First declare a Flask Blueprint for this module
judgements_api = Blueprint('judgements_api', __name__)
# Then pack the blueprint into a Flask-Restful API
api = new_restful_api(judgements_api)

new_judgement_parser = RequestParser()
new_judgement_parser.add_argument('answerpair_id', type=int, required=True,
								  help="Missing answer pair id.")
new_judgement_parser.add_argument('judgements', type=list, required=True, help="Missing judgements.")


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
		# update answer scores once we've passed round 1
		round = _get_judgement_round(question_id)
		current_app.logger.debug("Round: " + str(round))
		if round > 1:
			current_app.logger.debug("Doing scoring")
			_calculate_scores(course_id, question_id)
		return {'objects': marshal(judgements, dataformat.getJudgements())}
api.add_resource(JudgementRootAPI, '')

# /pair
class JudgementPairAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		'''
		Get an answer pair for judgement.
		'''
		# Make sure the course and question exists
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		if not question.judging_period:
			return {'error':'Judging Period is not in session.'}, 403
		answers = PostsForAnswers.query. \
			filter(PostsForAnswers.postsforquestions_id==question_id).all()
		if len(answers) < 2:
			return {"error":"Insufficient answers available for judgement."}, 400
		current_app.logger.debug("Checking judgement round for this question.")
		current_round_pairings = AnswerPairings.query.filter_by(
			postsforquestions_id=question_id, round=func.max(AnswerPairings.round).select()).all()
		round = _get_judgement_round(question_id)
		current_app.logger.debug("We're in round " + str(round))
		if round == 1 and not current_round_pairings:
			current_round_pairings = self._generate_random_pairings(question_id, answers)
		# check to see if we've used up all pairs
		current_app.logger.debug("Checking to see if all available pairs has been judged already.")
		## get already judged pairings (couldn't figure out how to write query to get unjudged pairs)
		judged_pairings = AnswerPairings.query.join(Judgements).filter(
			AnswerPairings.postsforquestions_id==question_id,
			AnswerPairings.round==round)
		## map this round's pairings by id
		unjudged_pairings = dict(map(lambda e: [e.id, e], current_round_pairings))
		current_app.logger.debug("All current round's pairings mapped by id")
		## remove judged pairings
		for pairing in judged_pairings:
			del unjudged_pairings[pairing.id]
		# no unjudged pairings left, so need to generate a new set
		if not unjudged_pairings:
			# in all rounds after 1, we have to pair answers up by how many times they've won
			current_app.logger.debug("No unjudged pairings left, need to generate new set.")
			unjudged_pairings = self._generate_score_matched_pairings(course_id, question_id,
																	 answers, round + 1)
		unjudged_pairings = unjudged_pairings.values()
		random.shuffle(unjudged_pairings) # randomly give the user an answer pair
		current_app.logger.debug("Making sure the user isn't getting a pair they've seen before.")
		# get all judgements made by this user
		user_judgements = Judgements.query.join(AnswerPairings).filter(
			Judgements.users_id == current_user.id,
			AnswerPairings.postsforquestions_id == question_id).all()
		# get all pairs judged by user
		selected_pair = None
		user_judged_pairs = [judgement.answerpairing for judgement in user_judgements]
		for unjudged_pairing in unjudged_pairings:
			used_pair = False
			for user_judged_pair in user_judged_pairs:
				if _same_answers_in_pair(unjudged_pairing, user_judged_pair):
					current_app.logger.debug("User has already judged this pair.")
					used_pair = True
					break
			if not used_pair:
				current_app.logger.debug("Found a pair that the user hasn't judged yet.")
				selected_pair = unjudged_pairing
				break
		if selected_pair == None:
			return {"error":"You've already judged all currently available answer pairs! There might be more available later."}, 400
		current_app.logger.debug("Return one of the unjudged pairings")
		return marshal(selected_pair, dataformat.getAnswerPairings(include_answers=True))

	def _generate_random_pairings(self, question_id, answers):
		'''
		Generate random answer pairings
		'''
		random_pairings = []
		# we're in round 1, where pairings are generated randomly
		current_app.logger.debug("No previously generated rounds, generating round 1.")
		# generate random pairings from available answers
		random.shuffle(answers)
		while answers:
			answerpairing = AnswerPairings(postsforquestions_id=question_id, round=1)
			if len(answers) > 1:
				answerpairing.answer1 = answers.pop()
				answerpairing.answer2 = answers.pop()
			else: # only 1 answer left, need to reuse a previously paired answer
				answerpairing.answer1 = answers.pop()
				random_pair = random.choice(random_pairings)
				odd_one_out_partner = random.choice([random_pair.answer1, random_pair.answer2])
				answerpairing.answer2 = odd_one_out_partner
			current_app.logger.debug(answerpairing)
			db.session.add(answerpairing)
			random_pairings.append(answerpairing)
		db.session.commit()
		return random_pairings

	def _generate_score_matched_pairings(self, course_id, question_id, answers, round):
		'''
		Generate answer pairings by matching answers with scores close to each other together
		'''
		score_matched_pairings = {}
		# randomize here
		random.shuffle(answers)
		# Multiple criteria means multiple scores, so we'd have to make different pairs according
		# to different criteria.
		# sort scores into the criteria they belong to, scores_by_criteria[criterion_id] = [scores]
		scores_by_criteria= {}
		for answer in answers:
			scores = answer.scores
			if not scores:
				current_app.logger.debug("No scores detected, try to calculate them.")
				_calculate_scores(course_id, question_id)
				scores = answer.scores
			for score in scores:
				criterion_id = score.criteriaandcourses_id
				scores_by_criterion = scores_by_criteria.get(criterion_id, [])
				scores_by_criterion.append(score)
				scores_by_criteria[criterion_id] = scores_by_criterion
		current_app.logger.debug("Scores By Criteria: " + str(scores_by_criteria))
		# generate answerpairs by matching scores for each criteria. This means that each criteria
		# will have their own set of answerpairs
		for criterion_id, scores_in_criterion in scores_by_criteria.items():
			# convert to a map of # wins to scores
			scores_by_wins = {}
			for score in scores_in_criterion:
				scores = scores_by_wins.get(score.wins, [])
				scores.append(score)
				scores_by_wins[score.wins] = scores
			# convert to a list of scores, sorted by # wins
			scores_sorted = []
			for wins in sorted(scores_by_wins):
				scores_sorted.extend(scores_by_wins[wins])
			current_app.logger.debug("Scores Sorted By Wins: " + str(scores_sorted))
			# make pairs
			while scores_sorted:
				answerpairing = AnswerPairings(postsforquestions_id=question_id, round=round)
				if len(scores_sorted) > 1:
					answerpairing.answer1 = scores_sorted.pop().answer
					answerpairing.answer2 = scores_sorted.pop().answer
				else: # only 1 answer left, need to reuse a previously paired answer
					answerpairing.answer1 = scores_sorted.pop().answer
					odd_one_out_partner = random.choice(answers)
					answerpairing.answer2 = odd_one_out_partner
				db.session.add(answerpairing)
				score_matched_pairings[answerpairing.id] = answerpairing
		db.session.commit()
		return score_matched_pairings

def _get_judgement_round(question_id):
	round = 1
	current_round_pairing = AnswerPairings.query.filter_by(
		postsforquestions_id=question_id, round=func.max(AnswerPairings.round).select()).first()
	if current_round_pairing:
		round = current_round_pairing.round
	return round

def _same_answers_in_pair(answer_pair1, answer_pair2):
	'''
	Check if two answer pairs have the same answers.
	:param answer_pair1:
	:param answer_pair2:
	:return:
	'''
	if answer_pair1.postsforanswers_id1 == answer_pair2.postsforanswers_id1 and \
		answer_pair1.postsforanswers_id2 == answer_pair2.postsforanswers_id2:
		return True
	if answer_pair1.postsforanswers_id1 == answer_pair2.postsforanswers_id2 and \
		answer_pair1.postsforanswers_id2 == answer_pair2.postsforanswers_id1:
		return True
	return False

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

def _calculate_scores(course_id, question_id):
	# get all judgements for this question
	judgements = Judgements.query.join(AnswerPairings).\
		filter(AnswerPairings.postsforquestions_id == question_id).all()
	# get all answers for this question
	answers = PostsForAnswers.query.filter_by(postsforquestions_id=question_id).all()
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
	current_app.logger.debug("Wins table: " + str(wins))
	# create scores for each answer
	for answer in answers:
		for course_criterion in course_criteria:
			score = Scores.query.filter_by(answer=answer, course_criterion=course_criterion).first()
			if not score:
				score = Scores(answer=answer, course_criterion=course_criterion)
			score.rounds = rounds[answer.id]
			score.score = wins.get_score(answer, course_criterion)
			score.wins = wins.get_total_wins(answer, course_criterion)
			db.session.add(score)
	db.session.commit()

api.add_resource(JudgementPairAPI, '/pair')
