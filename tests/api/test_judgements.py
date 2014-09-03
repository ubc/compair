import json
import copy
from acj import db
from acj.models import UserTypesForSystem, UserTypesForCourse
from tests.test_acj import ACJTestCase
from tests.test_data import SimpleTestData

__author__ = 'john'

class JudgementAPITests(ACJTestCase):
	def setUp(self):
		super(JudgementAPITests, self).setUp()
		self.data = SimpleTestData()
		self.course= self.data.get_course()
		self.question = self.data.get_questions()[0]
		self.base_url = self._build_url(self.course.id, self.question.id)
		self.answer_pair_url = self.base_url + '/pair'
		# delete answers made by enroled student, so we'll only get other student's answers
		for answer in self.data.get_answers():
			db.session.delete(answer)
			db.session.commit()
		# need to add additional student answers, since students can't judge their own answers
		extra_student1 = self.data.create_user(UserTypesForSystem.TYPE_NORMAL)
		extra_student2 = self.data.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.data.enrol_user(extra_student1, self.course, UserTypesForCourse.TYPE_STUDENT)
		self.data.enrol_user(extra_student2, self.course, UserTypesForCourse.TYPE_STUDENT)
		self.expected_answer1 = self.data.create_answer(self.question, extra_student1)
		self.expected_answer2 = self.data.create_answer(self.question, extra_student2)

	def _build_url(self, course_id, question_id, tail=""):
		url = '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/judgements' +\
			tail
		return url

	def test_get_answer_pair(self):
		return
		# test login required
		rv = self.client.get(self.answer_pair_url)
		self.assert401(rv)
		# test deny access to unenroled users
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert403(rv)
		self.logout()
		# enroled user from this point on
		self.login(self.data.get_enroled_student().username)
		# test non-existent course
		rv = self.client.get(self._build_url(9993929, self.question.id, '/pair'))
		self.assert404(rv)
		# test non-existent question
		rv = self.client.get(self._build_url(self.course.id, 23902390, '/pair'))
		self.assert404(rv)
		# no judgements has been entered yet
		rv = self.client.get(self.answer_pair_url)
		self.assert200(rv)
		# since the actual answer pair should come to us in random order, we need to impose
		# a reproducible order to it in order to validate it
		actual_answer_pair = rv.json
		actual_answer1 = actual_answer_pair['answer1']
		actual_answer2 = actual_answer_pair['answer2']
		if actual_answer1['id'] > actual_answer2['id']:
			actual_answer1 = actual_answer_pair['answer2']
			actual_answer2 = actual_answer_pair['answer1']
		# make sure that we actually got answers for the question we're targetting
		self.assertEqual(actual_answer1['id'], self.expected_answer1.id)
		self.assertEqual(actual_answer2['id'], self.expected_answer2.id)
		# additional testing in submit judgement

	def test_submit_judgement(self):
		# establish expected data by first getting an answer pair
		self.login(self.data.get_enroled_student().username)
		rv = self.client.get(self.answer_pair_url)
		self.assert200(rv)
		expected_answer_pair = rv.json
		expected_judgements = {
			'answerpair_id': rv.json['id'],
			'judgements': [
				{
					'course_criterion_id': self.course.criteriaandcourses[0].id,
					'answer_id_winner': rv.json['answer1']['id']
				}
			]
		}
		self.logout()
		# test login required
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert401(rv)
		# test deny access to unenroled users
		self.login(self.data.get_unenroled_student().username)
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		self.login(self.data.get_unenroled_instructor().username)
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		# test deny access to non-students
		self.login(self.data.get_enroled_instructor().username)
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert403(rv)
		self.logout()
		# authorized user from this point
		self.login(self.data.get_enroled_student().username)
		# test non-existent course
		rv = self.client.post(self._build_url(9999999, self.question.id),
			data=json.dumps(expected_judgements), content_type='application/json')
		self.assert404(rv)
		# test non-existent question
		rv = self.client.post(self._build_url(self.course.id, 9999999),
							  data=json.dumps(expected_judgements), content_type='application/json')
		self.assert404(rv)
		# test reject missing criteria
		faulty_judgements = copy.deepcopy(expected_judgements)
		faulty_judgements['judgements'] = []
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test reject missing course criteria id
		faulty_judgements = copy.deepcopy(expected_judgements)
		del faulty_judgements['judgements'][0]['course_criterion_id']
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test reject missing winner
		faulty_judgements = copy.deepcopy(expected_judgements)
		del faulty_judgements['judgements'][0]['answer_id_winner']
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid criteria id
		faulty_judgements = copy.deepcopy(expected_judgements)
		faulty_judgements['judgements'][0]['course_criterion_id'] = 3930230
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid winner id
		faulty_judgements = copy.deepcopy(expected_judgements)
		faulty_judgements['judgements'][0]['answer_id_winner'] = 2382301
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# test invalid answer pair
		faulty_judgements = copy.deepcopy(expected_judgements)
		faulty_judgements['answerpair_id'] = 2382301
		rv = self.client.post(self.base_url, data=json.dumps(faulty_judgements),
							  content_type='application/json')
		self.assert404(rv)
		# test normal post, should be the first judgement this question ever receives
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert200(rv)
		actual_judgements = rv.json['objects']
		self.assertEqual(len(actual_judgements), len(expected_judgements['judgements']),
			"The number of judgements saved does not match the number sent")
		for actual_judgement in actual_judgements:
			self.assertEqual(expected_answer_pair['answer1']['id'],
				actual_judgement['answerpairing']['postsforanswers_id1'],
				"Expected and actual judgement answer1 id did not match")
			self.assertEqual(expected_answer_pair['answer2']['id'],
				actual_judgement['answerpairing']['postsforanswers_id2'],
				"Expected and actual judgement answer2 id did not match")
			found_judgement = False
			for expected_judgement in expected_judgements['judgements']:
				if expected_judgement['course_criterion_id'] != \
					actual_judgement['course_criterion']['id']:
					continue
				self.assertEqual(expected_judgement['answer_id_winner'],
					actual_judgement['postsforanswers_id_winner'],
					"Expected and actual winner answer id did not match.")
				found_judgement = True
			self.assertTrue(found_judgement, "Actual judgement received contains a judgement that "
					"was not sent.")
		# Judgements has been entered, answers that have been judged less should be given priority
		# resubmit of same judgement should fail
		rv = self.client.post(self.base_url, data=json.dumps(expected_judgements),
							  content_type='application/json')
		self.assert400(rv)
		# all answers has been judged by the user, errors out when trying to get another pair
		rv = self.client.get(self.answer_pair_url)
		self.assert400(rv)
