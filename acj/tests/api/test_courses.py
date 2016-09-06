import datetime
import json
from acj import db

from data.fixtures.test_data import BasicTestData, ComparisonTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import Course, UserCourse


class CoursesAPITests(ACJAPITestCase):
    def setUp(self):
        super(CoursesAPITests, self).setUp()
        self.data = BasicTestData()

    def _verify_course_info(self, course_expected, course_actual):
        self.assertEqual(
            course_expected.name, course_actual['name'],
            "Expected course name does not match actual.")
        self.assertEqual(
            course_expected.id, course_actual['id'],
            "Expected course id does not match actual.")
        self.assertEqual(
            course_expected.description, course_actual['description'],
            "Expected course description does not match actual.")
        self.assertEqual(
            course_expected.year, course_actual['year'],
            "Expected course description does not match actual.")
        self.assertEqual(
            course_expected.term, course_actual['term'],
            "Expected course description does not match actual.")
        self.assertEqual(
            course_expected.available, course_actual['available'],
            "Expected course availability does not match actual.")

    def test_get_single_course(self):
        course_api_url = '/api/courses/' + str(self.data.get_course().id)

        # Test login required
        rv = self.client.get(course_api_url)
        self.assert401(rv)

        # Test root get course
        with self.login('root'):
            rv = self.client.get(course_api_url)
            self.assert200(rv)
            self._verify_course_info(self.data.get_course(), rv.json)

        # Test enroled users get course info
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(course_api_url)
            self.assert200(rv)
            self._verify_course_info(self.data.get_course(), rv.json)

        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(course_api_url)
            self.assert200(rv)
            self._verify_course_info(self.data.get_course(), rv.json)

        # Test unenroled user not permitted to get info
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(course_api_url)
            self.assert403(rv)

        with self.login(self.data.get_unauthorized_student().username):
            rv = self.client.get(course_api_url)
            self.assert403(rv)

        # Test get invalid course
        with self.login("root"):
            rv = self.client.get('/api/courses/38940450')
            self.assert404(rv)

    def test_get_all_courses(self):
        course_api_url = '/api/courses'

        # Test login required
        rv = self.client.get(course_api_url)
        self.assert401(rv)

        # Test only root can get a list of all courses
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(course_api_url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(course_api_url)
            self.assert403(rv)

        with self.login("root"):
            rv = self.client.get(course_api_url)
            self.assert200(rv)
            self._verify_course_info(self.data.get_course(), rv.json['objects'][0])

    def test_create_course(self):
        course_expected = {
            'name': 'ExpectedCourse1',
            'year': 2015,
            'term': 'Winter',
            'start_date': None,
            'end_date': None,
            'description': 'Test Course One Description Test'
        }
        # Test login required
        rv = self.client.post(
            '/api/courses',
            data=json.dumps(course_expected), content_type='application/json')
        self.assert401(rv)
        # Test unauthorized user
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(
                '/api/courses',
                data=json.dumps(course_expected), content_type='application/json')
            self.assert403(rv)

        # Test course creation
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/courses',
                data=json.dumps(course_expected), content_type='application/json')
            self.assert200(rv)
            # Verify return
            course_actual = rv.json
            self.assertEqual(course_expected['name'], course_actual['name'])
            self.assertEqual(course_expected['year'], course_actual['year'])
            self.assertEqual(course_expected['term'], course_actual['term'])
            self.assertEqual(course_expected['description'], course_actual['description'])
            self.assertTrue(course_actual['available'])

            # Verify the course is created in db
            course_in_db = Course.query.get(course_actual['id'])
            self.assertEqual(course_in_db.name, course_actual['name'])
            self.assertEqual(course_in_db.year, course_actual['year'])
            self.assertEqual(course_in_db.term, course_actual['term'])
            self.assertEqual(course_in_db.description, course_actual['description'])
            self.assertTrue(course_in_db.available)

            # Verify instructor added to course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_id=course_actual['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

            # Starts in the future
            now = datetime.datetime.utcnow()
            course_expected['start_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            course_expected['end_date'] = None
            rv = self.client.post('/api/courses', data=json.dumps(course_expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Ended in the past
            course_expected['start_date'] = None
            course_expected['end_date'] = (now - datetime.timedelta(days=7)).isoformat() + 'Z',
            rv = self.client.post('/api/courses', data=json.dumps(course_expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Is currently available
            course_expected['start_date'] = (now - datetime.timedelta(days=7)).isoformat() + 'Z',
            course_expected['end_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            rv = self.client.post('/api/courses', data=json.dumps(course_expected), content_type='application/json')
            self.assert200(rv)
            self.assertTrue(rv.json['available'])

    def test_create_course_with_bad_data_format(self):
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/courses',
                data=json.dumps({'description': 'd'}), content_type='application/json')
            self.assert400(rv)

    def test_edit_course(self):
        expected = {
            'id': self.data.get_course().id,
            'name': 'ExpectedCourse',
            'year': 2015,
            'term': 'Winter',
            'start_date': None,
            'end_date': None,
            'description': 'Test Description'
        }
        url = '/api/courses/' + str(self.data.get_course().id)

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

            # test unmatched course id
            rv = self.client.post(
                '/api/courses/' + str(self.data.get_secondary_course().id),
                data=json.dumps(expected), content_type='application/json')
            self.assert400(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.post('/api/courses/999', data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test authorized user
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            db.session.expire_all()
            self.assertEqual(expected['id'], rv.json['id'])
            self.assertEqual(expected['name'], rv.json['name'])
            self.assertEqual(expected['description'], rv.json['description'])
            self.assertTrue(rv.json['available'])

            # Starts in the future
            now = datetime.datetime.utcnow()
            expected['start_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            expected['end_date'] = None
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Ended in the past
            expected['start_date'] = None
            expected['end_date'] = (now - datetime.timedelta(days=7)).isoformat() + 'Z',
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Is currently available
            expected['start_date'] = (now - datetime.timedelta(days=7)).isoformat() + 'Z',
            expected['end_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.assertTrue(rv.json['available'])

    def test_duplicate_course_simple(self):
        url = '/api/courses/' + str(self.data.get_course().id) + '/duplicate'
        expected = {
            'year': 2015,
            'term': 'Winter',
        }
        # test login required
        rv = self.client.post(url, content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test year missing
            invalid_expected = {
                'term': 'Winter'
            }
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert404(rv)

            # test term missing
            invalid_expected = {
                'year': 2015
            }
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert404(rv)

            # test authorized user
            original_course = self.data.get_course()
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)

            # verify course duplicated correctly
            self.assertNotEqual(original_course.id, rv.json['id'])
            self.assertEqual(original_course.name, rv.json['name'])
            self.assertEqual(expected['year'], rv.json['year'])
            self.assertEqual(expected['term'], rv.json['term'])
            self.assertEqual(original_course.description, rv.json['description'])

            # verify instructor added to duplicate course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_id=rv.json['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

class CoursesDuplicateComplexAPITests(ACJAPITestCase):
    def setUp(self):
        super(CoursesDuplicateComplexAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.url = '/api/courses/' + str(self.data.get_course().id) + '/duplicate'
        self.expected = {
            'year': 2015,
            'term': 'Winter',
        }

    def test_duplicate_course_complex(self):
        original_course = self.data.get_course()

        # test authorized user
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(self.url, data=json.dumps(self.expected), content_type='application/json')
            self.assert200(rv)

            duplicate_course = Course.query.get(rv.json['id'])
            self.assertIsNotNone(duplicate_course)

            # verify course duplicated correctly
            self.assertNotEqual(original_course.id, duplicate_course.id)
            self.assertEqual(original_course.name, duplicate_course.name)
            self.assertEqual(self.expected['year'], duplicate_course.year)
            self.assertEqual(self.expected['term'], duplicate_course.term)
            self.assertEqual(original_course.description, duplicate_course.description)

            # verify instructor added to duplicate course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_id=rv.json['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

            original_assignments = original_course.assignments.all()
            duplicate_assignments = duplicate_course.assignments.all()

            self.assertEqual(len(original_assignments), 3)
            self.assertEqual(len(original_assignments), len(duplicate_assignments))

            for index, original_assignment in enumerate(original_assignments):
                duplicate_assignment = duplicate_assignments[index]

                self.assertNotEqual(original_assignment.id, duplicate_assignment.id)
                self.assertEqual(duplicate_course.id, duplicate_assignment.course_id)
                self.assertEqual(original_assignment.name, duplicate_assignment.name)
                self.assertEqual(original_assignment.description, duplicate_assignment.description)
                self.assertEqual(original_assignment.number_of_comparisons, duplicate_assignment.number_of_comparisons)
                self.assertEqual(original_assignment.students_can_reply, duplicate_assignment.students_can_reply)
                self.assertEqual(original_assignment.enable_self_evaluation, duplicate_assignment.enable_self_evaluation)
                self.assertEqual(original_assignment.pairing_algorithm, duplicate_assignment.pairing_algorithm)

                self.assertEqual(len(original_assignment.criteria), 1)
                self.assertEqual(len(original_assignment.criteria), len(duplicate_assignment.criteria))

                for index, original_criteria in enumerate(original_assignment.criteria):
                    duplicate_criteria = duplicate_assignment.criteria[index]
                    self.assertEqual(original_criteria.id, duplicate_criteria.id)


                original_comparison_examples = original_assignment.comparison_examples.all()
                duplicate_comparison_examples = duplicate_assignment.comparison_examples.all()

                if original_assignment.id in [1,2]:
                    self.assertEqual(len(original_comparison_examples), 1)
                else:
                    self.assertEqual(len(original_comparison_examples), 0)
                self.assertEqual(len(original_comparison_examples), len(duplicate_comparison_examples))

                for index, original_comparison_example in enumerate(original_comparison_examples):
                    duplicate_comparison_example = duplicate_comparison_examples[index]

                    self.assertNotEqual(original_comparison_example.id, duplicate_comparison_example.id)
                    self.assertNotEqual(original_comparison_example.answer1_id, duplicate_comparison_example.answer1_id)
                    self.assertNotEqual(original_comparison_example.answer2_id, duplicate_comparison_example.answer2_id)
                    self.assertEqual(duplicate_assignment.id, duplicate_comparison_example.assignment_id)

                    original_answer1 = original_comparison_example.answer1
                    duplicate_answer1 = duplicate_comparison_example.answer1

                    self.assertNotEqual(original_answer1.id, duplicate_answer1.id)
                    self.assertEqual(duplicate_assignment.id, duplicate_answer1.assignment_id)
                    self.assertEqual(original_answer1.content, duplicate_answer1.content)

                    original_answer2 = original_comparison_example.answer2
                    duplicate_answer2 = duplicate_comparison_example.answer2

                    self.assertNotEqual(original_answer2.id, duplicate_answer2.id)
                    self.assertEqual(duplicate_assignment.id, duplicate_answer2.assignment_id)
                    self.assertEqual(original_answer2.content, duplicate_answer2.content)