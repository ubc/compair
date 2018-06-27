# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from compair.core import db
from flask_login import current_app

from compair.learning_records.capture_events import on_assignment_create, \
    on_assignment_modified, on_assignment_delete

class AssignmentLearningRecordTests(ComPAIRLearningRecordTestCase):
    def setUp(self):
        super(ComPAIRLearningRecordTestCase, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.lti_data = LTITestData()
        self.user = self.data.authorized_student
        self.setup_session_data(self.user)
        self.course = self.data.main_course
        self.lti_context = self.lti_data.create_context(
            self.lti_data.lti_consumer,
            compair_course_id=self.course.id,
            lis_course_offering_sourcedid="sis_course_id",
            lis_course_section_sourcedid="sis_section_id",
        )
        self.assignment = self.data.assignments[0]

        self.expected_caliper_course = {
            'academicSession': self.course.term,
            'dateCreated': self.course.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.course.modified.replace(tzinfo=pytz.utc).isoformat(),
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'name': self.course.name,
            'type': 'CourseOffering',
            'extensions': {
                'ltiContexts': [{
                    'context_id': self.lti_context.context_id,
                    'oauth_consumer_key': self.lti_data.lti_consumer.oauth_consumer_key,
                    'lis_course_offering_sourcedid': "sis_course_id",
                    'lis_course_section_sourcedid': "sis_section_id",
                }]
            }
        }

        self.expected_caliper_assignment = {
            'name': self.assignment.name,
            'type': 'Assessment',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).isoformat(),
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).isoformat(),
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'isPartOf': self.expected_caliper_course,
            'items': [{
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/1",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/2",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/4",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/comparison/question/3",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/5",
                'type': 'AssessmentItem'
            }, {
                'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/evaluation/question/6",
                'type': 'AssessmentItem'
            }],
        }

        self.expected_xapi_course = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name}
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_sis_course = {
            'id': 'https://localhost:8888/course/'+self.lti_context.lis_course_offering_sourcedid,
            'objectType': 'Activity'
        }

        self.expected_xapi_sis_section = {
            'id': 'https://localhost:8888/course/'+self.lti_context.lis_course_offering_sourcedid+'/section/'+self.lti_context.lis_course_section_sourcedid,
            'objectType': 'Activity'
        }

        self.expected_xapi_assignment = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/assessment',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

    def test_on_assignment_create(self):
        on_assignment_create.send(
            current_app._get_current_object(),
            event_name=on_assignment_create.name,
            user=self.user,
            assignment=self.assignment
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Created',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': self.expected_caliper_assignment,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)


        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/author',
                'display': {'en-US': 'authored'}
            },
            "object": self.expected_xapi_assignment,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_course],
                    'grouping': [self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            }
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)



    def test_on_assignment_modified(self):
        on_assignment_modified.send(
            current_app._get_current_object(),
            event_name=on_assignment_modified.name,
            user=self.user,
            assignment=self.assignment
        )

        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Modified',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': self.expected_caliper_assignment,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)


        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/update',
                'display': {'en-US': 'updated'}
            },
            "object": self.expected_xapi_assignment,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_course],
                    'grouping': [self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            }
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

    def test_on_assignment_delete(self):
        on_assignment_delete.send(
            current_app._get_current_object(),
            event_name=on_assignment_delete.name,
            user=self.user,
            assignment=self.assignment
        )
        events = self.get_and_clear_caliper_event_log()
        expected_caliper_event = {
            'action': 'Deleted',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': self.expected_caliper_assignment,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)


        statements = self.get_and_clear_xapi_statement_log()
        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": {
                'id': 'http://activitystrea.ms/schema/1.0/delete',
                'display': {'en-US': 'deleted'}
            },
            "object": self.expected_xapi_assignment,
            "context": {
                'contextActivities': {
                    'parent': [self.expected_xapi_course],
                    'grouping': [self.expected_xapi_sis_course, self.expected_xapi_sis_section]
                },
                'extensions': {
                    'http://id.tincanapi.com/extension/browser-info': {},
                    'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
                }
            }
        }

        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)
