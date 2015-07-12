import json
from dateutil import parser

from data.fixtures.test_data import JudgementCommentsTestData

from acj.tests.test_acj import ACJTestCase


class EvalCommentsAPITests(ACJTestCase):
	def setUp(self):
		super(EvalCommentsAPITests, self).setUp()
		self.data = JudgementCommentsTestData()

	# may need judgement comment data

	def _build_url(self, course_id, question_id, tail=""):
		url = \
			'/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/judgements/' + \
			'comments' + tail
		return url

	def test_get_eval_comments(self):
		url = self._build_url(self.data.get_course().id, self.data.get_questions()[0].id)

		# test login required
		rv = self.client.get(url)
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_unauthorized_instructor().username)
		rv = self.client.get(url)
		self.assert403(rv)
		self.logout()

		# test invalid course id
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.get(self._build_url(999, self.data.get_questions()[0].id))
		self.assert404(rv)

		# test invalid question id
		rv = self.client.get(self._build_url(self.data.get_course().id, 999))
		self.assert404(rv)

		# test no comments
		rv = self.client.get(self._build_url(self.data.get_course().id, self.data.get_questions()[1].id))
		self.assert200(rv)
		expected = []
		self.assertEqual(expected, rv.json['comments'])

		# test success query
		rv = self.client.get(url)
		self.assert200(rv)
		expected = self.data.get_judge_comment()
		actual = rv.json['comments'][0]
		self.assertEqual(expected.judgements_id, actual['judgement']['id'])
		self.assertEqual(expected.comments_id, actual['postsforcomments']['id'])
		self.assertEqual(expected.postsforcomments.post.content, actual['postsforcomments']['post']['content'])

	def test_create_eval_comment(self):
		url = self._build_url(self.data.get_course().id, self.data.get_questions()[1].id)
		content = {'judgements': []}
		judge = {
			'id': self.data.get_judge_2().id,
			'comment': "A is better than B because A used the correct formula."
		}
		content['judgements'].append(judge)

		# test login required
		rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
		self.assert401(rv)

		# test unauthorized user
		self.login(self.data.get_authorized_instructor().username)
		rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
		self.assert403(rv)
		self.logout()

		self.login(self.data.get_judging_student().username)
		# test invalid course id
		invalid_url = self._build_url(999, self.data.get_questions()[1].id)
		rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
		self.assert404(rv)

		# test invalid question id
		invalid_url = self._build_url(self.data.get_course().id, 999)
		rv = self.client.post(invalid_url, data=json.dumps(content), content_type='application/json')
		self.assert404(rv)

		# test successful save
		rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
		self.assert200(rv)
		actual = rv.json['objects'][0]
		self.assertEqual(judge['id'], actual['judgement']['id'])
		self.assertEqual(judge['comment'], actual['postsforcomments']['post']['content'])

		# test invalid judgement id
		content['judgements'][0]['id'] = 999
		rv = self.client.post(url, data=json.dumps(content), content_type='application/json')
		self.assert404(rv)

	def test_eval_comment_view(self):
		url = self._build_url(self.data.get_course().id, self.data.get_questions()[0].id, '/view')

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
		rv = self.client.get(self._build_url(999, self.data.get_questions()[0].id, '/view'))
		self.assert404(rv)

		# test invalid question id
		rv = self.client.get(self._build_url(self.data.get_course().id, 999, '/view'))
		self.assert404(rv)

		# test successful query - instructor
		rv = self.client.get(url)
		self.assert200(rv)
		actual = rv.json['comparisons'][0][0]
		expected = self.data.get_judge_comment()

		self.assertEqual(len(rv.json['comparisons']), 1)
		self.assertEqual(actual['name'], self.data.get_judging_student().fullname)
		self.assertEqual(actual['avatar'], self.data.get_judging_student().avatar)
		self.assertEqual(
			actual['criteriaandquestions_id'],
			self.data.get_criteria_by_question(self.data.get_questions()[0]).id)
		self.assertEqual(actual['content'], expected.postsforcomments.post.content)
		self.assertFalse(actual['selfeval'])
		self.assertEqual(parser.parse(actual['created']).replace(tzinfo=None), expected.postsforcomments.post.created)
		self.assertEqual(actual['answer1']['id'], expected.judgement.answerpairing.answers_id1)
		self.assertEqual(
			actual['answer1']['feedback'],
			self.data.get_judge_feedback()[actual['answer1']['id']].content)
		self.assertEqual(actual['answer2']['id'], expected.judgement.answerpairing.answers_id2)
		self.assertEqual(
			actual['answer2']['feedback'],
			self.data.get_judge_feedback()[actual['answer2']['id']].content)
		self.assertEqual(actual['winner'], expected.judgement.answers_id_winner)
		self.logout()

		# test successful query - TA
		self.login(self.data.get_authorized_ta().username)
		rv = self.client.get(url)
		self.assert200(rv)
		actual = rv.json['comparisons'][0][0]
		expected = self.data.get_judge_comment()

		self.assertEqual(len(rv.json['comparisons']), 1)
		self.assertEqual(actual['name'], self.data.get_judging_student().fullname)
		self.assertEqual(actual['avatar'], self.data.get_judging_student().avatar)
		self.assertEqual(
			actual['criteriaandquestions_id'],
			self.data.get_criteria_by_question(self.data.get_questions()[0]).id)
		self.assertEqual(actual['content'], expected.postsforcomments.post.content)
		self.assertFalse(actual['selfeval'])
		self.assertEqual(parser.parse(actual['created']).replace(tzinfo=None), expected.postsforcomments.post.created)
		self.assertEqual(actual['answer1']['id'], expected.judgement.answerpairing.answers_id1)
		self.assertEqual(
			actual['answer1']['feedback'],
			self.data.get_judge_feedback()[actual['answer1']['id']].content)
		self.assertEqual(actual['answer2']['id'], expected.judgement.answerpairing.answers_id2)
		self.assertEqual(
			actual['answer2']['feedback'],
			self.data.get_judge_feedback()[actual['answer2']['id']].content)
		self.assertEqual(actual['winner'], expected.judgement.answers_id_winner)
		self.logout()

		# test successful query - student
		self.login(self.data.get_judging_student().username)
		rv = self.client.get(url)
		self.assert200(rv)
		actual = rv.json['comparisons'][0][0]

		self.assertEqual(len(rv.json['comparisons']), 1)
		self.assertEqual(actual['name'], self.data.get_judging_student().fullname)
		self.assertEqual(actual['avatar'], self.data.get_judging_student().avatar)
		self.assertEqual(
			actual['criteriaandquestions_id'],
			self.data.get_criteria_by_question(self.data.get_questions()[0]).id)
		self.assertEqual(actual['content'], expected.postsforcomments.post.content)
		self.assertFalse(actual['selfeval'])
		self.assertEqual(parser.parse(actual['created']).replace(tzinfo=None), expected.postsforcomments.post.created)
		self.assertEqual(actual['answer1']['id'], expected.judgement.answerpairing.answers_id1)
		self.assertEqual(
			actual['answer1']['feedback'],
			self.data.get_judge_feedback()[actual['answer1']['id']].content)
		self.assertEqual(actual['answer2']['id'], expected.judgement.answerpairing.answers_id2)
		self.assertEqual(
			actual['answer2']['feedback'],
			self.data.get_judge_feedback()[actual['answer2']['id']].content)
		self.assertEqual(actual['winner'], expected.judgement.answers_id_winner)
		self.logout()
