# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from data.fixtures import DefaultFixture
from data.fixtures.test_data import SimpleAssignmentTestData
from compair.tests.test_compair import ComPAIRAPITestCase

class ImpersonationAPITests(ComPAIRAPITestCase):

    def setUp(self):
        super(ImpersonationAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.course_base_url = '/api/courses'
        self.assignment_base_url = self.course_base_url + '/' + self.data.get_course().uuid + '/assignments'
        self.impersonate_base_url = '/api/impersonate'
        self.profile_base_url = '/api/users'
        self.session_base_url = '/api/session'

        self.assignment_main_course = self.data.get_assignments()[0]
        self.student_main_course = self.data.get_authorized_student();
        self.student_second_course = self.data.get_unauthorized_student();
        self.instructor_main_course = self.data.get_authorized_instructor();
        self.instructor_second_course = self.data.get_unauthorized_instructor();

    def _start_impersonation(self, pretending):
        return self.client.post(self.impersonate_base_url + '/' + pretending.uuid)

    def _end_impersonation(self):
        return self.client.delete(self.impersonate_base_url)

    def _verify_impersonation(self, original=None, pretending=None):
        rv = self.client.get(self.impersonate_base_url)
        self.assert200(rv)
        self.assertEquals(rv.json.get('impersonating'), True)
        if original:
            self.assertEquals(rv.json.get('original_user').get('id'), original.uuid)
        if pretending:
            rv = self.client.get(self.session_base_url)
            self.assert200(rv)
            self.assertEqual(rv.json.get('id'), pretending.uuid)

    def _is_not_impersonating(self):
        rv = self.client.get(self.impersonate_base_url)
        self.assert200(rv)
        self.assertEquals(rv.json.get('impersonating'), False)

    def test_impersonation_requires_login(self):
        self.assert401(self._start_impersonation(self.instructor_main_course))
        self.assert401(self._start_impersonation(self.student_main_course))

    def test_student_cannot_impersonate(self):
        with self.login(self.student_main_course.username):
            self.assert403(self._start_impersonation(self.instructor_main_course))
            self.assert403(self._start_impersonation(self.student_second_course))

    def test_instructor_can_impersonate_own_students(self):
        with self.impersonate(self.instructor_main_course, self.student_main_course):
            self._verify_impersonation(original=self.instructor_main_course, pretending=self.student_main_course)

    def test_instructor_cannot_impersonate_student_not_in_his_course(self):
        with self.login(self.instructor_main_course.username):
            self.assert403(self._start_impersonation(self.student_second_course))
        with self.login(self.instructor_second_course.username):
            self.assert403(self._start_impersonation(self.student_main_course))

    def test_instructor_cannot_impersonate_admin(self):
        with self.login(self.instructor_main_course.username):
            self.assert403(self._start_impersonation(DefaultFixture.ROOT_USER))

    def test_admin_can_impersonate_students_but_not_instructors(self):
        with self.login(DefaultFixture.ROOT_USER.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            self.assert403(self._start_impersonation(self.instructor_main_course))

    def test_end_impersonation(self):
        # Impersonation will block non-GET traffic, but should allow end impersonation (a DELETE call)
        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            self._verify_impersonation(original=self.instructor_main_course, pretending=self.student_main_course)

            self.assert200(self._end_impersonation())
            self._is_not_impersonating()

    def test_cannot_logout_during_impersonation(self):
        with self.impersonate(self.instructor_main_course, self.student_main_course):
            # explicit logout should fail
            self.assert403(self.client.delete('/api/logout', follow_redirects=True))
            # still logged in and impersonating
            self._verify_impersonation(original=self.instructor_main_course, pretending=self.student_main_course)

    def test_access_right_after_impersonation(self):
        comparisons_of_main_course_assignment_url = \
            self.assignment_base_url + '/' + self.assignment_main_course.uuid + '/users/comparisons?page=1&perPage=5'

        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            # no access when impersonating as student
            self.assert403(self.client.get(comparisons_of_main_course_assignment_url))
            self._end_impersonation()
            # resume access after impersonation
            self.assert200(self.client.get(comparisons_of_main_course_assignment_url))
