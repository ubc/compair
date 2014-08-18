from __future__ import division
import random
from bouncer.constants import READ, CREATE

from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
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
new_judgement_parser.add_argument('answer1_id', type=int, required=True, help="Missing answer1 id.")
new_judgement_parser.add_argument('answer2_id', type=int, required=True, help="Missing answer2 id.")
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
			if winner_id != params['answer1_id'] and winner_id != params['answer2_id']:
				return {"error": "Winner ID does not match the available pair of answers."}, 400
		# check that the answer ids are valid
		answer_pair = []
		answer_pair.append(PostsForAnswers.query.get_or_404(params['answer1_id']))
		answer_pair.append(PostsForAnswers.query.get_or_404(params['answer2_id']))
		# check if pair has already been judged by this user
		if is_already_judged_answer_pair(answer_pair, question_id):
			return {"error": "You've already judged this pair of answers!"}, 400
		# save judgement
		answerpairing = get_existing_answer_pair(answer_pair, question_id)
		if not answerpairing:
			answerpairing = AnswerPairings(answer1=answer_pair[0], answer2=answer_pair[1],
										   question=question)
			db.session.add(answerpairing)
		judgements = []
		criteria = []
		for judgement_params in params['judgements']:
			course_criterion = CriteriaAndCourses.query.get_or_404(
				judgement_params['course_criterion_id'])
			criteria.append(judgement_params['course_criterion_id'])
			judgement = Judgements(answerpairing=answerpairing, users_id=current_user.id,
				course_criterion=course_criterion,
				postsforanswers_id_winner=judgement_params['answer_id_winner'])
			db.session.add(judgement)
			require(CREATE, judgement)
			db.session.commit()
			judgements.append(judgement)
		answers = PostsForAnswers.query.filter(PostsForAnswers.postsforquestions_id==question.id).count()
		pairs = AnswerPairings.query.filter(AnswerPairings.postsforquestions_id==question.id).all()
		judged_answers = list(chain.from_iterable((i.postsforanswers_id1, i.postsforanswers_id2) for i in pairs))
		judged_answers = list(set(judged_answers))
		if answers == len(judged_answers):
			for criterion in criteria:
				rank_answers(question.id, judged_answers, criterion)
		return {'objects': marshal(judgements, dataformat.getJudgements())}
api.add_resource(JudgementRootAPI, '')

# /pair
class JudgementPairAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		'''
		Get an answer pair for judgement.
		'''
		course = Courses.query.get_or_404(course_id) # this is just to make sure course exists
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		if not question.judging_period:
			return {'error':'Judging Period is not in session.'}, 403
		# count number of times judged for each answer
		## get all answers for this question
		answers = PostsForAnswers.query.join(Posts).\
			filter(Posts.courses_id==course_id, PostsForAnswers.postsforquestions_id==question_id).all()
		answers_judge_count = {} # keeps track of number of times each answer has been judged
		for answer in answers:
			answers_judge_count[answer] = 0
		answers_already_judged_by_user = {} # track whether user has already judged this answer
		for answer in answers:
			answers_already_judged_by_user[answer] = False
		## get all judgements for this question
		judgements = Judgements.query.join(AnswerPairings).\
			filter(AnswerPairings.postsforquestions_id==question_id).all()
		## go through each judgement, check answer pair, add 1 to each answer
		for judgement in judgements:
			answer1 = judgement.answerpairing.answer1
			answer2 = judgement.answerpairing.answer2
			answers_judge_count[answer1] += 1
			answers_judge_count[answer2] += 1
			# record that the user has already judged these answers
			if judgement.users_id == current_user.id:
				answers_already_judged_by_user[answer1] = True
				answers_already_judged_by_user[answer2] = True
		## abort if all answers has already been judged by the user at least once
		all_answers_judged = True
		for answer, judged in answers_already_judged_by_user.items():
			if not judged:
				all_answers_judged = False
		if all_answers_judged:
			return {"error": "You've already judged all answers!"}, 400
		# group answers with same number of times judged together, sorted ascending
		judge_counts = {}
		for key, value in sorted(answers_judge_count.items(), key=lambda x: x[1]):
			judge_counts.setdefault(value, []).append(key)
		# starting from the pool of lowest number of times judged answers, form a pair, return pair
		answer_pair = []
		for count,answers in judge_counts.items():
			random.shuffle(answers) # we want to randomly pick answers
			while answers:
				answer_pair.append(answers.pop())
				if len(answer_pair) >= 2:
					if is_already_judged_answer_pair(answer_pair, question_id):
						answer_pair.pop() # it's a duplicate pair, remove the first answer and try again
					else:
						break # still need to stop outer loop
			# have sufficient answers to make a pair, can stop now
			if len(answer_pair) >= 2:
				break
		if len(answer_pair) < 2:
			return {"error":"Insufficient answers for judgement yet!"}, 400
		return {"answer1":
					marshal(answer_pair[0], dataformat.getPostsForAnswers(include_comments=False)),
				"answer2":
					marshal(answer_pair[1], dataformat.getPostsForAnswers(include_comments=False))}

def is_already_judged_answer_pair(answer_pair, question_id):
	answer1 = answer_pair[0]
	answer2 = answer_pair[1]
	# see if user has already judged this answer pair
	existing_answer_pair = get_existing_answer_pair(answer_pair, question_id)
	if existing_answer_pair:
		judgement = Judgements.query.filter_by(answerpairing=existing_answer_pair, \
			users_id=current_user.id).first()
		if judgement:
			return True
	else:
		return False

def get_existing_answer_pair(answer_pair, question_id):
	answer1 = answer_pair[0]
	answer2 = answer_pair[1]
	ret = AnswerPairings.query.filter_by(answer1=answer1, answer2=answer2, \
		postsforquestions_id=question_id).first()
	if ret:
		return ret
	ret = AnswerPairings.query.filter_by(answer1=answer2, answer2=answer1, \
		postsforquestions_id=question_id).first()
	if ret:
		return ret
	return False

def rank_answers(question_id, judged_answers, criterion):
	actual = []
	expected = []
	pairs = AnswerPairings.query.filter_by(postsforquestions_id=question_id).all()
	scores = Scores.query.filter_by(criteriaandcourses_id=criterion).filter(Scores.postsforanswers_id.in_(judged_answers)).all()
	formatted_scores = {} #store previously saved scores
	for score in scores:
		formatted_scores[score.postsforanswers_id] = score
	accessed_scores = {}	#store new scores from this round of ranking

	# accumulate scores from all the pairings
	for x in pairs:
		if (x.postsforanswers_id1 in formatted_scores):
			score1 = formatted_scores.get(x.postsforanswers_id1)
			score1.rounds = score1.wins = score1.score = 0
			del formatted_scores[x.postsforanswers_id1]
		elif (x.postsforanswers_id1 in accessed_scores):
			score1 = accessed_scores[x.postsforanswers_id1]
		else:
			score1 = Scores(criteriaandcourses_id=criterion, rounds=0, wins=0, score=0) 
			score1.postsforanswers_id = x.postsforanswers_id1
		accessed_scores[x.postsforanswers_id1] = score1 

		if (x.postsforanswers_id2 in formatted_scores):
			score2 = formatted_scores.get(x.postsforanswers_id2)
			score2.rounds = score2.wins = score2.score = 0
			del formatted_scores[x.postsforanswers_id2]
		elif (x.postsforanswers_id2 in accessed_scores):
			score2 = accessed_scores[x.postsforanswers_id2]
		else:
			score2 = Scores(criteriaandcourses_id=criterion, rounds=0, wins=0, score=0) 
			score2.postsforanswers_id = x.postsforanswers_id2 
		accessed_scores[x.postsforanswers_id2] = score2
	
		total = x.answer1_win + x.answer2_win
		score1.rounds = score1.rounds + total
		score2.rounds = score2.rounds + total

		ans1 = x.answer1_win / total
		score1.wins += x.answer1_win
		score1.score += ans1

		ans2 = x.answer2_win / total
		score2.wins += x.answer2_win
		score2.score += ans2

		accessed_scores[x.postsforanswers_id1] = score1
		accessed_scores[x.postsforanswers_id2] = score2

	for id in accessed_scores.keys():
		db.session.add(accessed_scores[id])
	db.session.commit()

api.add_resource(JudgementPairAPI, '/pair')
