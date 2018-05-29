# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from data.fixtures.test_data import TestFixture, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase

from compair.models import UserCourse, CourseRole, ThirdPartyType


class CourseGroupsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(CourseGroupsAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=3)

    def test_get_active_groups(self):
        url = '/api/courses/'+self.fixtures.course.uuid+'/groups'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.instructor.username):
            invalid_url = '/api/courses/999/groups'
            rv = self.client.get(invalid_url)
            self.assert404(rv)

            # test successful query
            rv = self.client.get(url)
            self.assert200(rv)
            actual = rv.json['objects']
            self.assertEqual(len(actual), 3)
            self.assertEqual(actual[0], self.fixtures.groups[0])

        # test TA
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(url)
            self.assert200(rv)
            actual = rv.json['objects']
            self.assertEqual(len(actual), 3)
            self.assertEqual(actual[0], self.fixtures.groups[0])

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.get(url)
                self.assert403(rv)

    def test_get_group_members(self):
        course = self.fixtures.course
        group_name = self.fixtures.groups[0]
        url = '/api/courses/'+course.uuid+'/groups/'+group_name

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get('/api/courses/999/groups/'+group_name)
            self.assert404(rv)

            # test invalid group id
            rv = self.client.get('/api/courses/'+course.uuid+'/groups/asdasdasdasd')
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(10, len(rv.json['objects']))
            self.assertEqual(self.fixtures.students[0].uuid, rv.json['objects'][0]['id'])

        # test authorized teaching assistant
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(10, len(rv.json['objects']))
            self.assertEqual(self.fixtures.students[0].uuid, rv.json['objects'][0]['id'])

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.get(url)
                self.assert403(rv)

    def test_group_enrolment(self):
        # frequently used objects
        course = self.fixtures.course
        group_name = self.fixtures.groups[0]

        # test login required
        url = self._create_group_user_url(course, self.fixtures.students[0], group_name)
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            url = self._create_group_user_url(course, self.fixtures.students[0], group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test user that is already in group
            url = self._create_group_user_url(course, self.fixtures.students[0], group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['group_name'], group_name)

            # test user that has never been in the group
            url = self._create_group_user_url(course, self.fixtures.instructor, group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['group_name'], group_name)

            # test user that has left the group
            url = self._create_group_user_url(course, self.fixtures.ta, group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['group_name'], group_name)

            # test user that is not enroled in the course anymore - eg. DROPPED
            url = self._create_group_user_url(course, self.fixtures.dropped_instructor, group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test user that has never been in the course
            url = self._create_group_user_url(course, self.fixtures.unauthorized_student, group_name)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test invalid course id
            url = '/api/courses/999/users/'+self.fixtures.students[0].uuid+'/groups/'+group_name
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test invalid user id
            url = '/api/courses/'+course.uuid+'/users/999/groups/'+group_name
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                url = self._create_group_user_url(course, self.fixtures.instructor, group_name)
                rv = self.client.post(url, data={}, content_type='application/json')
                self.assert403(rv)

    def test_group_unenrolment(self):
        course = self.fixtures.course

        # test login required
        url = self._create_group_user_url(course, self.fixtures.students[0])
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorzied user
        with self.login(self.fixtures.unauthorized_instructor.username):
            url = self._create_group_user_url(course, self.fixtures.students[0])
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test user in course
            url = self._create_group_user_url(course, self.fixtures.students[0])
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(rv.json['user_id'], self.fixtures.students[0].uuid)
            self.assertEqual(rv.json['course_id'], course.uuid)

            # test user not in course
            url = self._create_group_user_url(course, self.fixtures.unauthorized_student)
            rv = self.client.delete(url)
            self.assert404(rv)

            # test invalid course id
            url = '/api/courses/999/users/'+self.fixtures.students[0].uuid+'/groups'
            rv = self.client.delete(url)
            self.assert404(rv)

            # test invalid user id
            url = '/api/courses/'+course.uuid+'/users/999/groups'
            rv = self.client.delete(url)
            self.assert404(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                url = self._create_group_user_url(course, self.fixtures.students[0])
                rv = self.client.delete(url)
                self.assert403(rv)

    def test_group_multiple_enrolment(self):
        # frequently used objects
        course = self.fixtures.course
        group_name = self.fixtures.groups[0]
        group_name_2 = self.fixtures.groups[1]
        student_ids = [self.fixtures.students[0].uuid, self.fixtures.students[1].uuid]
        url = self._create_group_users_url(course, group_name)

        params = { 'ids': student_ids }

        # test login required
        rv = self.client.post(url,
            data=json.dumps(params),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/users/groups/'+group_name,
                data=json.dumps(params),
                content_type='application/json')
            self.assert404(rv)

            # test missing ids
            rv = self.client.post(url,
                data=json.dumps({'ids': []}),
                content_type='application/json')
            self.assert400(rv)

            # test invalid ids
            rv = self.client.post(url,
                data=json.dumps({'ids': [self.fixtures.unauthorized_student.uuid]}),
                content_type='application/json')
            self.assert400(rv)

            # test enrol users into group
            rv = self.client.post(url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['group_name'], group_name)

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_name, group_name)

            # test enrol users into another group
            url = self._create_group_users_url(course, group_name_2)
            rv = self.client.post(url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['group_name'], group_name_2)

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_name, group_name_2)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url,
                    data=json.dumps(params),
                    content_type='application/json')
                self.assert403(rv)

    def test_group_multiple_unenrolment(self):
        course = self.fixtures.course
        url = self._create_group_users_url(course)

        student_ids = [self.fixtures.students[0].uuid, self.fixtures.students[1].uuid]
        params = { 'ids': student_ids }

        # test login required
        rv = self.client.post(url,
            data=json.dumps(params),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorzied user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/users/groups',
                data=json.dumps(params),
                content_type='application/json')
            self.assert404(rv)

            # test missing ids
            rv = self.client.post(url,
                data=json.dumps({ 'ids': [] }),
                content_type='application/json')
            self.assert400(rv)

            # test invalid ids
            rv = self.client.post(url,
                data=json.dumps({ 'ids': [self.fixtures.unauthorized_student.uuid] }),
                content_type='application/json')
            self.assert400(rv)

            # test users in course
            rv = self.client.post(url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['course_id'], course.uuid)

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_name, None)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url,
                    data=json.dumps(params),
                    content_type='application/json')
                self.assert403(rv)

    def _create_group_user_url(self, course, user, group_name=None):
        url = '/api/courses/'+course.uuid+'/users/'+user.uuid+'/groups'
        if group_name:
            url = url+'/'+group_name
        return url

    def _create_group_users_url(self, course, group_name=None):
        url = '/api/courses/'+course.uuid+'/users/groups'
        if group_name:
            url = url+'/'+group_name
        return url
