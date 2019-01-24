# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from data.fixtures.test_data import TestFixture, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase

from compair.models import UserCourse, CourseRole, ThirdPartyType, Group


class GroupsAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(GroupsAPITests, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=3)

    def test_get_groups(self):
        url = '/api/courses/'+self.fixtures.course.uuid+'/groups'

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
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
            expected = sorted(self.fixtures.groups, key=lambda group: group.name)
            self.assertEqual(len(actual), 4)
            for index, group in enumerate(expected):
                self.assertEqual(actual[index]['id'], group.uuid)

        # test TA
        with self.login(self.fixtures.ta.username):
            rv = self.client.get(url)
            self.assert200(rv)
            actual = rv.json['objects']
            expected = sorted(self.fixtures.groups, key=lambda group: group.name)
            self.assertEqual(len(actual), 4)
            for index, group in enumerate(expected):
                self.assertEqual(actual[index]['id'], group.uuid)

    def test_create_group(self):
        url = '/api/courses/'+self.fixtures.course.uuid+'/groups'

        group_expected = {
            'name': 'Group 101',
        }

        invalid_expected = {
            'name': self.fixtures.groups[1].name,
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert403(rv)

        # test ta
        with self.login(self.fixtures.ta.username):
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            invalid_url = '/api/courses/999/groups'
            rv = self.client.post(invalid_url, data=json.dumps(group_expected), content_type='application/json')
            self.assert404(rv)

            # test non-unique name
            rv = self.client.post(url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Group Not Added")
            self.assertEqual(rv.json['message'], "Sorry, the group name you have entered already exists. Please choose a different name.")

            # test successful query
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert200(rv)

            group_actual = rv.json
            self.assertEqual(group_expected['name'], group_actual['name'])

    def test_edit_group(self):
        group = self.fixtures.groups[0]
        url = '/api/courses/'+self.fixtures.course.uuid+'/groups/'+group.uuid

        group_expected = {
            'id': group.uuid,
            'name': 'New Group Name',
        }

        invalid_expected = {
            'id': group.uuid,
            'name': self.fixtures.groups[1].name,
        }

        # test login required
        rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert403(rv)

        # test ta
        with self.login(self.fixtures.ta.username):
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            invalid_url = '/api/courses/999/groups/'+group.uuid
            rv = self.client.post(invalid_url, data=json.dumps(group_expected), content_type='application/json')
            self.assert404(rv)

            # test invalid group id
            invalid_url = '/api/courses/'+self.fixtures.course.uuid+'/groups/999'
            rv = self.client.post(invalid_url, data=json.dumps(group_expected), content_type='application/json')
            self.assert404(rv)

            # test non-unique name
            rv = self.client.post(url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Group Not Saved")
            self.assertEqual(rv.json['message'], "Sorry, the group name you have entered already exists. Please choose a different name.")

            # test successful query
            rv = self.client.post(url, data=json.dumps(group_expected), content_type='application/json')
            self.assert200(rv)

            group_actual = rv.json
            self.assertEqual(group_expected['id'], group_actual['id'])
            self.assertEqual(group_expected['name'], group_actual['name'])


    def test_delete_group(self):
        group = self.fixtures.groups[0]
        self.fixtures.add_assignments(num_assignments=1, with_group_answers=True)

        url = '/api/courses/'+self.fixtures.course.uuid+'/groups/'+group.uuid

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test ta
        with self.login(self.fixtures.ta.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test student
        student = self.fixtures.students[0]
        for user_context in [ self.login(student.username), self.impersonate(self.fixtures.instructor, student)]:
            with user_context:
                rv = self.client.delete(url)
                self.assert403(rv)

        with self.login(self.fixtures.instructor.username):
            # test invalid course id
            invalid_url = '/api/courses/999/groups/'+group.uuid
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test invalid group id
            invalid_url = '/api/courses/'+self.fixtures.course.uuid+'/groups/999'
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test successful query
            rv = self.client.delete(url)
            self.assert200(rv)

            # test cannot delete again
            rv = self.client.delete(url)
            self.assert404(rv)

            # the group answer flags should be false
            rv = self.client.get('/api/courses/'+self.fixtures.course.uuid+'/groups')
            self.assert200(rv)
            for the_group in [g for g in rv.json['objects']]:
                self.assertFalse(the_group['group_answer_exists'])

            # test cannot delete group if it has an answer
            self.fixtures.add_answers()
            group = self.fixtures.groups[1]
            url = '/api/courses/'+self.fixtures.course.uuid+'/groups/'+group.uuid
            rv = self.client.delete(url)
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Group Not Deleted")
            self.assertEqual(rv.json['message'], "Sorry, you cannot remove groups that have submitted answers.")

            # verify the group answer exists flag
            rv = self.client.get('/api/courses/'+self.fixtures.course.uuid+'/groups')
            self.assert200(rv)
            the_group = [g for g in rv.json['objects'] if g['id'] == group.uuid]
            self.assertEqual(len(the_group), 1)
            self.assertTrue(the_group[0]['group_answer_exists'])

            # verfiy that after group is deleted, can re-create it with same name
            deleted_group = self.fixtures.groups[0]
            new_group = {
                'name': deleted_group.name,
            }
            rv = self.client.post('/api/courses/'+self.fixtures.course.uuid+'/groups', data=json.dumps(new_group), content_type='application/json')
            self.assert200(rv)