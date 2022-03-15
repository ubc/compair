# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import pytz

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData
from compair.tests.test_compair import ComPAIRLearningRecordTestCase

from data.factories import AnswerFactory
from compair.core import db
from flask import current_app

from compair.learning_records.capture_events import on_get_file, \
    on_attach_file, on_detach_file

class FileLearningRecordTests(ComPAIRLearningRecordTestCase):
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
        self.answer = AnswerFactory(
            assignment=self.assignment,
            user=self.user
        )
        db.session.commit()

        self.expected_caliper_course = {
            'academicSession': self.course.term,
            'dateCreated': self.course.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.course.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'name': self.course.name,
            'type': 'CourseOffering',
            'otherIdentifiers': [{
                'identifier': self.lti_context.context_id,
                'identifierType': 'LtiContextId',
                'type': 'SystemIdentifier',
                'extensions': {
                    'lis_course_offering_sourcedid': 'sis_course_id',
                    'lis_course_section_sourcedid': 'sis_section_id',
                    'oauth_consumer_key': self.lti_data.lti_consumer.oauth_consumer_key,
                },
            }]
        }

        self.expected_caliper_assignment = {
            'name': self.assignment.name,
            'type': 'Assessment',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
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

        self.expected_caliper_assignment_question = {
            'name': self.assignment.name,
            'type': 'AssessmentItem',
            'dateCreated': self.assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToStartOn': self.assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateToSubmit': self.assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'description': self.assignment.description,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'isPartOf': self.expected_caliper_assignment,
        }

        self.expected_caliper_answer_attempt = {
            'assignable': self.expected_caliper_assignment_question,
            'assignee': self.get_compair_caliper_actor(self.user),
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question/attempt/"+self.answer.attempt_uuid,
            'duration': "PT05M00S",
            'startedAtTime': self.answer.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'endedAtTime': self.answer.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'type': 'Attempt'
        }

        self.expected_caliper_answer = {
            'attempt': self.expected_caliper_answer_attempt,
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'type': 'Response',
            'dateCreated': self.answer.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'dateModified': self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'extensions': {
                'characterCount': len(self.answer.content),
                'content': self.answer.content,
                'isDraft': False,
                'wordCount': 8,
            }
        }

        self.expected_xapi_course = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid,
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/course',
                'name': {'en-US': self.course.name}
            },
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

        self.expected_xapi_assignment_question = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/question",
            'definition': {
                'type': 'http://adlnet.gov/expapi/activities/question',
                'name': {'en-US': self.assignment.name},
                'description': {'en-US': self.assignment.description},
            },
            'objectType': 'Activity'
        }

        self.expected_xapi_answer = {
            'id': "https://localhost:8888/app/course/"+self.course.uuid+"/assignment/"+self.assignment.uuid+"/answer/"+self.answer.uuid,
            'definition': {
                'type': 'http://id.tincanapi.com/activitytype/solution',
                'extensions': {
                    'http://id.tincanapi.com/extension/isDraft': False
                }
            },
            'objectType': 'Activity'
        }


    def test_on_get_file(self):
        # not report or attachment
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="none",
            file_name="some_file"
        )

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 0)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 0)

        # test report
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="report",
            file_name="some_report.csv"
        )

        expected_caliper_object = {
            "id": 'https://localhost:8888/app/report/some_report.csv',
            "type": "Document",
            "name": "some_report.csv",
            "mediaType": "text/csv"
        }

        expected_caliper_event = {
            'action': 'Downloaded',
            'profile': 'ResourceManagementProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'object': expected_caliper_object,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'ResourceManagementEvent'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_object = {
            'id': 'https://localhost:8888/app/report/some_report.csv',
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/file',
                'name': {'en-US': 'some_report.csv'},
                'extensions': {
                    'http://id.tincanapi.com/extension/mime-type': "text/csv"
                }
            },
            'objectType': 'Activity'
        }

        expected_xapi_verb = {
            'id': 'http://id.tincanapi.com/verb/downloaded',
            'display': {'en-US': 'downloaded'}
        }

        expected_xapi_context = {
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info()
            }
        }

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_xapi_verb,
            "object": expected_xapi_object,
            "context": expected_xapi_context
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)

        # test attachment without file record
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name="some_file"
        )

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 0)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 0)


        # test attachment file record (not linked to assignments or answers)
        file_record = self.data.create_file(self.user)
        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 0)

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 0)

        # test attachment file record (assignment)
        self.assignment.file_id = file_record.id
        db.session.commit()

        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        expected_caliper_object = {
            "id": 'https://localhost:8888/app/attachment/'+file_record.name,
            "type": "Document",
            "name": file_record.alias,
            "mediaType": 'application/pdf',
            "isPartOf": self.expected_caliper_assignment,
            "dateCreated": file_record.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "dateModified": file_record.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }

        self.expected_caliper_assignment['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        expected_caliper_event['object'] = expected_caliper_object
        expected_caliper_event['membership'] = self.get_caliper_membership(self.course, self.user, self.lti_context)

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_object = {
            'id': 'https://localhost:8888/app/attachment/'+file_record.name,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/file',
                'name': {'en-US': file_record.alias},
                'extensions': {
                    'http://id.tincanapi.com/extension/mime-type': 'application/pdf'
                }
            },
            'objectType': 'Activity'
        }

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_assignment],
                'grouping': [self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement['object'] = expected_xapi_object
        expected_xapi_statement['context'] = expected_xapi_context

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)


        # test attachment file record (answer)
        self.assignment.file_id = None
        self.answer.file_id = file_record.id
        db.session.commit()

        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=self.user,
            file_type="attachment",
            file_name=file_record.name
        )

        self.expected_caliper_assignment_question['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.expected_caliper_assignment['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        expected_caliper_object["isPartOf"] = self.expected_caliper_answer

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_answer],
                'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement['context'] = expected_xapi_context

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)


    def test_on_attach_file(self):
        file_record = self.data.create_file(self.user)
        self.assignment.file_id = file_record.id
        db.session.commit()

        # attache to assignment
        on_attach_file.send(
            current_app._get_current_object(),
            event_name=on_attach_file.name,
            user=self.user,
            file=file_record,
        )

        expected_caliper_object = {
            "id": 'https://localhost:8888/app/attachment/'+file_record.name,
            "type": "Document",
            "name": file_record.alias,
            "mediaType": 'application/pdf',
            "isPartOf": self.expected_caliper_assignment,
            "dateCreated": file_record.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "dateModified": file_record.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }

        self.expected_caliper_assignment['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        expected_caliper_event = {
            'action': 'Attached',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': expected_caliper_object,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_verb = {
            'id': 'http://activitystrea.ms/schema/1.0/attach',
            'display': {'en-US': 'attached'}
        }

        expected_xapi_object = {
            'id': 'https://localhost:8888/app/attachment/'+file_record.name,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/file',
                'name': {'en-US': file_record.alias},
                'extensions': {
                    'http://id.tincanapi.com/extension/mime-type': 'application/pdf'
                }
            },
            'objectType': 'Activity'
        }

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_assignment],
                'grouping': [self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_xapi_verb,
            "object": expected_xapi_object,
            "context": expected_xapi_context
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)



        # attach to answer
        self.assignment.file_id = None
        self.answer.file_id = file_record.id
        db.session.commit()

        on_attach_file.send(
            current_app._get_current_object(),
            event_name=on_attach_file.name,
            user=self.user,
            file=file_record,
        )

        self.expected_caliper_assignment_question['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.expected_caliper_assignment['dateModified'] = self.assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.expected_caliper_answer['dateModified'] = self.answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        expected_caliper_object["isPartOf"] = self.expected_caliper_answer

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_answer],
                'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement['context'] = expected_xapi_context

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)


    def test_on_detach_file(self):
        file_record = self.data.create_file(self.user)
        db.session.commit()

        # attache to assignment
        on_detach_file.send(
            current_app._get_current_object(),
            event_name=on_detach_file.name,
            user=self.user,
            file=file_record,
            assignment=self.assignment
        )

        expected_caliper_object = {
            "id": 'https://localhost:8888/app/attachment/'+file_record.name,
            "type": "Document",
            "name": file_record.alias,
            "mediaType": 'application/pdf',
            "isPartOf": self.expected_caliper_assignment,
            "dateCreated": file_record.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "dateModified": file_record.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }

        expected_caliper_event = {
            'action': 'Removed',
            'profile': 'GeneralProfile',
            'actor': self.get_compair_caliper_actor(self.user),
            'membership': self.get_caliper_membership(self.course, self.user, self.lti_context),
            'object': expected_caliper_object,
            'session': self.get_caliper_session(self.get_compair_caliper_actor(self.user)),
            'type': 'Event'
        }

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_verb = {
            'id': 'https://w3id.org/xapi/dod-isd/verbs/removed',
            'display': {'en-US': 'removed'}
        }

        expected_xapi_object = {
            'id': 'https://localhost:8888/app/attachment/'+file_record.name,
            'definition': {
                'type': 'http://activitystrea.ms/schema/1.0/file',
                'name': {'en-US': file_record.alias},
                'extensions': {
                    'http://id.tincanapi.com/extension/mime-type': 'application/pdf'
                }
            },
            'objectType': 'Activity'
        }

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_assignment],
                'grouping': [self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement = {
            "actor": self.get_compair_xapi_actor(self.user),
            "verb": expected_xapi_verb,
            "object": expected_xapi_object,
            "context": expected_xapi_context
        }

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)



        # attach to answer
        on_detach_file.send(
            current_app._get_current_object(),
            event_name=on_detach_file.name,
            user=self.user,
            file=file_record,
            answer=self.answer
        )

        expected_caliper_object["isPartOf"] = self.expected_caliper_answer

        events = self.get_and_clear_caliper_event_log()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], expected_caliper_event)

        expected_xapi_context = {
            'contextActivities': {
                'parent': [self.expected_xapi_answer],
                'grouping': [self.expected_xapi_assignment_question, self.expected_xapi_assignment, self.expected_xapi_course]
            },
            'extensions': {
                'http://id.tincanapi.com/extension/browser-info': {},
                'http://id.tincanapi.com/extension/session-info': self.get_xapi_session_info(),
                'sis_courses': [{
                    'id': 'sis_course_id',
                    'section_ids': ['sis_section_id']
                }]
            }
        }

        expected_xapi_statement['context'] = expected_xapi_context

        statements = self.get_and_clear_xapi_statement_log()
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], expected_xapi_statement)
