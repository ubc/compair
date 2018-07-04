# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
from datetime import timedelta

from data.fixtures.test_data import TestFixture, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase

from compair.models import UserCourse, CourseRole, ThirdPartyType, Group


class GroupUsersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(GroupUsersAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=3, num_group_assignments=1)

        self.assignment = self.fixtures.assignment
        self.group_assignment = self.fixtures.assignments[1]


        now = datetime.datetime.now()
        self.assignment_dates = [
            # before answer period (no comparison dates)
            (False, now + timedelta(days=2), now + timedelta(days=3), None, None),
            # during answer period (no comparison dates)
            (False, now - timedelta(days=2), now + timedelta(days=3), None, None),
            # during compare period (no comparison dates)
            (True, now - timedelta(days=2), now - timedelta(days=1), None, None),
            # before answer period (with comparison dates)
            (False, now + timedelta(days=2), now + timedelta(days=3), now + timedelta(days=12), now + timedelta(days=13)),
            # during answer period (with comparison dates)
            (False, now - timedelta(days=2), now + timedelta(days=3), now + timedelta(days=12), now + timedelta(days=13)),
            # after answer period (with comparison dates)
            (False, now - timedelta(days=2), now - timedelta(days=1), now + timedelta(days=12), now + timedelta(days=13)),
            # during compare period (with comparison dates)
            (True, now - timedelta(days=12), now - timedelta(days=11), now - timedelta(days=2), now + timedelta(days=3)),
            # after compare period (with comparison dates)
            (True, now - timedelta(days=12), now - timedelta(days=11), now - timedelta(days=5), now - timedelta(days=3))
        ]

    def test_get_group_members(self):
        course = self.fixtures.course
        group = self.fixtures.groups[0]
        url = '/api/courses/'+course.uuid+'/groups/'+group.uuid+'/users'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get('/api/courses/999/groups/'+group.uuid+'/users')
            self.assert404(rv)

            # test invalid group id
            rv = self.client.get('/api/courses/'+course.uuid+'/groups/999/users')
            self.assert404(rv)

            # test authorized instructor
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(10, len(rv.json['objects']))
            members = sorted(
                [uc.user for uc in group.user_courses.all()],
                key=lambda user: (user.lastname, user.firstname)
            )
            for index, user in enumerate(members):
                self.assertEqual(user.uuid, rv.json['objects'][index]['id'])

        # test authorized teaching assistant
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(10, len(rv.json['objects']))
            members = sorted(
                [uc.user for uc in group.user_courses.all()],
                key=lambda user: (user.lastname, user.firstname)
            )
            for index, user in enumerate(members):
                self.assertEqual(user.uuid, rv.json['objects'][index]['id'])

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.get(url)
                self.assert403(rv)

    def test_get_current_user_group(self):
        course = self.fixtures.course
        url = '/api/courses/'+course.uuid+'/groups/user'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.get('/api/courses/999/groups/user')
            self.assert404(rv)

            # test authorized instructor
            for group in [None, self.fixtures.groups[0]]:
                self.fixtures.change_user_group(course, self.fixtures.instructor, group)
                rv = self.client.get(url)
                self.assert200(rv)

                if group == None:
                    self.assertIsNone(rv.json)
                else:
                    self.assertEquals(rv.json['id'], group.uuid)
                    self.assertEquals(rv.json['name'], group.name)


        # test authorized teaching assistant
        with self.login(self.fixtures.ta.username):
            for group in [None, self.fixtures.groups[0]]:
                self.fixtures.change_user_group(course, self.fixtures.ta, group)
                rv = self.client.get(url)
                self.assert200(rv)

                if group == None:
                    self.assertIsNone(rv.json)
                else:
                    self.assertEquals(rv.json['id'], group.uuid)
                    self.assertEquals(rv.json['name'], group.name)

        # test root admin (not enrolled in course)
        with self.login(self.fixtures.root_user.username):
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertIsNone(rv.json)

            # test root admin (enrolled in course)
            self.fixtures.enrol_user(self.fixtures.root_user, course, CourseRole.student, None)
            for group in [None, self.fixtures.groups[0]]:
                self.fixtures.change_user_group(course, self.fixtures.root_user, group)
                rv = self.client.get(url)
                self.assert200(rv)

                if group == None:
                    self.assertIsNone(rv.json)
                else:
                    self.assertEquals(rv.json['id'], group.uuid)
                    self.assertEquals(rv.json['name'], group.name)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                for group in [None, self.fixtures.groups[0]]:
                    self.fixtures.change_user_group(course, student, group)
                    rv = self.client.get(url)
                    self.assert200(rv)

                    if group == None:
                        self.assertIsNone(rv.json)
                    else:
                        self.assertEquals(rv.json['id'], group.uuid)
                        self.assertEquals(rv.json['name'], group.name)


    def test_add_group_member(self):
        # frequently used objects
        course = self.fixtures.course
        group = self.fixtures.groups[0]

        # test login required
        url = self._add_group_user_url(course, group, self.fixtures.students[0])
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            url = self._add_group_user_url(course, group, self.fixtures.students[0])
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                url = self._add_group_user_url(course, group, self.fixtures.instructor)
                rv = self.client.post(url, data={}, content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            url = '/api/courses/999/groups/'+group.uuid+'/users/'+self.fixtures.students[0].uuid
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test invalid user id
            url = '/api/courses/'+course.uuid+'/groups/999/users/'+self.fixtures.students[0].uuid
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test invalid user id
            url = '/api/courses/'+course.uuid+'/groups/'+group.uuid+'/users/999'
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test user that is already in group
            url = self._add_group_user_url(course, group, self.fixtures.students[0])
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['id'], group.uuid)

            # test user that has never been in the group
            url = self._add_group_user_url(course, group, self.fixtures.instructor)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['id'], group.uuid)

            # test user that has left the group
            url = self._add_group_user_url(course, group, self.fixtures.ta)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['id'], group.uuid)

            # test user that is not enrolled in the course anymore - eg. DROPPED
            url = self._add_group_user_url(course, group, self.fixtures.dropped_instructor)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            # test user that has never been in the course
            url = self._add_group_user_url(course, group, self.fixtures.unauthorized_student)
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert404(rv)

            for (groups_locked, answer_start, answer_end, compare_start, compare_end) in self.assignment_dates:
                self.group_assignment.answer_end = answer_end
                self.group_assignment.compare_start = compare_start
                self.group_assignment.compare_end = compare_end

                self.fixtures.add_students(2)
                grouped_student = self.fixtures.students[-2]
                self.fixtures.change_user_group(self.fixtures.course, grouped_student, self.fixtures.groups[0])
                ungrouped_student = self.fixtures.students[-1]
                group = self.fixtures.groups[1]

                url = self._add_group_user_url(course, group, grouped_student)
                if groups_locked:
                    # grouped_student should not be able to change groups
                    rv = self.client.post(url, data={}, content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual(rv.json['title'], "Group Not Saved")
                    self.assertEqual(rv.json['message'], "The course groups are locked. This user is already assigned to a different group.")
                else:
                    # grouped_student should be able to change groups
                    rv = self.client.post(url, data={}, content_type='application/json')
                    self.assert200(rv)

                # regardless ungrouped_student should be able to change groups
                url = self._add_group_user_url(course, group, ungrouped_student)
                rv = self.client.post(url, data={}, content_type='application/json')
                self.assert200(rv)

    def test_remove_group_member(self):
        course = self.fixtures.course

        # test login required
        url = self._remove_group_user_url(course, self.fixtures.students[0])
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorzied user
        with self.login(self.fixtures.unauthorized_instructor.username):
            url = self._remove_group_user_url(course, self.fixtures.students[0])
            rv = self.client.delete(url)
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                url = self._remove_group_user_url(course, self.fixtures.students[0])
                rv = self.client.delete(url)
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            url = '/api/courses/999/groups/users/'+self.fixtures.students[0].uuid
            rv = self.client.delete(url)
            self.assert404(rv)

            # test invalid user id
            url = '/api/courses/'+course.uuid+'/groups/users/999'
            rv = self.client.delete(url)
            self.assert404(rv)

            # test user in course
            url = self._remove_group_user_url(course, self.fixtures.students[0])
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertTrue(rv.json['success'])

            # test user not in course
            url = self._remove_group_user_url(course, self.fixtures.unauthorized_student)
            rv = self.client.delete(url)
            self.assert404(rv)

            for (groups_locked, answer_start, answer_end, compare_start, compare_end) in self.assignment_dates:
                self.group_assignment.answer_end = answer_end
                self.group_assignment.compare_start = compare_start
                self.group_assignment.compare_end = compare_end

                self.fixtures.add_students(2)
                grouped_student = self.fixtures.students[-2]
                self.fixtures.change_user_group(self.fixtures.course, grouped_student, self.fixtures.groups[0])
                ungrouped_student = self.fixtures.students[-1]

                url = self._remove_group_user_url(course, grouped_student)
                if groups_locked:
                    # grouped_student should not be able to be removed from groups
                    rv = self.client.delete(url)
                    self.assert400(rv)
                    self.assertEqual(rv.json['title'], "Group Not Saved")
                    self.assertEqual(rv.json['message'], "The course groups are locked. You may not remove users from the group they are already assigned to.")
                else:
                    # grouped_student should be able to be removed from groups
                    rv = self.client.delete(url)
                    self.assert200(rv)

                # regardless ungrouped_student should be able to be removed from groups
                url = self._remove_group_user_url(course, ungrouped_student)
                rv = self.client.delete(url)
                self.assert200(rv)

    def test_add_multiple_group_member(self):
        # frequently used objects
        course = self.fixtures.course
        group = self.fixtures.groups[0]
        group2 = self.fixtures.groups[1]
        student_ids = [self.fixtures.students[0].uuid, self.fixtures.students[1].uuid]
        url = self._add_group_user_url(course, group)

        params = { 'ids': student_ids }

        # test login required
        rv = self.client.post(url,
            data=json.dumps(params),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/groups/'+group.uuid+'/users', data=json.dumps(params), content_type='application/json')
            self.assert404(rv)

            # test invalid group id
            rv = self.client.post('/api/courses/'+course.uuid+'/groups/999/users',
                data=json.dumps(params), content_type='application/json')
            self.assert404(rv)

            # test missing ids
            rv = self.client.post(url, data=json.dumps({'ids': []}), content_type='application/json')
            self.assert400(rv)

            # test invalid ids
            rv = self.client.post(url, data=json.dumps({'ids': [self.fixtures.unauthorized_student.uuid]}), content_type='application/json')
            self.assert400(rv)

            # test add users into group
            rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['id'], group.uuid)

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_id, group.id)

            # test add users into another group
            url = self._add_group_user_url(course, group2)
            rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['id'], group2.uuid)

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_id, group2.id)


            for (groups_locked, answer_start, answer_end, compare_start, compare_end) in self.assignment_dates:
                self.group_assignment.answer_end = answer_end
                self.group_assignment.compare_start = compare_start
                self.group_assignment.compare_end = compare_end

                self.fixtures.add_students(4)
                grouped_students = [self.fixtures.students[-4], self.fixtures.students[-3]]
                self.fixtures.change_user_group(self.fixtures.course, grouped_students[0], self.fixtures.groups[0])
                self.fixtures.change_user_group(self.fixtures.course, grouped_students[1], self.fixtures.groups[0])

                grouped_student_uuids = [student.uuid for student in grouped_students]
                ungrouped_student_uuids = [self.fixtures.students[-2].uuid, self.fixtures.students[-1].uuid]
                group = self.fixtures.groups[1]

                url = self._add_group_user_url(course, group)
                params = { 'ids': grouped_student_uuids + ungrouped_student_uuids }
                if groups_locked:
                    # grouped_students should not be able to change groups (groups should not change)
                    rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual(rv.json['title'], "Group Not Saved")
                    self.assertEqual(rv.json['message'], "The course groups are locked. One or more users are already assigned to a different group.")

                    for user_course in course.user_courses:
                        if user_course.user_uuid in grouped_student_uuids:
                            self.assertEqual(user_course.group_id, self.fixtures.groups[0].id)
                        if user_course.user_uuid in ungrouped_student_uuids:
                            self.assertEqual(user_course.group_id, None)
                else:
                    # grouped_students should be able to change groups
                    rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                    self.assert200(rv)

                    for user_course in course.user_courses:
                        if user_course.user_uuid in grouped_student_uuids + ungrouped_student_uuids:
                            self.assertEqual(user_course.group_id, group.id)

                # regardless ungrouped_student should be able to change groups
                url = self._add_group_user_url(course, group)
                params = { 'ids': ungrouped_student_uuids }
                rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                self.assert200(rv)


    def test_remove_multiple_group_member(self):
        course = self.fixtures.course
        url = self._remove_group_user_url(course)

        student_ids = [self.fixtures.students[0].uuid, self.fixtures.students[1].uuid]
        params = { 'ids': student_ids }

        # test login required
        rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
        self.assert401(rv)

        # test unauthorzied user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            rv = self.client.post('/api/courses/999/users/groups', data=json.dumps(params), content_type='application/json')
            self.assert404(rv)

            # test missing ids
            rv = self.client.post(url, data=json.dumps({ 'ids': [] }), content_type='application/json')
            self.assert400(rv)

            # test invalid ids
            rv = self.client.post(url, data=json.dumps({ 'ids': [self.fixtures.unauthorized_student.uuid] }), content_type='application/json')
            self.assert400(rv)

            # test users in course
            rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
            self.assert200(rv)
            self.assertTrue(rv.json['success'])

            for user_course in course.user_courses:
                if user_course.user_id in student_ids:
                    self.assertEqual(user_course.group_id, None)

            for (groups_locked, answer_start, answer_end, compare_start, compare_end) in self.assignment_dates:
                self.group_assignment.answer_end = answer_end
                self.group_assignment.compare_start = compare_start
                self.group_assignment.compare_end = compare_end

                self.fixtures.add_students(4)
                grouped_students = [self.fixtures.students[-4], self.fixtures.students[-3]]
                self.fixtures.change_user_group(self.fixtures.course, grouped_students[0], self.fixtures.groups[0])
                self.fixtures.change_user_group(self.fixtures.course, grouped_students[1], self.fixtures.groups[0])

                grouped_student_uuids = [student.uuid for student in grouped_students]
                ungrouped_student_uuids = [self.fixtures.students[-2].uuid, self.fixtures.students[-1].uuid]
                group = self.fixtures.groups[1]

                params = { 'ids': grouped_student_uuids + ungrouped_student_uuids }
                if groups_locked:
                    # grouped_students should not be able to be removed from groups (groups should not change)
                    rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                    self.assert400(rv)
                    self.assertEqual(rv.json['title'], "Group Not Saved")
                    self.assertEqual(rv.json['message'], "The course groups are locked. You may not remove users from the group they are already assigned to.")

                    for user_course in course.user_courses:
                        if user_course.user_uuid in grouped_student_uuids:
                            self.assertEqual(user_course.group_id, self.fixtures.groups[0].id)
                        if user_course.user_uuid in ungrouped_student_uuids:
                            self.assertEqual(user_course.group_id, None)
                else:
                    # grouped_students should be able to be removed from groups
                    rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                    self.assert200(rv)

                    for user_course in course.user_courses:
                        if user_course.user_uuid in grouped_student_uuids + ungrouped_student_uuids:
                            self.assertEqual(user_course.group_id, None)

                # regardless ungrouped_student should be able to be removed from groups
                params = { 'ids': ungrouped_student_uuids }
                rv = self.client.post(url, data=json.dumps(params), content_type='application/json')
                self.assert200(rv)

    def _add_group_user_url(self, course, group, user=None):
        url = '/api/courses/'+course.uuid+'/groups/'+group.uuid+'/users'
        url += '/'+user.uuid if user else ''
        return url


    def _remove_group_user_url(self, course, user=None):
        url = '/api/courses/'+course.uuid+'/groups/users'
        url += '/'+user.uuid if user else ''
        return url
