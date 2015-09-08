import json

from data.fixtures.test_data import CriteriaTestData
from acj.tests.test_acj import ACJTestCase


class CriteriaAPITests(ACJTestCase):
    def setUp(self):
        super(CriteriaAPITests, self).setUp()
        self.data = CriteriaTestData()

    def _verify_course_critera(self, criteria_expected, criteria_actual):
        self.assertEqual(
            criteria_expected.name, criteria_actual['name'],
            'Expected criterion name does not match actual.')
        self.assertEqual(
            criteria_expected.description, criteria_actual['description'],
            'Expected criterion description does not match actual')

    def _verify_critera(self, criteria_expected, criteria_actual):
        self.assertEqual(
            criteria_expected.name, criteria_actual['name'],
            'Expected criterion name does not match actual.')
        self.assertEqual(
            criteria_expected.description, criteria_actual['description'],
            'Expected criterion description does not match actual')

    def _build_question_criteria_url(self, course_id, question_id, criteria_id):
        return '/api/courses/' + str(course_id) + '/questions/' + str(question_id) + '/criteria/' + str(criteria_id)

    def test_get_all_criteria_course(self):
        course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria'

        # Test login required
        rv = self.client.get(course_criteria_api_url)
        self.assert401(rv)

        # Test get criteria attached to course
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(course_criteria_api_url)
            self.assert200(rv)
            criteria_expected = self.data.get_default_criteria()
            criteria_actual = rv.json['objects'][0]
            self._verify_course_critera(criteria_expected, criteria_actual)
            # only one criteria - the other one is inactive
            self.assertEqual(len(rv.json['objects']), 1)

        # Test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get('/api/courses/999/criteria')
            self.assert404(rv)

    def test_create_criteria(self):
        course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria'
        criteria_expected = {
            'name': 'Which is more accurate?',
            'description': 'Please answer honestly.'
        }

        # Test login required
        rv = self.client.post(
            course_criteria_api_url,
            data=json.dumps(criteria_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/courses/999/criteria',
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert404(rv)

            # Test successful criteria creation
            rv = self.client.post(
                course_criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            criteria_actual = rv.json['criterion']
            self.assertEqual(criteria_expected['name'], criteria_actual['name'])
            self.assertEqual(criteria_expected['description'], criteria_actual['description'])

        # Test fail criteria creation - unauthorized
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                course_criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert403(rv)

    def test_get_criteria(self):
        criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)

        # Test login required
        rv = self.client.get(criteria_api_url)
        self.assert401(rv)

        # Test author access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            self._verify_course_critera(self.data.get_criteria(), rv.json)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert403(rv)

        # Test admin access
        with self.login('root'):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            self._verify_course_critera(self.data.get_criteria(), rv.json)

            # Test invalid criteria id
            rv = self.client.get('/api/criteria/999')
            self.assert404(rv)

    def test_edit_criteria(self):
        criteria_api_url = '/api/criteria/' + str(self.data.get_criteria().id)
        criteria_expected = {
            'id': self.data.get_criteria().id,
            'name': 'Which is more correct?',
            'description': 'Please answer more honestly.'
        }

        # Test login required
        rv = self.client.post(
            criteria_api_url,
            data=json.dumps(criteria_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert403(rv)

        # Test invalid criteria id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/criteria/999',
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert404(rv)

            # Test author access
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(criteria_expected['name'], rv.json['criterion']['name'])
            self.assertEqual(criteria_expected['description'], rv.json['criterion']['description'])

        # Test admin access
        # admin_criteria_expected = self.data.get_criteria()
        admin_criteria_expected = {
            'id': self.data.get_criteria().id,
            'name': 'Which one uses the correct formula?',
            'description': 'Hint: Law of Physics.'
        }
        with self.login('root'):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(admin_criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(admin_criteria_expected['name'], rv.json['criterion']['name'])
            self.assertEqual(admin_criteria_expected['description'], rv.json['criterion']['description'])

    def test_get_available_criteria(self):
        criteria_api_url = '/api/criteria'

        # Test login required
        rv = self.client.get(criteria_api_url)
        self.assert401(rv)

        # Test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # one public + two authored
            self.assertEqual(len(rv.json['criteria']), 3)
            self._verify_critera(self.data.get_default_criteria(), rv.json['criteria'][0])
            self._verify_critera(self.data.get_criteria(), rv.json['criteria'][1])

        # Test unauthorized instructor
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # one public + one authored
            self.assertEqual(len(rv.json['criteria']), 2)
            self._verify_critera(self.data.get_default_criteria(), rv.json['criteria'][0])
            self._verify_critera(self.data.get_secondary_criteria(), rv.json['criteria'][1])

        # Test admin
        with self.login('root'):
            rv = self.client.get(criteria_api_url)
            self.assert200(rv)
            # return all
            self.assertEqual(len(rv.json['criteria']), 4)
            self._verify_critera(self.data.get_default_criteria(), rv.json['criteria'][0])
            self._verify_critera(self.data.get_criteria(), rv.json['criteria'][1])
            self._verify_critera(self.data.get_secondary_criteria(), rv.json['criteria'][2])

    def test_deactivate_criteria(self):
        course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria/' + str(
            self.data.get_default_criteria().id)

        # Test login required
        rv = self.client.delete(course_criteria_api_url)
        self.assert401(rv)

        # Test invalid criteria_course
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/courses/999/criteria/' + str(self.data.get_default_criteria().id)
            rv = self.client.delete(url)
            self.assert404(rv)

            url = '/api/courses/' + str(self.data.get_course().id) + '/criteria/999'
            rv = self.client.delete(url)
            self.assert404(rv)

        # Test unauthorized user
        url = '/api/courses/' + str(self.data.get_secondary_course().id) + '/criteria/' + str(
            self.data.get_default_criteria().id)
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # Test authorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(self.data.get_default_criteria().id, rv.json['criterionId'])

        # Test attempt to remove course criteria that is already used in a question
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(course_criteria_api_url)
            self.assert403(rv)

        # Test admin
        with self.login('root'):
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(self.data.get_default_criteria().id, rv.json['criterionId'])

    def test_create_criteria_course(self):
        course_criteria_api_url = '/api/courses/' + str(self.data.get_course().id) + '/criteria/' + str(
            self.data.get_criteria().id)

        # Test login required
        rv = self.client.post(course_criteria_api_url)
        self.assert401(rv)

        # Test invalid criteria_course
        with self.login(self.data.get_authorized_instructor().username):
            url = '/api/courses/999/criteria/' + str(self.data.get_criteria().id)
            rv = self.client.post(url)
            self.assert404(rv)

            url = '/api/courses/' + str(self.data.get_course().id) + '/criteria/999'
            rv = self.client.post(url)
            self.assert404(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(course_criteria_api_url)
            self.assert403(rv)

        # Test authorized user
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(course_criteria_api_url)
            self.assert200(rv)
            expected_criteria_course = self.data.get_inactive_criteria_course()
            expected_criteria_course.active = True
            self.assertTrue(rv.json['criterion']['active'])

        # Test admin
        with self.login('root'):
            rv = self.client.post(course_criteria_api_url)
            self.assert200(rv)
            self.assertTrue(rv.json['criterion']['active'])

    def test_add_critera_course(self):
        criteria_api_url = '/api/criteria'
        criteria_expected = {
            'name': 'Which is more elaborate?',
            'description': 'Please answer accurately.'
        }

        # Test login required
        rv = self.client.post(
            criteria_api_url,
            data=json.dumps(criteria_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user - eg. student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert403(rv)

        # Test authorized user
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                criteria_api_url,
                data=json.dumps(criteria_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(criteria_expected['name'], rv.json['name'])
            self.assertEqual(criteria_expected['description'], rv.json['description'])

    def test_create_question_criteria(self):
        course_id = self.data.get_course().id
        question_id = self.data.get_questions()[0].id
        criteria_id = self.data.get_criteria2().id
        url = self._build_question_criteria_url(course_id, question_id, criteria_id)

        # test login required
        rv = self.client.post(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url)
            self.assert403(rv)

        # test invalid course
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.post(self._build_question_criteria_url(999, question_id, criteria_id))
            self.assert404(rv)

            # test invalid question id
            rv = self.client.post(self._build_question_criteria_url(course_id, 999, criteria_id))
            self.assert404(rv)

            # test invalid criteria_id
            rv = self.client.post(self._build_question_criteria_url(course_id, question_id, 999))
            self.assert404(rv)

            # test authorized teaching assistant
            rv = self.client.post(url)
            self.assert200(rv)
            self.assertEqual(criteria_id, rv.json['criterion']['criterion']['id'])
            self.assertEqual(True, rv.json['criterion']['active'])

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url)
            self.assert200(rv)
            self.assertEqual(criteria_id, rv.json['criterion']['criterion']['id'])
            self.assertEqual(True, rv.json['criterion']['active'])

            # test activating inactive criterion
            rv = self.client.post(
                self._build_question_criteria_url(course_id, question_id, self.data.get_criteria().id))
            self.assert200(rv)
            self.assertEqual(self.data.get_criteria().id, rv.json['criterion']['criterion']['id'])
            self.assertEqual(True, rv.json['criterion']['active'])

    def test_deactivate_question_criteria(self):
        course_id = self.data.get_course().id
        question_id = self.data.get_questions()[0].id
        criteria_id = self.data.get_default_criteria().id
        url = self._build_question_criteria_url(course_id, question_id, criteria_id)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.delete(self._build_question_criteria_url(999, question_id, criteria_id))
            self.assert404(rv)

            # test invalid question id
            rv = self.client.delete(self._build_question_criteria_url(course_id, 999, criteria_id))
            self.assert404(rv)

            # test invalid criteria id
            rv = self.client.delete(self._build_question_criteria_url(course_id, question_id, 999))
            self.assert404(rv)

            # test invalid criteria and question pair
            rv = self.client.delete(self._build_question_criteria_url(
                course_id, question_id,
                self.data.get_criteria().id))
            self.assert404(rv)

            # test authorized teaching assistant
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(criteria_id, rv.json['criterion']['criterion']['id'])
            self.assertEqual(False, rv.json['criterion']['active'])

        # test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(criteria_id, rv.json['criterion']['criterion']['id'])
            self.assertEqual(False, rv.json['criterion']['active'])
