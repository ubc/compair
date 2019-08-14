# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import json
from random import choice
from string import ascii_letters
from compair import db

from data.fixtures import DefaultFixture
from data.fixtures.test_data import BasicTestData, ComparisonTestData, LTITestData, SimpleAssignmentTestData
from compair.tests.test_compair import ComPAIRAPITestCase, ComPAIRAPIDemoTestCase
from compair.models import Course, UserCourse


class CoursesAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(CoursesAPITests, self).setUp()
        self.data = BasicTestData()

    def _verify_course_info(self, course_expected, course_actual):
        self.assertEqual(
            course_expected.name, course_actual['name'],
            "Expected course name does not match actual.")
        self.assertEqual(
            course_expected.uuid, course_actual['id'],
            "Expected course id does not match actual.")
        self.assertEqual(
            course_expected.year, course_actual['year'],
            "Expected course year does not match actual.")
        self.assertEqual(
            course_expected.term, course_actual['term'],
            "Expected course term does not match actual.")
        self.assertEqual(
            course_expected.sandbox, course_actual['sandbox'],
            "Expected course sandbox flag does not match actual.")
        self.assertEqual(
            course_expected.available, course_actual['available'],
            "Expected course availability does not match actual.")

    def test_get_single_course(self):
        course_api_url = '/api/courses/' + self.data.get_course().uuid

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

        student = self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.get(course_api_url)
                self.assert200(rv)
                self._verify_course_info(self.data.get_course(), rv.json)

        # Test unenroled user not permitted to get info
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(course_api_url)
            self.assert403(rv)

        student = self.data.get_unauthorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(DefaultFixture.ROOT_USER, student)]:
            with user_context:
                rv = self.client.get(course_api_url)
                self.assert403(rv)

        # Test get invalid course
        with self.login("root"):
            rv = self.client.get('/api/courses/38940450')
            self.assert404(rv)

    def test_create_course(self):
        course_expected = {
            'name': 'ExpectedCourse1',
            'year': 2015,
            'term': 'Winter',
            'sandbox' : False,
            'start_date': datetime.datetime.utcnow().isoformat() + 'Z',
            'end_date': None
        }
        # Test login required
        rv = self.client.post(
            '/api/courses',
            data=json.dumps(course_expected), content_type='application/json')
        self.assert401(rv)
        # Test unauthorized user
        student = self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
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
            self.assertEqual(course_expected['sandbox'], course_actual['sandbox'])
            self.assertTrue(course_actual['available'])

            # Verify the course is created in db
            course_in_db = Course.query.filter_by(uuid=course_actual['id']).first()
            self.assertEqual(course_in_db.name, course_actual['name'])
            self.assertEqual(course_in_db.year, course_actual['year'])
            self.assertEqual(course_in_db.term, course_actual['term'])
            self.assertEqual(course_in_db.sandbox, course_actual['sandbox'])
            self.assertTrue(course_in_db.available)

            # Verify instructor added to course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_uuid=course_actual['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

            # Start date missing
            invalid_expected = course_expected.copy()
            invalid_expected['start_date'] = None
            rv = self.client.post('/api/courses', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["message"]["start_date"], "Course start date is required.")

            # Starts in the future
            now = datetime.datetime.utcnow()
            course_expected['start_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            course_expected['end_date'] = None
            rv = self.client.post('/api/courses', data=json.dumps(course_expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Ended in the past
            course_expected['start_date'] = (now - datetime.timedelta(days=14)).isoformat() + 'Z',
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
                data=json.dumps({'year': 'd'}), content_type='application/json')
            self.assert400(rv)

    def test_edit_course(self):
        expected = {
            'id': self.data.get_course().uuid,
            'name': 'ExpectedCourse',
            'year': 2015,
            'term': 'Winter',
            'sandbox': False,
            'start_date': datetime.datetime.utcnow().isoformat() + 'Z',
            'end_date': None
        }
        url = '/api/courses/' + self.data.get_course().uuid

        # test login required
        rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
        self.assert401(rv)

        # test with student
        student = self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert403(rv)

                # test unmatched course id
                rv = self.client.post(
                    '/api/courses/' + self.data.get_secondary_course().uuid,
                    data=json.dumps(expected), content_type='application/json')
                self.assert403(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

            # test unmatched course id
            rv = self.client.post(
                '/api/courses/' + self.data.get_secondary_course().uuid,
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
            self.assertTrue(rv.json['available'])

            # Start date missing
            invalid = expected.copy()
            invalid['start_date'] = None
            rv = self.client.post(url, data=json.dumps(invalid), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["message"]["start_date"], "Course start date is required.")

            # Starts in the future
            now = datetime.datetime.utcnow()
            expected['start_date'] = (now + datetime.timedelta(days=7)).isoformat() + 'Z',
            expected['end_date'] = None
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)
            self.assertFalse(rv.json['available'])

            # Ended in the past
            expected['start_date'] = (now - datetime.timedelta(days=14)).isoformat() + 'Z',
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

    def test_delete_course(self):
        course_uuid = self.data.get_course().uuid
        url = '/api/courses/' + course_uuid

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        student = self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.delete(url)
                self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.delete('/api/courses/999')
            self.assert404(rv)

            # test deletion by authorized insturctor
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(course_uuid, rv.json['id'])

            # test course is deleted
            rv = self.client.delete(url)
            self.assert404(rv)

        course2 = self.data.create_course()
        url = '/api/courses/' + course2.uuid

        with self.login('root'):
            # test deletion by system admin
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(course2.uuid, rv.json['id'])

            # test course is deleted
            rv = self.client.delete(url)
            self.assert404(rv)


    def test_duplicate_course_simple(self):
        url = '/api/courses/' + self.data.get_course().uuid + '/duplicate'
        expected = {
            'name': 'duplicate course',
            'year': 2015,
            'term': 'Winter',
            'sandbox': False,
            'start_date': datetime.datetime.utcnow().isoformat() + 'Z',
            'end_date': None
        }
        # test login required
        rv = self.client.post(url, content_type='application/json')
        self.assert401(rv)

        # test student
        student = self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert403(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(expected), content_type='application/json')
            self.assert404(rv)

            # test year missing
            invalid_expected = expected.copy()
            invalid_expected['year'] = None
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert404(rv)

            # test term missing
            invalid_expected = expected.copy()
            invalid_expected['term'] = None
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert404(rv)

            # course start date missing
            invalid_expected = expected.copy()
            invalid_expected['start_date'] = None
            rv = self.client.post('/api/courses/999/duplicate', data=json.dumps(invalid_expected), content_type='application/json')
            self.assert404(rv)

            # test authorized user
            original_course = self.data.get_course()
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)

            # verify course duplicated correctly
            self.assertNotEqual(original_course.uuid, rv.json['id'])
            self.assertEqual(expected['name'], rv.json['name'])
            self.assertEqual(expected['year'], rv.json['year'])
            self.assertEqual(expected['term'], rv.json['term'])
            self.assertEqual(expected['sandbox'], rv.json['sandbox'])
            self.assertEqual(expected['start_date'].replace('Z', ''), rv.json['start_date'].replace('+00:00', ''))
            self.assertEqual(expected['end_date'], rv.json['end_date'])

            # verify instructor added to duplicate course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_uuid=rv.json['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

class CoursesDuplicateComplexAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(CoursesDuplicateComplexAPITests, self).setUp()
        self.data = ComparisonTestData()
        self.course = self.data.get_course()

        # add start_date
        self.course.start_date = datetime.datetime.utcnow()
        self.course.end_date = datetime.datetime.utcnow() + datetime.timedelta(days=90)

        index = 0
        self.assertGreaterEqual(self.course.assignments.count(), 4) # make sure we have enough assignments to play with
        for assignment in self.course.assignments:
            assignment.answer_start = self.course.start_date + datetime.timedelta(days=index)
            assignment.answer_end = self.course.start_date + datetime.timedelta(days=index+7)
            if assignment.compare_start != None:
                assignment.compare_start = self.course.start_date + datetime.timedelta(days=index+14)
            if assignment.compare_end != None:
                assignment.compare_end = self.course.start_date + datetime.timedelta(days=index+21)
            # modify some assignments with self-evaluation
            if index % 2 == 0:
                assignment.enable_self_evaluation = True
            else:
                assignment.enable_self_evaluation = False
            if index % 4 == 0:
                assignment.self_eval_start = assignment.answer_end + datetime.timedelta(days=1)
                assignment.self_eval_end = assignment.self_eval_start + datetime.timedelta(days=1)
                assignment.self_eval_instructions = ''.join([choice(ascii_letters) for i in range(10)])
            else:
                assignment.self_eval_start = None
                assignment.self_eval_end = None
                assignment.self_eval_instructions = None
            index+=1
        db.session.commit()

        self.url = '/api/courses/' + self.course.uuid + '/duplicate'

        self.date_delta = datetime.timedelta(days=180)
        self.expected = {
            'name': 'duplicate course',
            'year': 2015,
            'term': 'Winter',
            'sandbox': False,
            'start_date': (self.course.start_date + self.date_delta).isoformat() + 'Z',
            'end_date': (self.course.end_date + self.date_delta).isoformat() + 'Z',
            'assignments': []
        }

        for assignment in self.course.assignments:
            if not assignment.active:
                continue

            assignment_data = {
                'id': assignment.uuid,
                'name': assignment.name,
                'answer_start': (assignment.answer_start + self.date_delta).isoformat() + 'Z',
                'answer_end': (assignment.answer_end + self.date_delta).isoformat() + 'Z',
                'enable_self_evaluation': assignment.enable_self_evaluation,
                'self_eval_start': (assignment.self_eval_start + self.date_delta).isoformat() + 'Z' if assignment.self_eval_start else assignment.self_eval_start,
                'self_eval_end': (assignment.self_eval_end + self.date_delta).isoformat() + 'Z' if assignment.self_eval_end else assignment.self_eval_end,
                'self_eval_instructions': assignment.self_eval_instructions,
            }

            if assignment.compare_start != None:
                assignment_data['compare_start'] = (assignment.compare_start + self.date_delta).isoformat() + 'Z'

            if assignment.compare_end != None:
                assignment_data['compare_end'] = (assignment.compare_end + self.date_delta).isoformat() + 'Z'

            self.expected['assignments'].append(assignment_data)

        now = datetime.datetime.utcnow()
        self.valid_course = self.data.create_course()
        self.data.enrol_instructor(self.data.get_authorized_instructor(), self.valid_course)
        self.valid_assignment = self.data.create_assignment_in_answer_period(self.valid_course, self.data.get_authorized_instructor())

        self.valid_start_date = now.isoformat() + 'Z'
        self.valid_end_date = (now + datetime.timedelta(days=120)).isoformat() + 'Z'

        self.invalid_end_date = (now - datetime.timedelta(days=1)).isoformat() + 'Z'

        self.valid_answer_start = now.isoformat() + 'Z'
        self.valid_answer_end = (now + datetime.timedelta(days=90)).isoformat() + 'Z'

        self.invalid_answer_start = (now - datetime.timedelta(days=1)).isoformat() + 'Z'
        self.invalid_answer_end = (now - datetime.timedelta(days=1)).isoformat() + 'Z'
        self.invalid_answer_end2 = (now + datetime.timedelta(days=121)).isoformat() + 'Z'

        self.valid_compare_start = now.isoformat() + 'Z'
        self.valid_compare_end = (now + datetime.timedelta(days=90)).isoformat() + 'Z'

        self.invalid_compare_start = (now - datetime.timedelta(days=1)).isoformat() + 'Z'
        self.invalid_compare_end = (now - datetime.timedelta(days=1)).isoformat() + 'Z'
        self.invalid_compare_end2 = (now + datetime.timedelta(days=121)).isoformat() + 'Z'

        self.valid_self_eval_start = (now + datetime.timedelta(days=92)).isoformat() + 'Z'
        self.valid_self_eval_end = (now + datetime.timedelta(days=120)).isoformat() + 'Z'

        self.invalid_self_eval_start = (now - datetime.timedelta(seconds=1)).isoformat() + 'Z' # = compare_start
        self.invalid_self_eval_start2 = (now + datetime.timedelta(days=90)).isoformat() + 'Z' # = answer_end
        self.invalid_self_eval_end = (now + datetime.timedelta(days=91)).isoformat() + 'Z'   # < self_eval_start
        self.invalid_self_eval_end2 = (now + datetime.timedelta(days=121)).isoformat() + 'Z'  # > course_end

        self.validation_url = '/api/courses/' + self.valid_course.uuid + '/duplicate'
        self.validate_expected_assignment = {
            'id': self.valid_assignment.uuid,
            'name': self.valid_assignment.name,
            'answer_start': self.valid_answer_start,
            'answer_end': self.valid_answer_end,
            'compare_start': self.valid_compare_start,
            'compare_end': self.valid_compare_end
        }
        self.validate_expected_course = {
            'name': 'duplicate validation course',
            'year': 2015,
            'term': 'Winter',
            'sandbox': False,
            'start_date': self.valid_start_date,
            'end_date': self.valid_end_date,
            'assignments': [self.validate_expected_assignment]
        }

    def test_duplicate_course_complex(self):
        original_course = self.data.get_course()

        # test authorized user
        with self.login(self.data.get_authorized_instructor().username):
            # test valid expected
            rv = self.client.post(self.validation_url, data=json.dumps(self.validate_expected_course), content_type='application/json')
            self.assert200(rv)

            # test invalid course start/end dates
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['end_date'] = self.invalid_end_date
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Course end time must be after course start time.")

            # test invalid assignment answer start
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['answer_start'] = None
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No answer period start time provided for assignment "+self.valid_assignment.name+".")

            # test invalid assignment answer end
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['answer_end'] = None
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No answer period end time provided for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['answer_end'] = self.invalid_answer_end
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Answer period end time must be after the answer start time for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['answer_end'] = self.invalid_answer_end2
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Answer period end time must be before the course end time for assignment "+self.valid_assignment.name+".")

            # test invalid assignment compare start
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['compare_start'] = None
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No compare period start time provided for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['compare_start'] = self.invalid_compare_start
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Compare period start time must be after the answer start time for assignment "+self.valid_assignment.name+".")

            # test invalid assignment compare end
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['compare_end'] = None
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No compare period end time provided for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['compare_end'] = self.invalid_compare_end
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Compare period end time must be after the compare start time for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['compare_end'] = self.invalid_compare_end2
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Compare period end time must be before the course end time for assignment "+self.valid_assignment.name+".")

            # test invalid assignment self-eval start
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['self_eval_start'] = None
            invalid_expected['assignments'][0]['self_eval_end'] = self.valid_self_eval_end
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No self-evaluation start time provided for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['self_eval_start'] = self.invalid_self_eval_start
            invalid_expected['assignments'][0]['self_eval_end'] = self.valid_self_eval_end
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Self-evaluation start time must be after the compare start time for assignment "+self.valid_assignment.name+".")

            # invalid_expected = self.validate_expected_course.copy()
            # invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            # invalid_expected['assignments'][0]['compare_start'] = None
            # invalid_expected['assignments'][0]['compare_end'] = None
            # invalid_expected['assignments'][0]['self_eval_start'] = self.invalid_self_eval_start2
            # invalid_expected['assignments'][0]['self_eval_end'] = self.valid_self_eval_end
            # rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            # self.assert400(rv)
            # self.assertEqual(rv.json["title"], "Course Not Saved")
            # self.assertEqual(rv.json["message"], "Self-evaluation start time must be after the answer end time for assignment "+self.valid_assignment.name+".")

            # test invalid assignment self-eval end
            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['self_eval_start'] = self.valid_self_eval_start
            invalid_expected['assignments'][0]['self_eval_end'] = None
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "No self-evaluation end time provided for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['self_eval_start'] = self.valid_self_eval_start
            invalid_expected['assignments'][0]['self_eval_end'] = self.invalid_self_eval_end
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Self-evaluation end time must be after the self-evaluation start time for assignment "+self.valid_assignment.name+".")

            invalid_expected = self.validate_expected_course.copy()
            invalid_expected['assignments'][0] = self.validate_expected_assignment.copy()
            invalid_expected['assignments'][0]['self_eval_start'] = self.valid_self_eval_start
            invalid_expected['assignments'][0]['self_eval_end'] = self.invalid_self_eval_end2
            rv = self.client.post(self.validation_url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json["title"], "Course Not Saved")
            self.assertEqual(rv.json["message"], "Self-evaluation end time must be before the course end time for assignment "+self.valid_assignment.name+".")

            # test deep copy assignments
            rv = self.client.post(self.url, data=json.dumps(self.expected), content_type='application/json')
            self.assert200(rv)

            duplicate_course = Course.query.filter_by(uuid=rv.json['id']).first()
            self.assertIsNotNone(duplicate_course)

            # verify course duplicated correctly
            self.assertNotEqual(original_course.id, duplicate_course.id)
            self.assertNotEqual(original_course.uuid, duplicate_course.uuid)
            self.assertEqual(self.expected['name'], duplicate_course.name)
            self.assertEqual(self.expected['year'], duplicate_course.year)
            self.assertEqual(self.expected['term'], duplicate_course.term)
            self.assertEqual(self.expected['sandbox'], duplicate_course.sandbox)
            self.assertEqual(self.expected['start_date'].replace('Z', ''), rv.json['start_date'].replace('+00:00', ''))
            self.assertEqual(self.expected['end_date'].replace('Z', ''), rv.json['end_date'].replace('+00:00', ''))

            # verify instructor added to duplicate course
            user_course = UserCourse.query \
                .filter_by(
                    user_id=self.data.get_authorized_instructor().id,
                    course_uuid=rv.json['id']
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

            original_assignments = original_course.assignments.all()
            duplicate_assignments = duplicate_course.assignments.all()

            self.assertEqual(len(original_assignments), 5)
            self.assertEqual(len(original_assignments), len(duplicate_assignments))

            for index, original_assignment in enumerate(original_assignments):
                duplicate_assignment = duplicate_assignments[index]

                self.assertNotEqual(original_assignment.id, duplicate_assignment.id)
                self.assertNotEqual(original_assignment.uuid, duplicate_assignment.uuid)
                self.assertEqual(duplicate_course.id, duplicate_assignment.course_id)
                self.assertEqual(original_assignment.name, duplicate_assignment.name)
                self.assertEqual(original_assignment.description, duplicate_assignment.description)
                self.assertEqual(original_assignment.number_of_comparisons, duplicate_assignment.number_of_comparisons)
                self.assertEqual(original_assignment.students_can_reply, duplicate_assignment.students_can_reply)
                self.assertEqual(original_assignment.enable_self_evaluation, duplicate_assignment.enable_self_evaluation)
                self.assertEqual(original_assignment.pairing_algorithm, duplicate_assignment.pairing_algorithm)
                self.assertEqual(original_assignment.answer_grade_weight, duplicate_assignment.answer_grade_weight)
                self.assertEqual(original_assignment.comparison_grade_weight, duplicate_assignment.comparison_grade_weight)
                self.assertEqual(original_assignment.self_evaluation_grade_weight, duplicate_assignment.self_evaluation_grade_weight)
                self.assertEqual(original_assignment.enable_group_answers, duplicate_assignment.enable_group_answers)
                self.assertEqual(original_assignment.scoring_algorithm, duplicate_assignment.scoring_algorithm)
                self.assertEqual(original_assignment.peer_feedback_prompt, duplicate_assignment.peer_feedback_prompt)
                self.assertEqual(original_assignment.educators_can_compare, duplicate_assignment.educators_can_compare)
                self.assertEqual(original_assignment.rank_display_limit, duplicate_assignment.rank_display_limit)

                self.assertEqual(original_assignment.answer_start,
                    (duplicate_assignment.answer_start - self.date_delta))
                self.assertEqual(original_assignment.answer_end,
                    (duplicate_assignment.answer_end - self.date_delta))

                if original_assignment.compare_start != None:
                    self.assertEqual(original_assignment.compare_start,
                        (duplicate_assignment.compare_start - self.date_delta))
                else:
                    self.assertIsNone(duplicate_assignment.compare_start)

                if original_assignment.compare_end != None:
                    self.assertEqual(original_assignment.compare_end,
                        (duplicate_assignment.compare_end - self.date_delta))
                else:
                    self.assertIsNone(duplicate_assignment.compare_end)

                self.assertEqual(len(original_assignment.criteria), 1)
                self.assertEqual(len(original_assignment.criteria), len(duplicate_assignment.criteria))

                for index, original_criteria in enumerate(original_assignment.criteria):
                    duplicate_criteria = duplicate_assignment.criteria[index]
                    self.assertEqual(original_criteria.id, duplicate_criteria.id)

                self.assertEqual(original_assignment.enable_self_evaluation,
                    duplicate_assignment.enable_self_evaluation)
                if original_assignment.self_eval_start:
                    self.assertEqual(original_assignment.self_eval_start,
                        (duplicate_assignment.self_eval_start - self.date_delta))
                else:
                    self.assertIsNone(duplicate_assignment.self_eval_start)
                if original_assignment.self_eval_end:
                    self.assertEqual(original_assignment.self_eval_end,
                        (duplicate_assignment.self_eval_end - self.date_delta))
                else:
                    self.assertIsNone(duplicate_assignment.self_eval_end)
                self.assertEqual(original_assignment.self_eval_instructions,
                    duplicate_assignment.self_eval_instructions)

                original_comparison_examples = original_assignment.comparison_examples.all()
                duplicate_comparison_examples = duplicate_assignment.comparison_examples.all()

                if original_assignment.id in [1,2,3,4]:
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
                    self.assertEqual(original_answer1.practice, duplicate_answer1.practice)
                    self.assertEqual(original_answer1.active, duplicate_answer1.active)
                    self.assertEqual(original_answer1.draft, duplicate_answer1.draft)

                    original_answer2 = original_comparison_example.answer2
                    duplicate_answer2 = duplicate_comparison_example.answer2

                    self.assertNotEqual(original_answer2.id, duplicate_answer2.id)
                    self.assertEqual(duplicate_assignment.id, duplicate_answer2.assignment_id)
                    self.assertEqual(original_answer2.content, duplicate_answer2.content)
                    self.assertEqual(original_answer2.practice, original_answer2.practice)
                    self.assertEqual(original_answer2.active, original_answer2.active)
                    self.assertEqual(original_answer2.draft, original_answer2.draft)


class CourseDemoAPITests(ComPAIRAPIDemoTestCase):
    def setUp(self):
        super(CourseDemoAPITests, self).setUp()

    def test_delete_demo_course(self):
        course = Course.query.get(1)
        url = '/api/courses/' + course.uuid

        with self.login('root'):
            # test deletion by authorized instructor fails
            self.app.config['DEMO_INSTALLATION'] = True
            rv = self.client.delete(url)
            self.assert400(rv)

            # test deletion by authorized instructor success
            self.app.config['DEMO_INSTALLATION'] = False
            rv = self.client.delete(url)
            self.assert200(rv)

    def test_edit_demo_course(self):
        course = Course.query.get(1)
        url = '/api/courses/' + course.uuid

        expected = {
            'id': course.uuid,
            'name': 'ExpectedCourse',
            'year': 2015,
            'term': 'Winter',
            'sandbox': False,
            'start_date': datetime.datetime.utcnow().isoformat() + 'Z',
            'end_date': None,
            'description': 'Test Description'
        }

        with self.login('root'):
            # test deletion fails
            self.app.config['DEMO_INSTALLATION'] = True
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert400(rv)

            # test deletion success
            self.app.config['DEMO_INSTALLATION'] = False
            rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
            self.assert200(rv)


class CoursesLTIAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(CoursesLTIAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.lti_data = LTITestData()

    def test_delete_course(self):
        # test unlinking of lti contexts when course deleted
        course = self.data.get_course()
        url = '/api/courses/' + course.uuid

        lti_consumer = self.lti_data.get_consumer()
        lti_context1 = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id
        )
        lti_context2 = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id
        )
        lti_resource_link1 = self.lti_data.create_resource_link(
            lti_consumer,
            lti_context=lti_context2,
            compair_assignment=self.data.assignments[0]
        )
        lti_resource_link2 = self.lti_data.create_resource_link(
            lti_consumer,
            lti_context=lti_context2,
            compair_assignment=self.data.assignments[1]
        )

        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(course.uuid, rv.json['id'])

            self.assertIsNone(lti_context1.compair_course_id)
            self.assertIsNone(lti_context2.compair_course_id)
            self.assertIsNone(lti_resource_link1.compair_assignment_id)
            self.assertIsNone(lti_resource_link2.compair_assignment_id)