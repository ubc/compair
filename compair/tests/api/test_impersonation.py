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
        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
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

    # def test_cannot_logout_during_impersonation(self):
    #     with self.login(self.instructor_main_course.username):
    #         self.assert200(self._start_impersonation(self.student_main_course))
    #         self._verify_impersonation(original=self.instructor_main_course, pretending=self.student_main_course)
    #
    #         # explicit logout
    #         self.assert403(self.logout())
    #         self._verify_impersonation(original=self.instructor_main_course, pretending=self.student_main_course)
    #         self.assert200(self._end_impersonation())
    #         self.assert200(self.logout())

    def test_impersonation_access_assignment(self):
        assignment_url = self.assignment_base_url + '/' + self.assignment_main_course.uuid
        draft_answer = {'draft': True, 'content': 'This is a draft answer'}

        # during impersonation, instructor can read but can't create a draft for student
        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            rv = self.client.get(assignment_url + '/answers/user?draft=true&unsaved=true')
            self.assert200(rv)
            self.assertFalse(rv.json.get('objects'))    # expect empty list
            # try to create draft
            rv = self.client.post(assignment_url + '/answers',
                data=json.dumps(draft_answer),
                content_type='application/json')
            self.assert403(rv)
            rv = self.client.delete(self.impersonate_base_url)
            self.assert200(rv)

        # student darfts an answer.
        # instructor should be able to see it during impersonation, but can't update it
        with self.login(self.student_main_course.username):
            rv = self.client.post(assignment_url + '/answers',
                data=json.dumps(draft_answer),
                content_type='application/json')
            self.assert200(rv)
            draft_answer['id'] = rv.json.get('id')
        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            rv = self.client.get(assignment_url + '/answers/user?draft=true')
            self.assert200(rv)
            self.assertEquals(rv.json.get('objects')[0].get('id', None), draft_answer['id'])
            self.assertEquals(rv.json.get('objects')[0].get('content', None), draft_answer['content'])
            # attempt update
            instructor_update_answer = draft_answer.copy()
            instructor_update_answer['content'] = "shouldn't see instructor's udpate"
            rv = self.client.post(assignment_url + '/answers' + '/' + draft_answer['id'],
                data=json.dumps(instructor_update_answer),
                content_type='application/json')
            self.assert403(rv)
            self.assert200(self._end_impersonation())
        with self.login(self.student_main_course.username):
            rv = self.client.get(assignment_url + '/answers/user?draft=true')
            self.assert200(rv)
            self.assertEquals(rv.json.get('objects')[0].get('id', None), draft_answer['id'])
            # verify content is still the original draft
            self.assertEquals(rv.json.get('objects')[0].get('content', None), draft_answer['content'])

    def test_impersonation_cannot_access_courses_of_other_instructors(self):
        # enrol main course student to second course too
        self.data.enrol_student(self.student_main_course, self.data.secondary_course)

        with self.login(self.student_main_course.username):
            # student can access it
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert200(rv)
        with self.login(self.instructor_main_course.username):
            # but instructor of main course can't...
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert403(rv)
            # ... even during impersonation
            self.assert200(self._start_impersonation(self.student_main_course))
            self._verify_impersonation(pretending=self.student_main_course)
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert403(rv)

    def test_impersonation_can_access_courses_if_added_as_joint_instructor(self):
        # enrol main course instructor and student to second course too
        self.data.enrol_student(self.student_main_course, self.data.secondary_course)
        self.data.enrol_instructor(self.instructor_main_course, self.data.secondary_course)

        with self.login(self.student_main_course.username):
            # student can access it
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert200(rv)
        with self.login(self.instructor_main_course.username):
            # so as the instructor...
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert200(rv)
            # ... also during impersonation
            self.assert200(self._start_impersonation(self.student_main_course))
            self._verify_impersonation(pretending=self.student_main_course)
            rv = self.client.get(self.course_base_url + '/' + self.data.secondary_course.uuid + '/assignments')
            self.assert200(rv)

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

    def test_impersonation_access_student_profile(self):
        with self.login(self.instructor_main_course.username):
            self.assert200(self._start_impersonation(self.student_main_course))
            rv = self.client.get(self.profile_base_url + '/' + self.student_main_course.uuid)
            self.assert200(rv)
            # instructor should see display name etc, but not email
            student_profile = rv.json
            self.assertEquals(student_profile.get('id'), self.student_main_course.uuid)
            self.assertEquals(student_profile.get('displayname'), self.student_main_course.displayname)
            self.assertEquals(student_profile.get('firstname'), self.student_main_course.firstname)
            self.assertEquals(student_profile.get('lastname'), self.student_main_course.lastname)
            self.assertFalse(student_profile.get('email', None))
            # instructor can't update student's profile while impersonating
            rv = self.client.post(self.profile_base_url + '/' + self.student_main_course.uuid,
                data = json.dumps(student_profile),
                content_type='application/json')
            self.assert403(rv)