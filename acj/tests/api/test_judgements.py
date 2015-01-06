import json
import copy
import operator

from data.fixtures.test_data import JudgmentsTestData

from acj.models import PostsForAnswers, Posts
from acj.tests.test_acj import ACJTestCase


__author__ = 'john'

class JudgementAPITests(ACJTestCase):
	def setUp(self):
		super(JudgementAPITests, self).setUp()
		self.data = JudgmentsTestData()
		self.course= self.data.get_course()
		self.question = self.data.get_questions()[0]
		self.base_url = self._build_url(self.course.id, self.question.id)
		self.answer_pair_url = self.base_url + '/pair'

	def _build_url(self, course_id, question_id, tail=""):
		url = '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/judgements' +\
			tail
		return url

	def _build_judgement_submit(self, answerpair_id, winner_id):
		submit = {
			'answerpair_id': answerpair_id,
			'judgements': [
				{
				'question_criterion_id': self.question.criteria[0].id,
				'answer_id_winner': winner_id
				}
			]
		}
		return submit

	def test_get_answer_pair_access_control(self):
		# test login required
		rv = self.client.get(self.answer_pair_url)
		self.assert401(rv)
		# test deny access to unenroled users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert403(rv)
		self.logout()
		# enroled user from this point on
		self.login(self.data.get_authorized_student().username)
		# test non-existent course
		rv = self.client.get(self._build_url(9993929, self.question.id, '/pair'))
		self.assert404(rv)
		# test non-existent question
		rv = self.client.get(self._build_url(self.course.id, 23902390, '/pair'))
		self.assert404(rv)
		# no judgements has been entered yet, question is not in judging period
		rv = self.client.get(self._build_url(
			self.course.id, self.data.get_question_in_answer_period().id, '/pair'))
		self.assert403(rv)

	def test_get_answer_pair_basic(self):
		self.login(self.data.get_authorized_student().username)
		# no judgements has been entered yet
		rv = self.client.get(self.answer_pair_url)
		self.assert200(rv)
		actual_answer_pair = rv.json
		actual_answer1 = actual_answer_pair['answer1']
		actual_answer2 = actual_answer_pair['answer2']
		expected_answer_ids = [answer.id for answer in self.data.get_student_answers()]
		# make sure that we actually got answers for the question we're targetting
		self.assertIn(actual_answer1['id'], expected_answer_ids)
		self.assertIn(actual_answer2['id'], expected_answer_ids)

	def test_get_answer_pair_answer_exclusions_for_answers_with_no_scores(self):
		'''
		The user doing judgements should not see their own answer in a judgement.
		Instructor and TA answers should not show up.
		Answers cannot be paired with itself.
		For answers that don't have a score yet, which means they're randomly matched up.
		'''
		self.login(self.data.get_authorized_student().username)
		excluded_student_answer = PostsForAnswers.query.join(Posts).filter(
			Posts.users_id == self.data.get_authorized_student().id, \
			PostsForAnswers.questions_id == self.question.id).first()
		self.assertTrue(excluded_student_answer, "Missing authorized student's answer.")
		excluded_instructor_answer = PostsForAnswers.query.join(Posts).filter(
			Posts.users_id == self.data.get_authorized_instructor().id, \
			PostsForAnswers.questions_id == self.question.id).first()
		self.assertTrue(excluded_instructor_answer, "Missing instructor answer")
		excluded_ta_answer = PostsForAnswers.query.join(Posts).filter(
			Posts.users_id == self.data.get_authorized_ta().id, \
			PostsForAnswers.questions_id == self.question.id).first()
		self.assertTrue(excluded_ta_answer, "Missing TA answer")
		# no judgements has been entered yet, this tests the randomized pairing when no answers has
		# scores, since it's randomized though, we'll have to run it lots of times to be sure
		for i in range(50):
			rv = self.client.get(self.answer_pair_url)
			self.assert200(rv)
			actual_answer_pair = rv.json
			actual_answer1 = actual_answer_pair['answer1']
			actual_answer2 = actual_answer_pair['answer2']
			# exclude student's own answer
			self.assertNotEqual(actual_answer1['id'], excluded_student_answer.id)
			self.assertNotEqual(actual_answer2['id'], excluded_student_answer.id)
			# exclude instructor answer
			self.assertNotEqual(actual_answer1['id'], excluded_instructor_answer.id)
			self.assertNotEqual(actual_answer2['id'], excluded_instructor_answer.id)
			# exclude ta answer
			self.assertNotEqual(actual_answer1['id'], excluded_ta_answer.id)
			self.assertNotEqual(actual_answer2['id'], excluded_ta_answer.id)
		self.logout()
		# need a user with no answers submitted, otherwise pairs with the same answers
		# won't be generated since we have too few answers
		self.login(self.data.get_authorized_student_with_no_answers().username)
		for i in range(50):
			rv = self.client.get(self.answer_pair_url)
			self.assert200(rv)
			# answer cannot be paired with itself
			self.assertNotEqual(rv.json['answer1']['id'], rv.json['answer2']['id'])

	def test_submit_judgement_access_control(self):
		# establish expected data by first getting an answer pair
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert200(rv)
		expected_answer_pair = rv.json
		judgement_submit = self._build_judgement_submit(rv.json['id'], rv.json['answer1']['id'])
		self.logout()
		# test login required
		rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
							  content_type='application/json')
		self.assert401(rv)
		# test deny access to unenroled users
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test deny access to non-students
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		# authorized user from this point
		self.login(self.data.get_authorized_student().username)
		# test non-existent course
		rv = self.client.post(self._build_url(9999999, self.question.id),
			data=json.dumps(judgement_submit), content_type='application/json')
		self.assert404(rv)
		# test non-existent question
		rv = self.client.post(self._build_url(self.course.id, 9999999),
							  data=json.dumps(judgement_submit), content_type='application/json')
		self.assert404(rv)
		# test reject missing criteria
		faulty_judgements = copy.deepcopy(judgement_submit)
		faulty_judgements['judgements'] = []
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test reject missing course criteria id
		faulty_judgements = copy.deepcopy(judgement_submit)
		del faulty_judgements['judgements'][0]['question_criterion_id']
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test reject missing winner
		faulty_judgements = copy.deepcopy(judgement_submit)
		del faulty_judgements['judgements'][0]['answer_id_winner']
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid criteria id
		faulty_judgements = copy.deepcopy(judgement_submit)
		faulty_judgements['judgements'][0]['question_criterion_id'] = 3930230
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid winner id
		faulty_judgements = copy.deepcopy(judgement_submit)
		faulty_judgements['judgements'][0]['answer_id_winner'] = 2382301
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid answer pair
		faulty_judgements = copy.deepcopy(judgement_submit)
		faulty_judgements['answerpair_id'] = 2382301
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert404(rv)

	def test_submit_judgement_basic(self):
		self.login(self.data.get_authorized_student().username)
		# calculate number of judgements to do before user has judged all the pairs it can
		num_eligible_answers = -1 # need to minus one to exclude the logged in user's own answer
		for answer in self.data.get_student_answers():
			if answer.question.id == self.question.id:
				num_eligible_answers += 1
		# n - 1 possible pairs before all answers have been judged
		num_possible_judgements = num_eligible_answers - 1
		winner_ids = []
		for i in range(num_possible_judgements):
			# establish expected data by first getting an answer pair
			rv = self.client.get(self.answer_pair_url)
			self.assert200(rv)
			expected_answer_pair = rv.json
			judgement_submit = self._build_judgement_submit(rv.json['id'], rv.json['answer1']['id'])
			winner_ids.append(rv.json['answer1']['id'])
			# test normal post
			rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
								  content_type='application/json')
			self.assert200(rv)
			actual_judgements = rv.json['objects']
			self._validate_judgement_submit(judgement_submit, actual_judgements, expected_answer_pair)
			# Resubmit of same judgement should fail
			rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
								  content_type='application/json')
			self.assert400(rv)
		# all answers has been judged by the user, errors out when trying to get another pair
		rv = self.client.get(self.answer_pair_url)
		self.assert400(rv)

	def _validate_judgement_submit(self, judgement_submit, actual_judgements, expected_answer_pair):
		self.assertEqual(len(actual_judgements), len(judgement_submit['judgements']),
						 "The number of judgements saved does not match the number sent")
		for actual_judgement in actual_judgements:
			self.assertEqual(expected_answer_pair['answer1']['id'],
							 actual_judgement['answerpairing']['answers_id1'],
							 "Expected and actual judgement answer1 id did not match")
			self.assertEqual(expected_answer_pair['answer2']['id'],
							 actual_judgement['answerpairing']['answers_id2'],
							 "Expected and actual judgement answer2 id did not match")
			found_judgement = False
			for expected_judgement in judgement_submit['judgements']:
				if expected_judgement['question_criterion_id'] != \
						actual_judgement['question_criterion']['id']:
					continue
				self.assertEqual(expected_judgement['answer_id_winner'],
								 actual_judgement['answers_id_winner'],
								 "Expected and actual winner answer id did not match.")
				found_judgement = True
			self.assertTrue(found_judgement, "Actual judgement received contains a judgement that "
											 "was not sent.")

	def test_get_answer_pair_answer_exclusion_with_scored_answers(self):
		'''
		The user doing judgements should not see their own answer in a judgement.
		Instructor and TA answers should not show up.
		Answers cannot be paired with itself.
		Scored answer pairing means answers should be matched up to similar scores.
		'''
		# Make sure all answers are judged first
		self._submit_all_possible_judgements_for_user(
			self.data.get_authorized_student().username)
		self._submit_all_possible_judgements_for_user(
			self.data.get_secondary_authorized_student().username)

		self.login(self.data.get_authorized_student_with_no_answers().username)
		excluded_instructor_answer = PostsForAnswers.query.join(Posts).filter(
			Posts.users_id == self.data.get_authorized_instructor().id, \
			PostsForAnswers.questions_id == self.question.id).first()
		self.assertTrue(excluded_instructor_answer, "Missing instructor answer")
		excluded_ta_answer = PostsForAnswers.query.join(Posts).filter(
			Posts.users_id == self.data.get_authorized_ta().id, \
			PostsForAnswers.questions_id == self.question.id).first()
		self.assertTrue(excluded_ta_answer, "Missing TA answer")
		# no judgements has been entered yet, this tests the randomized pairing when no answers has
		# scores, since it's randomized though, we'll have to run it lots of times to be sure
		for i in range(50):
			rv = self.client.get(self.answer_pair_url)
			self.assert200(rv)
			actual_answer_pair = rv.json
			actual_answer1 = actual_answer_pair['answer1']
			actual_answer2 = actual_answer_pair['answer2']
			# exclude instructor answer
			self.assertNotEqual(actual_answer1['id'], excluded_instructor_answer.id)
			self.assertNotEqual(actual_answer2['id'], excluded_instructor_answer.id)
			# exclude ta answer
			self.assertNotEqual(actual_answer1['id'], excluded_ta_answer.id)
			self.assertNotEqual(actual_answer2['id'], excluded_ta_answer.id)
			# answer cannot be paired with itself
			self.assertNotEqual(actual_answer1['id'], actual_answer2['id'])

	def _submit_all_possible_judgements_for_user(self, username):
		self.login(username)
		# calculate number of judgements to do before user has judged all the pairs it can
		num_eligible_answers = -1 # need to minus one to exclude the logged in user's own answer
		for answer in self.data.get_student_answers():
			if answer.question.id == self.question.id:
				num_eligible_answers += 1
		# n - 1 possible pairs before all answers have been judged
		num_possible_judgements = num_eligible_answers - 1
		winner_ids = []
		loser_ids = []
		for i in range(num_possible_judgements):
			# establish expected data by first getting an answer pair
			rv = self.client.get(self.answer_pair_url)
			self.assert200(rv)
			expected_answer_pair = rv.json
			min_id = min([rv.json['answer1']['id'], rv.json['answer2']['id']])
			max_id = max([rv.json['answer1']['id'], rv.json['answer2']['id']])
			judgement_submit = self._build_judgement_submit(rv.json['id'], min_id)
			winner_ids.append(min_id)
			loser_ids.append(max_id)
			# test normal post
			rv = self.client.post(self.base_url, data=json.dumps(judgement_submit),
								  content_type='application/json')
			self.assert200(rv)
		self.logout()

		return {'winners': winner_ids, 'losers': loser_ids}

	def test_score_calculation(self):
		'''
		This is just a rough check on whether score calculations are correct. Answers
		that has more wins should have the highest scores.
		'''
		# Make sure all answers are judged first
		winner_ids = self._submit_all_possible_judgements_for_user(
			self.data.get_authorized_student().username)['winners']
		winner_ids.extend(self._submit_all_possible_judgements_for_user(
			self.data.get_secondary_authorized_student().username)['winners'])

		# Count the number of wins each answer has had
		num_wins_by_id = {}
		for winner_id in winner_ids:
			num_wins = num_wins_by_id.setdefault(winner_id, 0)
			num_wins_by_id[winner_id] = num_wins + 1

		# Get the actual score calculated for each answer
		answers = self.data.get_student_answers()
		answer_scores = {}
		for answer in answers:
			if answer.question.id == self.question.id:
				answer_scores[answer.id] = answer.scores[0].score

		# Check that ranking by score and by wins match, this only works for low number of
		# judgements
		expected_ranking_by_wins = [answer_id for (answer_id, wins) in sorted(num_wins_by_id.items(),
			key=operator.itemgetter(1))]
		actual_ranking_by_scores = [answer_id for (answer_id, score) in sorted(answer_scores.items(),
			key=operator.itemgetter(1)) if score > 0]
		self.assertSequenceEqual(actual_ranking_by_scores, expected_ranking_by_wins)

	def test_comparison_count_matched_pairing(self):
		# Make sure all answers are judged first
		answer_ids = self._submit_all_possible_judgements_for_user(
			self.data.get_authorized_student().username)
		answer_ids2 = self._submit_all_possible_judgements_for_user(
			self.data.get_secondary_authorized_student().username)
		compared_ids = answer_ids['winners'] + answer_ids2['winners'] + \
			answer_ids['losers'] + answer_ids2['losers']

		# Just a simple test for now, make sure that answers with the smaller number of
		# comparisons are matched up with each other
		# Count number of comparisons done for each answer
		num_comp_by_id = {}
		for answer_id in compared_ids:
			num_comp = num_comp_by_id.setdefault(answer_id, 0)
			num_comp_by_id[answer_id] = num_comp + 1

		comp_groups = {}
		for answerId in num_comp_by_id:
			count = num_comp_by_id[answerId]
			comp_groups.setdefault(count, [])
			comp_groups[count].append(answerId)
		counts = sorted(comp_groups)
		# get the answerIds with the lowest count of comparisons
		possible_answer_ids = comp_groups[counts[0]]
		if len(possible_answer_ids) < 2:
			# if the lowest count group does not have enough to create a pair - add the next group
			possible_answer_ids += comp_groups[counts[1]]

		# Check that the 2 answers with 1 win gets returned
		self.login(self.data.get_authorized_student_with_no_answers().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert200(rv)
		self.assertIn(rv.json['answer1']['id'], possible_answer_ids)
		self.assertIn(rv.json['answer2']['id'], possible_answer_ids)

	def test_get_judgement_count(self):
		url = self._build_url(self.data.get_course().id, self.question.id)

		# test login required
		tail = '/users/' + str(self.data.get_authorized_student().id) + '/count'
		rv = self.client.get(url + tail)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_student().username)
		tail = '/users/' + str(self.data.get_unauthorized_student().id) + '/count'
		rv = self.client.get(url + tail)
		self.assert403(rv)

		self.login(self.data.get_authorized_instructor().username)
		tail = '/users/' + str(self.data.get_authorized_instructor().id) + '/count'
		# test invalid course id
		invalid_url = self._build_url(999, self.question.id)
		rv = self.client.get(invalid_url + tail)
		self.assert404(rv)

		# test invalid question id
		invalid_url = self._build_url(self.data.get_course().id, 999)
		rv = self.client.get(invalid_url + tail)
		self.assert404(rv)

		# test authorized instructor
		rv = self.client.get(url + tail)
		self.assert200(rv)
		self.assertEqual(rv.json['count'], 0)
		self.logout()

		# test authorized student
		winners = self._submit_all_possible_judgements_for_user(
			self.data.get_authorized_student().username)['winners']
		tail = '/users/' + str(self.data.get_authorized_student().id) + '/count'
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(url + tail)
		self.assert200(rv)
		self.assertEqual(rv.json['count'], len(winners))
		self.logout()

	def test_get_all_judgement_count(self):
		url = '/api/courses/' + str(self.data.get_course().id) + '/judgements/count'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_authorized_instructor().username)
		# test invalid course id
		rv = self.client.get('/api/courses/999/judgements/count')
		self.assert404(rv)

		questions = self.data.get_questions()
		# test authorized instructor
		rv = self.client.get(url)
		self.assert200(rv)
		count = rv.json['judgements']

		for ques in questions:
			quesId = str(ques.id)
			self.assertTrue(quesId in count)
			self.assertEqual(count[quesId], 0)

		self.logout()

		# test authorized student
		winners = self._submit_all_possible_judgements_for_user(
			self.data.get_authorized_student().username)['winners']
		judgement_count = len(winners)
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(url)
		self.assert200(rv)
		count = rv.json['judgements']

		for ques in questions:
			quesId = str(ques.id)
			self.assertTrue(quesId in count)
			jcount = judgement_count if ques.id == self.question.id else 0
			self.assertEqual(count[quesId], jcount)

		self.logout()

	def test_get_all_availPair_logic(self):
		url = '/api/courses/' + str(self.data.get_course().id) + '/judgements/availpair'

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_authorized_student().username)
		# test invalid course id
		invalid_url = '/api/courses/999/judgements/availpair'
		rv = self.client.get(invalid_url)
		self.assert404(rv)

		first_ques = self.data.get_questions()[0]
		last_ques = self.data.get_questions()[-1]
		expected = {ques.id: True for ques in self.data.get_questions()}
		expected[last_ques.id] = False
		# test authorized student - when haven't judged
		rv = self.client.get(url)
		self.assert200(rv)
		logic = rv.json['availPairsLogic']
		for ques in self.data.get_questions():
			self.assertEqual(logic[str(ques.id)], expected[ques.id])
		self.logout()

		self._submit_all_possible_judgements_for_user(self.data.get_authorized_student().username)
		self.login(self.data.get_authorized_student().username)
		# test authorized student - when have judged all
		rv = self.client.get(url)
		self.assert200(rv)
		logic = rv.json['availPairsLogic']
		expected[first_ques.id] = False
		for ques in self.data.get_questions():
			self.assertEqual(logic[str(ques.id)], expected[ques.id])
		self.logout()

	def test_get_availPair_logic(self):
		url = self._build_url(self.data.get_course().id, self.question.id)

		tail = '/users/' + str(self.data.get_unauthorized_student().id) + '/availpair'
		# test login required
		rv = self.client.get(url + tail)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_student().username)
		rv = self.client.get(url + tail)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		tail = '/users/' + str(self.data.get_authorized_student().id) + '/availpair'
		self.login(self.data.get_authorized_student().username)
		invalid_url = self._build_url(999, self.question.id)
		rv = self.client.get(invalid_url + tail)
		self.assert404(rv)

		# test invalid question id
		invalid_url = self._build_url(self.data.get_course().id, 999)
		rv = self.client.get(invalid_url + tail)
		self.assert404(rv)
		self.logout()

		self.login(self.data.get_authorized_student().username)
		# test authorized student - when haven't judged
		rv = self.client.get(url + tail)
		self.assert200(rv)
		self.assertTrue(rv.json['availPairsLogic'])
		self.logout()

		self._submit_all_possible_judgements_for_user(self.data.get_authorized_student().username)
		# test authorized student - when have judged all
		self.login(self.data.get_authorized_student().username)
		rv = self.client.get(url + tail)
		self.assert200(rv)
		self.assertFalse(rv.json['availPairsLogic'])
		self.logout()
