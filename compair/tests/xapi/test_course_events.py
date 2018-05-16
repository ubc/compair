# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from data.fixtures.test_data import BasicTestData
from compair.tests.test_compair import ComPAIRXAPITestCase

from compair.core import db
from flask_login import current_app

from compair.xapi.capture_events import on_course_create, \
    on_course_modified, on_course_delete

class CourseXAPITests(ComPAIRXAPITestCase):
    def setUp(self):
        super(ComPAIRXAPITestCase, self).setUp()
        self.data = BasicTestData()
        self.user = self.data.authorized_student
        self.course = self.data.main_course

    def test_on_course_create(self):
        on_course_create.send(
            current_app._get_current_object(),
            event_name=on_course_create.name,
            user=self.user,
            course=self.course
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/author',
            'display': {'en-US': 'authored'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])


    def test_on_course_modified(self):
        on_course_modified.send(
            current_app._get_current_object(),
            event_name=on_course_modified.name,
            user=self.user,
            course=self.course
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/update',
            'display': {'en-US': 'updated'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])

    def test_on_course_delete(self):
        on_course_delete.send(
            current_app._get_current_object(),
            event_name=on_course_delete.name,
            user=self.user,
            course=self.course
        )

        statements = self.get_and_clear_statement_log()
        self.assertEqual(len(statements), 1)

        self.assertEqual(statements[0]['actor'], self.get_compair_actor(self.user))
        self.assertEqual(statements[0]['verb'], {
            'id': 'http://activitystrea.ms/schema/1.0/delete',
            'display': {'en-US': 'deleted'}
        })
        self.assertEqual(statements[0]['object'], {
            'id': 'https://localhost:8888/app/xapi/course/'+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name }
            },
            'objectType': 'Activity'
        })
        self.assertNotIn('result', statements[0])
        self.assertNotIn('context', statements[0])