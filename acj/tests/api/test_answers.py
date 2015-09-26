import json
import datetime

from acj import db
from data.fixtures import PostsFactory, PostsForAnswersFactory
from data.fixtures.test_data import TestFixture
from acj.models import PostsForAnswers
from acj.tests.test_acj import ACJAPITestCase


class AnswersAPITests(ACJAPITestCase):
    def setUp(self):
        super(AnswersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=2)
        self.base_url = self._build_url(self.fixtures.course.id, self.fixtures.question.id)

    def _build_url(self, course_id, question_id, tail=""):
        url = '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/answers' + tail
        return url

    def test_get_all_answers(self):
        # Test login required
        rv = self.client.get(self.base_url)
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(self.base_url)
            self.assert403(rv)

        with self.login(self.fixtures.students[0].username):
            # test non-existent entry
            rv = self.client.get(self._build_url(self.fixtures.course.id, 4903409))
            self.assert404(rv)
            # test data retrieve is correct
            self.fixtures.question.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
            db.session.add(self.fixtures.question)
            db.session.commit()
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            expected_answers = PostsForAnswers.query.filter_by(questions_id=self.fixtures.question.id).paginate(1, 20)
            for i, expected in enumerate(expected_answers.items):
                actual = actual_answers[i]
                self.assertEqual(expected.content, actual['content'])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_answers.total, rv.json['total'])

            # test the second page
            rv = self.client.get(self.base_url + '?page=2')
            self.assert200(rv)
            actual_answers = rv.json['objects']
            expected_answers = PostsForAnswers.query.filter_by(questions_id=self.fixtures.question.id).paginate(2, 20)
            for i, expected in enumerate(expected_answers.items):
                actual = actual_answers[i]
                self.assertEqual(expected.content, actual['content'])
            self.assertEqual(2, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_answers.total, rv.json['total'])

            # test sorting
            rv = self.client.get(
                self.base_url + '?orderBy={}'.format(self.fixtures.question.criteria[0].id)
            )
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            expected = sorted(
                self.fixtures.answers,
                key=lambda ans: ans.scores[0].score if len(ans.scores) else 0,
                reverse=True)[:20]
            self.assertEqual([a.id for a in expected], [a['id'] for a in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_answers.total, rv.json['total'])

            # test author filter
            rv = self.client.get(self.base_url + '?author={}'.format(self.fixtures.students[0].id))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['user_id'], self.fixtures.students[0].id)

            # test group filter
            rv = self.client.get(self.base_url + '?group={}'.format(self.fixtures.groups[0].id))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), len(self.fixtures.answers) / len(self.fixtures.groups))

            # test ids filter
            ids = {str(a.id) for a in self.fixtures.answers[:3]}
            rv = self.client.get(self.base_url + '?ids={}'.format(','.join(ids)))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(ids, {str(a['id']) for a in result})

            # test combined filter
            rv = self.client.get(
                self.base_url + '?orderBy={}&group={}'.format(
                    self.fixtures.question.criteria[0].id,
                    self.fixtures.groups[0].id
                )
            )
            self.assert200(rv)
            result = rv.json['objects']
            # test the result is paged and sorted
            answers_per_group = int(len(self.fixtures.answers) / len(self.fixtures.groups)) if len(
                self.fixtures.groups) else 0
            answers = self.fixtures.answers[:answers_per_group]
            expected = sorted(answers, key=lambda ans: ans.scores[0].score, reverse=True)
            self.assertEqual([a.id for a in expected], [a['id'] for a in result])

            # all filters
            rv = self.client.get(
                self.base_url + '?orderBy={}&group={}&author={}&page=1&perPage=20'.format(
                    self.fixtures.question.criteria[0].id,
                    self.fixtures.groups[0].id,
                    self.fixtures.students[0].id
                )
            )
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['user_id'], self.fixtures.students[0].id)

            # add instructor answer
            post = PostsFactory(course=self.fixtures.course, user=self.fixtures.instructor)
            answer = PostsForAnswersFactory(question=self.fixtures.question, post=post)
            self.fixtures.answers.append(answer)
            db.session.commit()
            rv = self.client.get(self.base_url + '?orderBy={}'.format(self.fixtures.question.criteria[0].id))
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual(len(self.fixtures.answers), rv.json['total'])
            # first answer should be instructor answer
            self.assertEqual(self.fixtures.instructor.id, result[0]['user_id'])

            # test data retrieve before answer period ended with non-privileged user
            self.fixtures.question.answer_end = datetime.datetime.now() + datetime.timedelta(days=2)
            db.session.add(self.fixtures.question)
            db.session.commit()
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            self.assertEqual(1, len(actual_answers))
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

        # test data retrieve before answer period ended with privileged user
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self.base_url)
            self.assert200(rv)
            actual_answers = rv.json['objects']
            self.assertEqual(20, len(actual_answers))
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(self.fixtures.answers), rv.json['total'])

    def test_create_answer(self):
        # test login required
        expected_answer = {'content': 'this is some answer content'}
        response = self.client.post(
            self.base_url,
            data=json.dumps(expected_answer),
            content_type='application/json')
        self.assert401(response)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
            response = self.client.post(self.base_url, data=json.dumps(expected_answer),
                                        content_type='application/json')
            self.assert403(response)
        with self.login(self.fixtures.unauthorized_instructor.username):
            response = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert403(response)
        # test invalid format
        with self.login(self.fixtures.students[0].username):
            invalid_answer = {'post': {'blah': 'blah'}}
            response = self.client.post(
                self.base_url,
                data=json.dumps(invalid_answer),
                content_type='application/json')
            self.assert400(response)
            # test invalid question
            response = self.client.post(
                self._build_url(self.fixtures.course.id, 9392402),
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert404(response)
            # test invalid course
            response = self.client.post(
                self._build_url(9392402, self.fixtures.question.id),
                data=json.dumps(expected_answer), content_type='application/json')
            self.assert404(response)

        # test create successful
        with self.login(self.fixtures.instructor.username):
            response = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(response)
            # retrieve again and verify
            rv = json.loads(response.data.decode('utf-8'))
            actual_answer = PostsForAnswers.query.get(rv['id'])
            self.assertEqual(expected_answer['content'], actual_answer.post.content)

            # test instructor could submit multiple answers for his/her own
            response = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(response)
            rv = json.loads(response.data.decode('utf-8'))
            actual_answer = PostsForAnswers.query.get(rv['id'])
            self.assertEqual(expected_answer['content'], actual_answer.post.content)

            # test instructor could submit on behave of a student
            self.fixtures.add_students(1)
            expected_answer.update({'user': self.fixtures.students[-1].id})
            response = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert200(response)
            rv = json.loads(response.data.decode('utf-8'))
            actual_answer = PostsForAnswers.query.get(rv['id'])
            self.assertEqual(expected_answer['content'], actual_answer.post.content)

            # test instructor can not submit additional answers for a student
            expected_answer.update({'user': self.fixtures.students[0].id})
            response = self.client.post(
                self.base_url,
                data=json.dumps(expected_answer),
                content_type='application/json')
            self.assert400(response)
            rv = json.loads(response.data.decode('utf-8'))
            self.assertEqual({"error": "An answer has already been submitted."}, rv)

    def test_get_answer(self):
        question_id = self.fixtures.questions[0].id
        answer = self.fixtures.answers[0]

        # test login required
        rv = self.client.get(self.base_url + '/' + str(answer.id))
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self.base_url + '/' + str(answer.id))
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(self._build_url(999, question_id, '/' + str(answer.id)))
            self.assert404(rv)

            # test invalid answer id
            rv = self.client.get(self._build_url(self.fixtures.course.id, question_id, '/' + str(999)))
            self.assert404(rv)

            # test authorized student
            rv = self.client.get(self.base_url + '/' + str(answer.id))
            self.assert200(rv)
            self.assertEqual(question_id, rv.json['questions_id'])
            self.assertEqual(answer.post.users_id, rv.json['user_id'])
            self.assertEqual(answer.post.content, rv.json['content'])

        # test authorized teaching assistant
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(self.base_url + '/' + str(answer.id))
            self.assert200(rv)
            self.assertEqual(question_id, rv.json['questions_id'])
            self.assertEqual(answer.post.users_id, rv.json['user_id'])
            self.assertEqual(answer.post.content, rv.json['content'])

        # test authorized instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self.base_url + '/' + str(answer.id))
            self.assert200(rv)
            self.assertEqual(question_id, rv.json['questions_id'])
            self.assertEqual(answer.post.users_id, rv.json['user_id'])
            self.assertEqual(answer.post.content, rv.json['content'])

    def test_edit_answer(self):
        question_id = self.fixtures.questions[0].id
        answer = self.fixtures.answers[0]
        expected = {'id': str(answer.id), 'content': 'This is an edit'}

        # test login required
        rv = self.client.post(
            self.base_url + '/' + str(answer.id),
            data=json.dumps(expected),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.students[1].username):
            rv = self.client.post(
                self.base_url + '/' + str(answer.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self._build_url(999, question_id, '/' + str(answer.id)),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid question id
            rv = self.client.post(
                self._build_url(self.fixtures.course.id, 999, '/' + str(answer.id)),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

            # test invalid answer id
            rv = self.client.post(
                self.base_url + '/999',
                data=json.dumps(expected),
                content_type='application/json')
            self.assert404(rv)

        # test unmatched answer id
        with self.login(self.fixtures.students[1].username):
            rv = self.client.post(
                self.base_url + '/' + str(self.fixtures.answers[1].id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert400(rv)

        # test edit by author
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                self.base_url + '/' + str(answer.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(answer.id, rv.json['id'])
            self.assertEqual('This is an edit', rv.json['content'])

        # test edit by user that can manage posts
        expected['content'] = 'This is another edit'
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                self.base_url + '/' + str(answer.id),
                data=json.dumps(expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(answer.id, rv.json['id'])
            self.assertEqual('This is another edit', rv.json['content'])

    def test_delete_answer(self):
        answer_id = self.fixtures.answers[0].id

        # test login required
        rv = self.client.delete(self.base_url + '/' + str(answer_id))
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.students[1].username):
            rv = self.client.delete(self.base_url + '/' + str(answer_id))
            self.assert403(rv)

        # test invalid answer id
        with self.login(self.fixtures.students[0].username):
            rv = self.client.delete(self.base_url + '/999')
            self.assert404(rv)

            # test deletion by author
            rv = self.client.delete(self.base_url + '/' + str(answer_id))
            self.assert200(rv)
            self.assertEqual(answer_id, rv.json['id'])

        # test deletion by user that can manage posts
        with self.login(self.fixtures.instructor.username):
            answer_id2 = self.fixtures.answers[1].id
            rv = self.client.delete(self.base_url + '/' + str(answer_id2))
            self.assert200(rv)
            self.assertEqual(answer_id2, rv.json['id'])

    def test_get_user_answers(self):
        question_id = self.fixtures.questions[0].id
        answer = self.fixtures.answers[0]
        url = self._build_url(self.fixtures.course.id, question_id, '/user')

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test invalid course
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(self._build_url(999, question_id, '/user'))
            self.assert404(rv)

            # test invalid question
            rv = self.client.get(self._build_url(self.fixtures.course.id, 999, '/user'))
            self.assert404(rv)

            # test successful queries
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(1, len(rv.json['answer']))
            self.assertEqual(answer.id, rv.json['answer'][0]['id'])
            self.assertEqual(answer.post.content, rv.json['answer'][0]['content'])

        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['answer']))

    def test_flag_answer(self):
        answer = self.fixtures.question.answers[0]
        flag_url = self.base_url + "/" + str(answer.id) + "/flagged"
        # test login required
        expected_flag_on = {'flagged': True}
        expected_flag_off = {'flagged': False}
        rv = self.client.post(
            flag_url,
            data=json.dumps(expected_flag_on),
            content_type='application/json')
        self.assert401(rv)
        # test unauthorized users
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_on),
                content_type='application/json')
            self.assert403(rv)

        # test flagging
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_on),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                expected_flag_on['flagged'],
                rv.json['flagged'],
                "Expected answer to be flagged.")
            # test unflagging
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_off),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                expected_flag_off['flagged'],
                rv.json['flagged'],
                "Expected answer to be flagged.")

        # test prevent unflagging by other students
        with self.login(self.fixtures.students[0].username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_on),
                content_type='application/json')
            self.assert200(rv)

        # create another student
        self.fixtures.add_students(1)
        other_student = self.fixtures.students[-1]
        # try to unflag answer as other student, should fail
        with self.login(other_student.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_off),
                content_type='application/json')
            self.assert400(rv)

        # test allow unflagging by instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.post(
                flag_url,
                data=json.dumps(expected_flag_off),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(
                expected_flag_off['flagged'],
                rv.json['flagged'],
                "Expected answer to be flagged.")

    def test_get_question_answered(self):
        count_url = self.base_url + '/count'

        # test login required
        rv = self.client.get(count_url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(count_url)
            self.assert403(rv)

        # test invalid course id
        self.fixtures.add_students(1)
        with self.login(self.fixtures.students[-1].username):
            rv = self.client.get('/api/courses/999/questions/1/answers/count')
            self.assert404(rv)

            # test invalid question id
            rv = self.client.get('/api/courses/1/questions/999/answers/count')
            self.assert404(rv)

            # test successful query - no answers
            rv = self.client.get(count_url)
            self.assert200(rv)
            self.assertEqual(0, rv.json['answered'])

        # test successful query - answered
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(count_url)
            self.assert200(rv)
            self.assertEqual(1, rv.json['answered'])

    def test_get_answered_count(self):
        answered_url = '/api/courses/' + str(self.fixtures.course.id) + '/answers/answered'

        # test login required
        rv = self.client.get(answered_url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.get(answered_url)
            self.assert403(rv)

        # test invalid course id
        self.fixtures.add_students(1)
        with self.login(self.fixtures.students[-1].username):
            rv = self.client.get('/api/courses/999/answered')
            self.assert404(rv)

            # test successful query - have not answered any questions in the course
            rv = self.client.get(answered_url)
            self.assert200(rv)
            self.assertEqual(0, len(rv.json['answered']))

        # test successful query - have submitted one answer per question
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(answered_url)
            self.assert200(rv)
            expected = {str(question.id): 1 for question in self.fixtures.questions}
            self.assertEqual(expected, rv.json['answered'])

    def test_get_answers_view(self):
        view_url = \
            '/api/courses/' + str(self.fixtures.course.id) + '/questions/' + \
            str(self.fixtures.questions[0].id) + '/answers/view'

        # test login required
        rv = self.client.get(view_url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(view_url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get('/api/courses/999/questions/' + str(self.fixtures.questions[0].id) + '/answers/view')
            self.assert404(rv)

            # test invalid question id
            rv = self.client.get('/api/courses/' + str(self.fixtures.course.id) + '/questions/999/answers/view')
            self.assert404(rv)

            # test successful query
            rv = self.client.get(view_url)
            self.assert200(rv)
            expected = self.fixtures.answers

            self.assertEqual(30, len(rv.json['answers']))
            for i, exp in enumerate(expected):
                actual = rv.json['answers'][str(exp.id)]
                self.assertEqual(exp.id, actual['id'])
                self.assertEqual(exp.post.content, actual['content'])
                self.assertFalse(actual['file'])

        # test successful query - student
        with self.login(self.fixtures.students[0].username):
            rv = self.client.get(view_url)
            self.assert200(rv)

            actual = rv.json['answers']
            expected = self.fixtures.answers[0]

            self.assertEqual(1, len(actual))
            self.assertTrue(str(expected.id) in actual)
            answer = actual[str(expected.id)]
            self.assertEqual(expected.id, answer['id'])
            self.assertEqual(expected.post.content, answer['content'])
            self.assertFalse(answer['file'])
            self.assertFalse('scores' in answer)
