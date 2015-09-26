import json
from acj import db

from data.fixtures.test_data import BasicTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import Courses


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
        self.assertTrue(course_expected.criteriaandcourses, "Course is missing a criteria")

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
            self.assertEqual(course_expected['description'], course_actual['description'])

            # Verify the course is created in db
            course_in_db = Courses.query.get(course_actual['id'])
            self.assertEqual(course_in_db.name, course_actual['name'])
            self.assertEqual(course_in_db.description, course_actual['description'])

            # create course with criteria
            course = course_expected.copy()
            course['name'] = 'ExpectedCourse2'
            course['criteria'] = [{'id': 1}]
            rv = self.client.post(
                '/api/courses',
                data=json.dumps(course), content_type='application/json')
            self.assert200(rv)
            course_actual = rv.json

            # Verify the course is created in db
            course_in_db = Courses.query.get(course_actual['id'])
            self.assertEqual(len(course_in_db.criteriaandcourses), 1)
            self.assertEqual(course_in_db.criteriaandcourses[0].criteria_id, course['criteria'][0]['id'])

    def test_create_duplicate_course(self):
        with self.login(self.data.get_authorized_instructor().username):
            course_existing = self.data.get_course()
            course_expected = {
                'name': course_existing.name,
                'description': course_existing.description
            }
            rv = self.client.post(
                '/api/courses',
                data=json.dumps(course_expected), content_type='application/json')
            self.assert400(rv)

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

            # test add criteria
            course = expected.copy()
            course['criteria'] = [{'id': 1}]
            rv = self.client.post(url, data=json.dumps(course), content_type='application/json')
            self.assert200(rv)

            db.session.expire_all()
            course_in_db = Courses.query.get(course['id'])
            self.assertEqual(len(course_in_db.criteriaandcourses), 1)
            self.assertEqual(course_in_db.criteriaandcourses[0].criteria_id, course['criteria'][0]['id'])

            # test remove criteria
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)

            # expire all instances in session and force session to query from db
            db.session.expire_all()
            course_in_db = Courses.query.get(course['id'])
            self.assertEqual(len(course_in_db.criteriaandcourses), 0)
