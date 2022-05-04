# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink
from compair.models.lti_models import MembershipInvalidRequestException, MembershipNoResultsException, \
    MembershipNoValidContextsException
from compair.core import db

class LTICourseAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LTICourseAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.lti_data = LTITestData()

    def get_all_lti_course_links(self):
        course = self.data.get_course()
        course2 = self.data.create_course()

        lti_consumer = self.lti_data.get_consumer()
        lti_consumer2 = self.lti_data.create_consumer()
        url = '/api/lti/course/context'

        for _ in range(15):
            self.lti_data.create_context(
                lti_consumer,
                compair_course_id=course.id
            )
        for _ in range(15):
            self.lti_data.create_context(
                lti_consumer2,
                compair_course_id=course2.id
            )

        # Test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.fixtures.get_authorized_instructor.username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.fixtures.get_authorized_student.username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.fixtures.get_authorized_ta.username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login('root'):
            # test non-existent entry
            rv = self.client.get('/api/lti/course/999/context')
            self.assert404(rv)

            # test data retrieve is correct
            rv = self.client.get(url)
            self.assert200(rv)

            actual_lti_contexts = rv.json['objects']

            result = rv.json['objects']
            expected_results = LTIContext.query \
                .order_by(LTIContext.created.desc()) \
                .paginate(1, 20)

            for i, expected in enumerate(expected_results.items):
                self.assertEqual(expected.uuid, result[i]['id'])
                self.assertEqual(expected.compair_course.uuid, result[i]['compair_course_id'])
                self.assertEqual(expected.compair_course.name, result[i]['compair_course_name'])
                self.assertEqual(expected.oauth_consumer_key, result[i]['oauth_consumer_key'])
                self.assertEqual(expected.context_id, result[i]['context_id'])
                self.assertEqual(expected.context_title, result[i]['context_title'])

            self.assertEqual(1, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_results.total, rv.json['total'])

            # test the second page
            rv = self.client.get(url + '?page=2')
            self.assert200(rv)

            result = rv.json['objects']
            expected_results = LTIContext.query \
                .order_by(LTIContext.created.desc()) \
                .paginate(2, 20)

            for i, expected in enumerate(expected_results.items):
                self.assertEqual(expected.uuid, result[i]['id'])
                self.assertEqual(expected.compair_course.uuid, result[i]['compair_course_id'])
                self.assertEqual(expected.compair_course.name, result[i]['compair_course_name'])
                self.assertEqual(expected.oauth_consumer_key, result[i]['oauth_consumer_key'])
                self.assertEqual(expected.context_id, result[i]['context_id'])
                self.assertEqual(expected.context_title, result[i]['context_title'])

            self.assertEqual(2, rv.json['page'])
            self.assertEqual(2, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(expected_results.total, rv.json['total'])

            # test sorting by context_title
            rv = self.client.get(url + '?orderBy=context_title')
            self.assert200(rv)
            result = rv.json['objects']

            # test the result is paged and sorted
            expected = sorted(
                [lti_context for lti_context in self.lti_data.lti_contexts],
                key=lambda context: (lti_context.context_title, context.created),
                reverse=True)[:20]

            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            # test sorting by course name
            rv = self.client.get(url + '?orderBy=course.name')
            self.assert200(rv)
            result = rv.json['objects']

            # test the result is paged and sorted
            expected = sorted(
                [lti_context for lti_context in self.lti_data.lti_contexts],
                key=lambda context: (lti_context.compair_course.name, context.created),
                reverse=True)[:20]

            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(len(expected), rv.json['total'])

            # test search filter context title
            expected = [self.lti_data.lti_contexts[10]]
            search_filter = self.lti_data.lti_contexts[10].context_title
            rv = self.client.get(self.base_url + '?search='+search_filter)
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

            # test search filter context id
            expected = [self.lti_data.lti_contexts[10]]
            search_filter = self.lti_data.lti_contexts[10].context_id
            rv = self.client.get(self.base_url + '?search='+search_filter)
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(1, rv.json['total'])

            # test search filter course_name
            expected = sorted(
                [lti_context for lti_context in self.lti_data.lti_contexts
                    if lti_context.compair_course_id == course.id],
                key=lambda context: context.created,
                reverse=True)
            search_filter = course.name
            rv = self.client.get(self.base_url + '?search='+search_filter)
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(15, rv.json['total'])

            # test search filter oauth_consumer_key
            expected = sorted(
                [lti_context for lti_context in self.lti_data.lti_contexts
                    if lti_context.lti_consumer_id == lti_consumer.id],
                key=lambda context: context.created,
                reverse=True)
            search_filter = lti_consumer.oauth_consumer_key
            rv = self.client.get(self.base_url + '?search='+search_filter)
            self.assert200(rv)
            result = rv.json['objects']
            self.assertEqual([c.uuid for c in expected], [c['id'] for c in result])
            self.assertEqual(1, rv.json['page'])
            self.assertEqual(1, rv.json['pages'])
            self.assertEqual(20, rv.json['per_page'])
            self.assertEqual(15, rv.json['total'])

    def test_lti_course_link(self):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        url = '/api/lti/course/'+course.uuid+'/context'

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(lti_consumer)
        lti_user = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
        lti_user_resource_link = self.lti_data.create_user_resource_link(
            lti_user, lti_resource_link, CourseRole.instructor)

        # test login required
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert401(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # requires lti session
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert400(rv)

        # setup lti session with no context id
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=None, roles="Instructor") as rv:
            self.assert200(rv)

        # check session
        with self.client.session_transaction() as sess:
            # check that user is logged in
            self.assertEqual(str(instructor.id), sess.get('_user_id'))
            self.assertIsNone(sess.get('lti_context'))

        # link course
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert400(rv)

        # setup lti session with context id
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor") as rv:
            self.assert200(rv)

        # check session
        with self.client.session_transaction() as sess:
            # check that user is logged in
            self.assertEqual(str(instructor.id), sess.get('_user_id'))
            self.assertEqual(lti_context.id, sess.get('lti_context'))

        # link course
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert200(rv)


    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._post_membership_request')
    def test_lti_course_link_with_membership_ext(self, mocked_post_membership_request):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        current_users = [(user_course.user_id, user_course.course_role) for user_course in course.user_courses]

        url = '/api/lti/course/'+course.uuid+'/context'

        lti_consumer = self.lti_data.lti_consumer
        lti_consumer.global_unique_identifier_param = "custom_puid"
        lti_consumer.student_number_param = "custom_student_number"
        lti_consumer.custom_param_regex_sanitizer = "^\\$.+$"
        db.session.commit()

        lti_context = self.lti_data.create_context(lti_consumer)
        lti_user = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
        lti_user_resource_link = self.lti_data.create_user_resource_link(
            lti_user, lti_resource_link, CourseRole.instructor)

        # test invalid request
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type></lti_message_type>
                <statusinfo>
                    <codemajor>Failure</codemajor>
                    <severity>Error</severity>
                    <codeminor>Invalid request</codeminor>
                </statusinfo>
                </message_response>
            """

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # membership should not change
            for user_course in course.user_courses:
                self.assertIn((user_course.user_id, user_course.course_role), current_users)

        # test empty membership response
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                </memberships>
                </message_response>
            """

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # membership should not change
            for user_course in course.user_courses:
                self.assertIn((user_course.user_id, user_course.course_role), current_users)


        # test successful membership response (minimual returned data)
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>{instructor_user_id}</user_id>
                    <roles>Instructor</roles>
                    </member>
                    <member>
                    <user_id>compair_student_1</user_id>
                    <roles>Learner</roles>
                    </member>
                    <member>
                    <user_id>compair_student_2</user_id>
                    <roles>Learner</roles>
                    </member>
                    <member>
                    <user_id>compair_student_3è</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                    <member>
                    <user_id>compair_instructor_2</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                </memberships>
                </message_response>
            """.format(instructor_user_id=lti_user.user_id)

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members in minimal_membership (all old users besides instructor should be dropped)

            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user.user_id, "compair_student_1", "compair_student_2",
                    "compair_student_3è", "compair_instructor_2"])
                self.assertIsNone(lti_membership.lti_user.student_number)

        # test successful membership response (with global_unique_identifier_param)
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>some_user_id_1</user_id>
                    <roles>Instructor</roles>
                    <custom_puid>guid1</custom_puid>
                    <custom_student_number></custom_student_number>
                    </member>
                    <member>
                    <user_id>some_user_id_2</user_id>
                    <roles>Learner</roles>
                    <custom_puid>guid2</custom_puid>
                    <custom_student_number>12345678901</custom_student_number>
                    </member>
                    <member>
                    <user_id>some_user_id_3</user_id>
                    <roles>Learner</roles>
                    <custom_puid>guid3</custom_puid>
                    <custom_student_number>12345678902</custom_student_number>
                    </member>
                    <member>
                    <user_id>some_user_id_4</user_id>
                    <roles>TeachingAssistant</roles>
                    <custom_puid>guid4è</custom_puid>
                    <custom_student_number>12345678903</custom_student_number>
                    </member>
                    <member>
                    <user_id>some_user_id_5</user_id>
                    <roles>TeachingAssistant</roles>
                    <custom_puid>guid5</custom_puid>
                    <custom_student_number>12345678904</custom_student_number>
                    </member>
                </memberships>
                </message_response>
            """

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members in minimal_membership (old users expect instructor should be dropped)

            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user.global_unique_identifier == 'guid1' or user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user.global_unique_identifier in ['guid4è', 'guid5']:
                    self.assertEqual(user_course.course_role, CourseRole.teaching_assistant)
                elif user_course.user.global_unique_identifier in ['guid2', 'guid3']:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [
                    lti_user.user_id, "some_user_id_1", "some_user_id_2",
                    "some_user_id_3", "some_user_id_4", "some_user_id_5"])
                self.assertIn(lti_membership.lti_user.global_unique_identifier, [
                    "guid1", "guid2", "guid3", "guid4è", "guid5"])

                if lti_membership.lti_user.system_role == SystemRole.student:
                    self.assertIn(lti_membership.lti_user.student_number, ["12345678901", "12345678902", "12345678903", "12345678904"])
                else:
                    self.assertIsNone(lti_membership.lti_user.student_number)

    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._get_membership_request')
    def test_lti_course_link_with_membership_service(self, mocked_get_membership_request):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        current_users = [(user_course.user_id, user_course.course_role) for user_course in course.user_courses]

        url = '/api/lti/course/'+course.uuid+'/context'

        lti_consumer = self.lti_data.lti_consumer

        lti_context = self.lti_data.create_context(lti_consumer)
        lti_user = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
        lti_user_resource_link = self.lti_data.create_user_resource_link(
            lti_user, lti_resource_link, CourseRole.instructor)

        # test empty membership response
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                custom_context_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "@id":None,
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[]
                    },
                    "@id":None,
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # membership should not change
            for user_course in course.user_courses:
                self.assertIn((user_course.user_id, user_course.course_role), current_users)


        def minimal_membership_requests(memberships_url, headers=None):
            if memberships_url == "https://mockmembershipurl.com":
                return {
                    "@id":None,
                    "@type":"Page",
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "differences":None,
                    "nextPage":None,
                    "pageOf":{
                        "membershipPredicate":"http://www.w3.org/ns/org#membership",
                        "membershipSubject":{
                            "name":"Test Course",
                            "@type":"Context",
                            "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                            "membership":[
                                {
                                    "status":"Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/Instructor"
                                    ],
                                    "member":{
                                        "userId":lti_user.user_id
                                    }
                                },
                                {
                                    "status":"liss:Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_1"
                                    }
                                },
                                {
                                    "status":"Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_2"
                                    }
                                },
                                {
                                    "status":"Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/TeachingAssistant"
                                    ],
                                    "member":{
                                        "userId":"compair_student_3è"
                                    }
                                },
                                {
                                    "status":"Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/TeachingAssistant"
                                    ],
                                    "member":{
                                        "userId":"compair_instructor_2"
                                    }
                                },
                                {
                                    "status":"Inactive",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_100"
                                    }
                                }
                            ]
                        },
                        "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                        "@type":"LISMembershipContainer"
                    }
                }
            elif memberships_url == "https://mockmembershipurl.com?role=Learner&rlid="+lti_resource_link.resource_link_id:
                return {
                    "@id":None,
                    "@type":"Page",
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "differences":None,
                    "nextPage":None,
                    "pageOf":{
                        "membershipPredicate":"http://www.w3.org/ns/org#membership",
                        "membershipSubject":{
                            "name":"Test Course",
                            "@type":"Context",
                            "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                            "membership":[
                                {
                                    "status":"liss:Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_1"
                                    },
                                    "message": [{
                                        "message_type": "basic-lti-launch-request",
                                        "lis_result_sourcedid": "lis_result_sourcedid_compair_student_1"
                                    },{
                                        "message_type": "other-message-type"
                                    }]
                                },
                                {
                                    "status":"Active",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_2"
                                    },
                                    "message": [{
                                        "message_type": "basic-lti-launch-request",
                                        "lis_result_sourcedid": "lis_result_sourcedid_compair_student_2"
                                    },{
                                        "message_type": "other-message-type"
                                    }]
                                },
                                {
                                    "status":"Inactive",
                                    "role":[
                                        "urn:lti:role:ims/lis/Learner"
                                    ],
                                    "member":{
                                        "userId":"compair_student_100"
                                    },
                                    "message": [{
                                        "message_type": "basic-lti-launch-request",
                                        "lis_result_sourcedid": "lis_result_sourcedid_compair_student_100"
                                    },{
                                        "message_type": "other-message-type"
                                    }]
                                }
                            ]
                        },
                        "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                        "@type":"LISMembershipContainer"
                    }
                }


        # test successful membership response (minimal returned data)
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                custom_context_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            mocked_get_membership_request.reset_mock()
            mocked_get_membership_request.side_effect = minimal_membership_requests

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members in minimal_membership (all old users besides instructor should be dropped)

            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            lti_user_resource_links = LTIUserResourceLink.query \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user.user_id, "compair_student_1", "compair_student_2",
                    "compair_student_3è", "compair_instructor_2"])

                # ensure the lti_user_resource_link is generated and stores the lis_result_sourcedid
                if lti_membership.lti_user.user_id in [lti_user.user_id, "compair_student_3è", "compair_instructor_2"]:
                    self.assertIsNone(lti_membership.lis_result_sourcedids)
                else:
                    self.assertIsNotNone(lti_membership.lis_result_sourcedids)
                    lti_user_resource_links = [lti_user_resource_link \
                        for lti_user_resource_link in lti_membership.lti_user.lti_user_resource_links.all() \
                        if lti_user_resource_link.lti_resource_link_id == lti_resource_link.id
                    ]
                    self.assertEqual(len(lti_user_resource_links), 1)
                    self.assertEqual(lti_user_resource_links[0].lis_result_sourcedid,
                        "lis_result_sourcedid_"+lti_membership.lti_user.user_id)

        for global_unique_identifier_param in [None, "custom_puid", "ext_user_username"]:
            for student_number_param in [None, "custom_student_number"]:

                def global_unique_identifier_membership_requests(memberships_url, headers=None):
                    if memberships_url == "https://mockmembershipurl.com":
                        return {
                            "@id":None,
                            "@type":"Page",
                            "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                            "differences":None,
                            "nextPage":None,
                            "pageOf":{
                                "membershipPredicate":"http://www.w3.org/ns/org#membership",
                                "membershipSubject":{
                                    "name":"Test Course",
                                    "@type":"Context",
                                    "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                                    "membership":[
                                        {
                                            "status":"Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/Instructor"
                                            ],
                                            "member":{
                                                "userId": lti_user.user_id
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": lti_user.user_id,
                                                    "custom" : {
                                                        "puid": lti_user.user_id,
                                                        "student_number": None
                                                    },
                                                    "ext" : {
                                                        "user_username": lti_user.user_id
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"liss:Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_2"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "1234567890-1",
                                                    "custom" : {
                                                        "puid": "compair_student_1_puid",
                                                        "student_number": "12345678901"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_1_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_3"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "1234567890-2",
                                                    "custom" : {
                                                        "puid": "compair_student_2_puid",
                                                        "student_number": "12345678902"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_2_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/TeachingAssistant"
                                            ],
                                            "member":{
                                                "userId":"userId_4"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "1234567890-3",
                                                    "custom" : {
                                                        "puid": "compair_student_3è_puid",
                                                        "student_number": "12345678903"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_3è_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/TeachingAssistant"
                                            ],
                                            "member":{
                                                "userId":"userId_5"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "1234567890-4",
                                                    "custom" : {
                                                        "puid": "compair_instructor_2_puid",
                                                        "student_number": "12345678904"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_instructor_2_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Inactive",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_6"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "1234567890-5",
                                                    "custom" : {
                                                        "puid": "compair_student_100_puid",
                                                        "student_number": "12345678905"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_100_username",
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                                "@type":"LISMembershipContainer"
                            }
                        }
                    elif memberships_url == "https://mockmembershipurl.com?role=Learner&rlid="+lti_resource_link.resource_link_id:
                        return {
                            "@id":None,
                            "@type":"Page",
                            "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                            "differences":None,
                            "nextPage":None,
                            "pageOf":{
                                "membershipPredicate":"http://www.w3.org/ns/org#membership",
                                "membershipSubject":{
                                    "name":"Test Course",
                                    "@type":"Context",
                                    "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                                    "membership":[
                                        {
                                            "status":"liss:Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_2"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "lis_result_sourcedid_compair_student_1",
                                                    "custom" : {
                                                        "puid": "compair_student_1_puid",
                                                        "student_number": "12345678901"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_1_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Active",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_3"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "lis_result_sourcedid_compair_student_2",
                                                    "custom" : {
                                                        "puid": "compair_student_2_puid",
                                                        "student_number": "12345678902"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_2_username",
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "status":"Inactive",
                                            "role":[
                                                "urn:lti:role:ims/lis/Learner"
                                            ],
                                            "member":{
                                                "userId": "userId_6"+str(global_unique_identifier_param)
                                            },
                                            "message" : [
                                                {
                                                    "message_type": "basic-lti-launch-request",
                                                    "lis_result_sourcedid": "lis_result_sourcedid_compair_student_100",
                                                    "custom" : {
                                                        "puid": "compair_student_100_puid",
                                                        "student_number": "12345678905"+str(global_unique_identifier_param)
                                                    },
                                                    "ext" : {
                                                        "user_username": "compair_student_100_username",
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                                "@type":"LISMembershipContainer"
                            }
                        }

                lti_consumer.global_unique_identifier_param = global_unique_identifier_param
                lti_consumer.student_number_param = student_number_param
                db.session.commit()

                # test successful membership response (global_unique_identifier_param)
                with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                        user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                        custom_context_memberships_url="https://mockmembershipurl.com") as rv:
                    self.assert200(rv)

                    mocked_get_membership_request.reset_mock()
                    mocked_get_membership_request.side_effect = global_unique_identifier_membership_requests

                    # link course
                    rv = self.client.post(url, data={}, content_type='application/json')
                    self.assert200(rv)

                    # 5 members in minimal_membership (all old users besides instructor should be dropped)

                    # verify user course roles
                    for user_course in course.user_courses:
                        if global_unique_identifier_param == None:
                            if user_course.user_id == instructor.id:
                                self.assertEqual(user_course.course_role, CourseRole.instructor)
                            else:
                                #everyone else should be dropped
                                self.assertEqual(user_course.course_role, CourseRole.dropped)
                        elif global_unique_identifier_param == "custom_puid":
                            if user_course.user_id == instructor.id:
                                self.assertEqual(user_course.course_role, CourseRole.instructor)
                            elif user_course.user.global_unique_identifier in ["compair_student_1_puid", "compair_student_2_puid"]:
                                self.assertEqual(user_course.course_role, CourseRole.student)
                            elif user_course.user.global_unique_identifier in ["compair_student_3è_puid", "compair_instructor_2_puid"]:
                                self.assertEqual(user_course.course_role, CourseRole.teaching_assistant)
                            else:
                                #everyone else should be dropped
                                self.assertEqual(user_course.course_role, CourseRole.dropped)
                        elif global_unique_identifier_param == "ext_user_username":
                            if user_course.user_id == instructor.id:
                                self.assertEqual(user_course.course_role, CourseRole.instructor)
                            elif user_course.user.global_unique_identifier in ["compair_student_1_username", "compair_student_2_username"]:
                                self.assertEqual(user_course.course_role, CourseRole.student)
                            elif user_course.user.global_unique_identifier in ["compair_student_3è_username", "compair_instructor_2_username"]:
                                self.assertEqual(user_course.course_role, CourseRole.teaching_assistant)
                            else:
                                #everyone else should be dropped
                                self.assertEqual(user_course.course_role, CourseRole.dropped)

                    # verify membership table
                    lti_memberships = LTIMembership.query \
                        .filter_by(compair_course_id=course.id) \
                        .all()

                    self.assertEqual(len(lti_memberships), 5)
                    for lti_membership in lti_memberships:
                        id_app = str(global_unique_identifier_param)
                        self.assertIn(lti_membership.lti_user.user_id, [
                            lti_user.user_id, "userId_2"+id_app, "userId_3"+id_app,
                            "userId_4"+id_app, "userId_5"+id_app])

                        if global_unique_identifier_param == None:
                            self.assertIsNone(lti_membership.lti_user.global_unique_identifier)
                        elif global_unique_identifier_param == "custom_puid":
                            self.assertIn(lti_membership.lti_user.global_unique_identifier, [
                                lti_user.user_id, "compair_student_1_puid", "compair_student_2_puid",
                                "compair_student_3è_puid", "compair_instructor_2_puid"])
                        elif global_unique_identifier_param == "ext_user_username":
                            self.assertIn(lti_membership.lti_user.global_unique_identifier, [
                                lti_user.user_id, "compair_student_1_username", "compair_student_2_username",
                                "compair_student_3è_username", "compair_instructor_2_username"])
                        elif global_unique_identifier_param == "lis_result_sourcedid":
                            self.assertIn(lti_membership.lti_user.global_unique_identifier, [
                                lti_user.user_id, "1234567890-1", "1234567890-2",
                                "1234567890-3", "1234567890-4"])

                        if student_number_param == "custom_student_number" and lti_membership.lti_user.system_role == SystemRole.student:
                            sn_app = str(global_unique_identifier_param)
                            self.assertIn(lti_membership.lti_user.student_number,
                                ["12345678901"+sn_app, "12345678902"+sn_app,
                                "12345678903"+sn_app, "12345678904"+sn_app])
                        else:
                            self.assertIsNone(lti_membership.lti_user.student_number)

        lti_consumer.global_unique_identifier_param = None
        lti_consumer.student_number_param = None
        db.session.commit()

        def paginated_membership_requests(memberships_url, headers=None):
            result = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage": None, #fill in
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[
                            {
                                "status":"Active",
                                "role":[], #fill in
                                "member":{
                                    "userId": None #fill in
                                }
                            }
                        ]
                    },
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }
            result_launch_message = {
                "message_type" : "basic-lti-launch-request",
                "lis_result_sourcedid" : None #fill in
            }
            rlid = lti_resource_link.resource_link_id

            if memberships_url == "https://mockmembershipurl.com":
                result['nextPage'] = "https://mockmembershipurl.com?page=2&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Instructor"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = lti_user.user_id

            elif memberships_url == "https://mockmembershipurl.com?page=2&per_page=1":
                result['nextPage'] = "https://mockmembershipurl.com?page=3&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Learner"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_1"

            elif memberships_url == "https://mockmembershipurl.com?page=3&per_page=1":
                result['nextPage'] = "https://mockmembershipurl.com?page=4&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Instructor"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_2"

            elif memberships_url == "https://mockmembershipurl.com?page=4&per_page=1":
                result['nextPage'] = "https://mockmembershipurl.com?page=5&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/TeachingAssistant"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_3è"

            elif memberships_url == "https://mockmembershipurl.com?page=5&per_page=1":
                result['nextPage'] = "https://mockmembershipurl.com?page=6&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/TeachingAssistant"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_instructor_2"

            elif memberships_url == "https://mockmembershipurl.com?page=6&per_page=1":
                result['nextPage'] = None
                result['pageOf']['membershipSubject']['membership'][0]['status'] = "Inactive"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Learner"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_100"

            elif memberships_url == "https://mockmembershipurl.com?role=Learner&rlid="+rlid:
                result['nextPage'] = "https://mockmembershipurl.com?role=Learner&rlid="+rlid+"&page=2&per_page=1"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Learner"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_1"
                result_launch_message['lis_result_sourcedid'] = "lis_result_sourcedid_compair_student_1"
                result['pageOf']['membershipSubject']['membership'][0]['message'] = [result_launch_message]

            elif memberships_url == "https://mockmembershipurl.com?role=Learner&rlid="+rlid+"&page=2&per_page=1":
                result['nextPage'] = None
                result['pageOf']['membershipSubject']['membership'][0]['status'] = "Inactive"
                result['pageOf']['membershipSubject']['membership'][0]['role'] = ["urn:lti:role:ims/lis/Learner"]
                result['pageOf']['membershipSubject']['membership'][0]['member']['userId'] = "compair_student_100"
                result_launch_message['lis_result_sourcedid'] = "lis_result_sourcedid_compair_student_100"
                result['pageOf']['membershipSubject']['membership'][0]['message'] = [result_launch_message]

            return result

        mocked_get_membership_request.reset_mock()
        mocked_get_membership_request.side_effect = paginated_membership_requests

        # test successful membership response with pagination
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                custom_context_memberships_url="https://mockmembershipurl.com") as rv:
            self.assert200(rv)

            # link course
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            self.assertEqual(mocked_get_membership_request.call_count, 8)

            # 5 members in minimal_membership (all old users besides instructor should be dropped)

            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user.user_id, "compair_student_1", "compair_student_2",
                    "compair_student_3è", "compair_instructor_2"])

    def test_lti_course_unlink(self):
        course = self.data.get_course()

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id
        )
        lti_consumer2 = self.lti_data.create_consumer()
        lti_context2 = self.lti_data.create_context(
            lti_consumer2,
            compair_course_id=course.id
        )

        url = '/api/lti/course/'+course.uuid+'/context/'+lti_context.uuid

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized users
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_student().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        with self.login('root'):
            # test invalid course id
            rv = self.client.delete('/api/courses/999/context/'+lti_context.uuid)
            self.assert404(rv)

            # test invalid context id
            rv = self.client.delete('/api/courses/'+course.uuid+'/context/999')
            self.assert404(rv)

            # test deletion by admin
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(len(course.lti_contexts.all()), 1)

            # test lti link is unlinked
            rv = self.client.delete(url)
            self.assert400(rv)
            self.assertEqual("Course Not Unlinked", rv.json['title'])
            self.assertEqual("Sorry, The LTI context is already not linked to the course.", rv.json['message'])

            # test deletion by admin again
            url = '/api/lti/course/'+course.uuid+'/context/'+lti_context2.uuid
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(len(course.lti_contexts.all()), 0)

    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._get_membership')
    def test_lti_course_unlink_with_membership(self, mocked_get_membership):
        mocked_get_membership.return_value = []

        course = self.data.get_course()

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id,
            ext_ims_lis_memberships_id="123",
            ext_ims_lis_memberships_url="https://mockmembershipurl.com"
        )
        lti_consumer2 = self.lti_data.create_consumer()
        lti_context2 = self.lti_data.create_context(
            lti_consumer2,
            compair_course_id=course.id,
            ext_ims_lis_memberships_id="456",
            ext_ims_lis_memberships_url="https://mockmembershipurl2.com"
        )

        url = '/api/lti/course/'+course.uuid+'/context/'+lti_context.uuid

        with self.login('root'):
            # test deletion by admin
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(len(course.lti_contexts.all()), 1)

            mocked_get_membership.assert_called_once_with(
                lti_context2
            )
            mocked_get_membership.reset_mock()

            # test deletion by admin again
            # shouldn't cause error due to no valid contexts
            url = '/api/lti/course/'+course.uuid+'/context/'+lti_context2.uuid
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(len(course.lti_contexts.all()), 0)

            mocked_get_membership.assert_not_called()

    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._post_membership_request')
    def test_lti_membership_for_consumer_with_membership_ext(self, mocked_post_membership_request):
        course = self.data.get_course()
        instructor = self.data.get_authorized_instructor()
        student_1 = self.data.authorized_student
        student_2 = self.data.create_normal_user()
        self.data.enrol_student(student_2, course)

        current_user_ids = [user_course.user_id for user_course in course.user_courses]

        url = '/api/lti/course/'+course.uuid+'/membership'

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id,
            ext_ims_lis_memberships_id="123",
            ext_ims_lis_memberships_url="https://mockmembershipurl.com"
        )

        lti_user_instructor = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_user_student_1 = self.lti_data.create_user(lti_consumer, SystemRole.student, student_1)

        # test login required
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert401(rv)


        with self.login(self.data.get_unauthorized_instructor().username):
            # test unauthroized user
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert403(rv)


        with self.login(self.data.get_authorized_instructor().username):
            # Test invalid course id
            rv = self.client.post('/api/lti/course/999/membership', data={}, content_type='application/json')
            self.assert404(rv)

            # test invalid request
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type></lti_message_type>
                <statusinfo>
                    <codemajor>Failure</codemajor>
                    <severity>Error</severity>
                    <codeminor>Invalid request</codeminor>
                </statusinfo>
                </message_response>
            """
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'], "The membership request was invalid. Please relaunch the LTI link and try again.")

            # test empty membership response
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                </memberships>
                </message_response>
            """
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "The membership service did not return any users. Please check your LTI course and try again.")

            # test full membership response
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>{instructor_user_id}</user_id>
                    <user_image>http://www.gravatar.com/avatar/1</user_image>
                    <roles>Instructor</roles>
                    <person_sourcedid>compair_instructor_2</person_sourcedid>
                    <person_contact_email_primary>compair_instructor_2@test.com</person_contact_email_primary>
                    <person_name_given>Instructor</person_name_given>
                    <person_name_family>Two</person_name_family>
                    <person_name_full>Instructor Two</person_name_full>
                    </member>
                    <member>
                    <user_id>{student_user_id}</user_id>
                    <user_image>http://www.gravatar.com/avatar/2</user_image>
                    <roles>Learner</roles>
                    <person_sourcedid>compair_student_1</person_sourcedid>
                    <person_contact_email_primary>compair_student_1@test.com</person_contact_email_primary>
                    <person_name_given>Student</person_name_given>
                    <person_name_family>One</person_name_family>
                    <person_name_full>Student One</person_name_full>
                    <lis_result_sourcedid>:_676_1::compai:compair_student_1</lis_result_sourcedid>
                    </member>
                    <member>
                    <user_id>compair_student_2</user_id>
                    <user_image>http://www.gravatar.com/avatar/3</user_image>
                    <roles>Learner</roles>
                    <person_sourcedid>compair_student_2</person_sourcedid>
                    <person_contact_email_primary>compair_student_2@test.com</person_contact_email_primary>
                    <person_name_given>Student</person_name_given>
                    <person_name_family>Two</person_name_family>
                    <person_name_full>Student Two</person_name_full>
                    <lis_result_sourcedid>:_676_1::compai:compair_student_2</lis_result_sourcedid>
                    </member>
                    <member>
                    <user_id>compair_student_3è</user_id>
                    <user_image>http://www.gravatar.com/avatar/4</user_image>
                    <roles>TeachingAssistant</roles>
                    <person_sourcedid>compair_student_3è</person_sourcedid>
                    <person_contact_email_primary>compair_student_3è@test.com</person_contact_email_primary>
                    <person_name_given>Student</person_name_given>
                    <person_name_family>Six</person_name_family>
                    <person_name_full>Student Six</person_name_full>
                    </member>
                    <member>
                    <user_id>compair_instructor_2</user_id>
                    <user_image>http://www.gravatar.com/avatar/5</user_image>
                    <roles>TeachingAssistant</roles>
                    <person_sourcedid>compair_instructor_2</person_sourcedid>
                    <person_contact_email_primary>compair_instructor_2@email.com</person_contact_email_primary>
                    <person_name_given>Instructor</person_name_given>
                    <person_name_family>One</person_name_family>
                    <person_name_full>Instructor One</person_name_full>
                    </member>
                </memberships>
                </message_response>
            """.format(instructor_user_id=lti_user_instructor.user_id, student_user_id=lti_user_student_1.user_id)

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2"])
                if lti_membership.lti_user.user_id == lti_user_instructor.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@test.com")
                elif lti_membership.lti_user.user_id == lti_user_student_1.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_1@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_2@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_3è":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Six")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_3è@test.com")
                elif lti_membership.lti_user.user_id == "compair_instructor_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@email.com")

            # test full name handling in membership response
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>{instructor_user_id}</user_id>
                    <user_image>http://www.gravatar.com/avatar/1</user_image>
                    <roles>Instructor</roles>
                    <person_sourcedid>compair_instructor_2</person_sourcedid>
                    <person_contact_email_primary>compair_instructor_2@test.com</person_contact_email_primary>
                    <person_name_full>Instructor Two</person_name_full>
                    </member>
                    <member>
                    <user_id>{student_user_id}</user_id>
                    <user_image>http://www.gravatar.com/avatar/2</user_image>
                    <roles>Learner</roles>
                    <person_sourcedid>compair_student_1</person_sourcedid>
                    <person_contact_email_primary>compair_student_1@test.com</person_contact_email_primary>
                    <person_name_full>Student One</person_name_full>
                    <lis_result_sourcedid>:_676_1::compai:compair_student_1</lis_result_sourcedid>
                    </member>
                    <member>
                    <user_id>compair_student_2</user_id>
                    <user_image>http://www.gravatar.com/avatar/3</user_image>
                    <roles>Learner</roles>
                    <person_sourcedid>compair_student_2</person_sourcedid>
                    <person_contact_email_primary>compair_student_2@test.com</person_contact_email_primary>
                    <person_name_full>Student Two</person_name_full>
                    <lis_result_sourcedid>:_676_1::compai:compair_student_2</lis_result_sourcedid>
                    </member>
                    <member>
                    <user_id>compair_student_3è</user_id>
                    <user_image>http://www.gravatar.com/avatar/4</user_image>
                    <roles>TeachingAssistant</roles>
                    <person_sourcedid>compair_student_3è</person_sourcedid>
                    <person_contact_email_primary>compair_student_3è@test.com</person_contact_email_primary>
                    <person_name_full>Student Six</person_name_full>
                    </member>
                    <member>
                    <user_id>compair_instructor_2</user_id>
                    <user_image>http://www.gravatar.com/avatar/5</user_image>
                    <roles>TeachingAssistant</roles>
                    <person_sourcedid>compair_instructor_2</person_sourcedid>
                    <person_contact_email_primary>compair_instructor_2@email.com</person_contact_email_primary>
                    <person_name_full>Instructor One</person_name_full>
                    </member>
                </memberships>
                </message_response>
            """.format(instructor_user_id=lti_user_instructor.user_id, student_user_id=lti_user_student_1.user_id)

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2"])
                if lti_membership.lti_user.user_id == lti_user_instructor.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@test.com")
                elif lti_membership.lti_user.user_id == lti_user_student_1.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_1@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_2@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_3è":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Six")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_3è@test.com")
                elif lti_membership.lti_user.user_id == "compair_instructor_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@email.com")

            # test minimual membership response
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>{instructor_user_id}</user_id>
                    <roles>Instructor</roles>
                    </member>
                    <member>
                    <user_id>{student_user_id}</user_id>
                    <roles>Learner</roles>
                    </member>
                    <member>
                    <user_id>compair_student_2</user_id>
                    <roles>Learner</roles>
                    </member>
                    <member>
                    <user_id>compair_student_3è</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                    <member>
                    <user_id>compair_instructor_2</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                </memberships>
                </message_response>
            """.format(instructor_user_id=lti_user_instructor.user_id, student_user_id=lti_user_student_1.user_id)

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members (all old users besides instructor should be dropped)
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2"])
                self.assertIsNone(lti_membership.lti_user.lis_person_name_given)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_family)
                self.assertIsNone(lti_membership.lti_user.lis_person_contact_email_primary)

            # test ensure current user is not unenrolled from course on membership fetch
            mocked_post_membership_request.return_value = """
                <message_response>
                <lti_message_type>basic-lis-readmembershipsforcontext</lti_message_type>
                <statusinfo>
                    <codemajor>Success</codemajor>
                    <severity>Status</severity>
                    <codeminor>fullsuccess</codeminor>
                    <description>Roster retrieved</description>
                </statusinfo>
                <memberships>
                    <member>
                    <user_id>{student_user_id}</user_id>
                    <roles>Learner</roles>
                    </member>
                </memberships>
                </message_response>
            """.format(student_user_id=lti_user_student_1.user_id)

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 1 members (+ current user instructor)
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 1)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, lti_user_student_1.user_id)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_given)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_family)
                self.assertIsNone(lti_membership.lti_user.lis_person_contact_email_primary)

        with self.login(self.data.get_unauthorized_instructor().username):
            course_2 = self.data.secondary_course
            url_2 = '/api/lti/course/'+course_2.uuid+'/membership'

            # requires course linked to at least one lti context
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "Sorry, your LTI link settings have no course context. Please edit your LTI link settings and try linking again.")

            # requires at least one linked lti context to support membership
            lti_context_2 = self.lti_data.create_context(lti_consumer, compair_course=course_2)
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "The LTI link does not support the membership extension. Please edit your LTI link settings or contact your system administrator and try again.")


    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._get_membership_request')
    def test_lti_membership_for_consumer_with_membership_service(self, mocked_get_membership_request):
        course = self.data.get_course()
        instructor = self.data.get_authorized_instructor()
        student_1 = self.data.authorized_student
        student_2 = self.data.create_normal_user()
        self.data.enrol_student(student_2, course)

        current_user_ids = [user_course.user_id for user_course in course.user_courses]

        url = '/api/lti/course/'+course.uuid+'/membership'

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(
            lti_consumer,
            compair_course_id=course.id,
            custom_context_memberships_url="https://mockmembershipurl.com"
        )

        lti_user_instructor = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_user_student_1 = self.lti_data.create_user(lti_consumer, SystemRole.student, student_1)

        with self.login(self.data.get_authorized_instructor().username):
            # test empty membership response

            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "@id":None,
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[]
                    },
                    "@id":None,
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }
            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "The membership service did not return any users. Please check your LTI course and try again.")

            # test full membership response
            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "@id":None,
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Instructor"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Instructor Two",
                                    "img":"http://www.gravatar.com/avatar/1",
                                    "email":"compair_instructor_2@test.com",
                                    "familyName":"Two",
                                    "givenName":"Instructor",
                                    "resultSourcedId":"compair_instructor_2",
                                    "sourcedId":None,
                                    "userId":lti_user_instructor.user_id
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student One",
                                    "img":"http://www.gravatar.com/avatar/2",
                                    "email":"compair_student_1@test.com",
                                    "familyName":"One",
                                    "givenName":"Student",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_1",
                                    "userId":lti_user_student_1.user_id
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student Two",
                                    "img":"http://www.gravatar.com/avatar/3",
                                    "email":"compair_student_2@test.com",
                                    "familyName":"Two",
                                    "givenName":"Student",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_2",
                                    "userId":"compair_student_2"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/TeachingAssistant"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student Six",
                                    "img":"http://www.gravatar.com/avatar/4",
                                    "email":"compair_student_3è@test.com",
                                    "familyName":"Six",
                                    "givenName":"Student",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_3è",
                                    "userId":"compair_student_3è"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/TeachingAssistant"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Instructor One",
                                    "img":"http://www.gravatar.com/avatar/5",
                                    "email":"compair_instructor_2@email.com",
                                    "familyName":"One",
                                    "givenName":"Instructor",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_instructor_2",
                                    "userId":"compair_instructor_2"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Inactive",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student One Hundred",
                                    "img":"http://www.gravatar.com/avatar/6",
                                    "email":"compair_student_100@test.com",
                                    "familyName":"One Hundred",
                                    "givenName":"Student",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_100",
                                    "userId":"compair_student_100"
                                }
                            }
                        ]
                    },
                    "@id":None,
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2", "compair_student_100"])

                if lti_membership.lti_user.user_id == lti_user_instructor.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@test.com")
                elif lti_membership.lti_user.user_id == lti_user_student_1.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_1@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_2@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_3è":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Six")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_3è@test.com")
                elif lti_membership.lti_user.user_id == "compair_instructor_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@email.com")
                elif lti_membership.lti_user.user_id == "compair_student_100":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One Hundred")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_100@test.com")

            # test full name handling
            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "@id":None,
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Instructor"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Instructor Two",
                                    "img":"http://www.gravatar.com/avatar/1",
                                    "email":"compair_instructor_2@test.com",
                                    "resultSourcedId":"compair_instructor_2",
                                    "sourcedId":None,
                                    "userId":lti_user_instructor.user_id
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student One",
                                    "img":"http://www.gravatar.com/avatar/2",
                                    "email":"compair_student_1@test.com",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_1",
                                    "userId":lti_user_student_1.user_id
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student Two",
                                    "img":"http://www.gravatar.com/avatar/3",
                                    "email":"compair_student_2@test.com",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_2",
                                    "userId":"compair_student_2"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/TeachingAssistant"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student Six",
                                    "img":"http://www.gravatar.com/avatar/4",
                                    "email":"compair_student_3è@test.com",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_3è",
                                    "userId":"compair_student_3è"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/TeachingAssistant"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Instructor One",
                                    "img":"http://www.gravatar.com/avatar/5",
                                    "email":"compair_instructor_2@email.com",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_instructor_2",
                                    "userId":"compair_instructor_2"
                                }
                            },
                            {
                                "@id":None,
                                "status":"Inactive",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "@id":None,
                                    "name":"Student One Hundred",
                                    "img":"http://www.gravatar.com/avatar/6",
                                    "email":"compair_student_100@test.com",
                                    "resultSourcedId":None,
                                    "sourcedId":"compair_student_100",
                                    "userId":"compair_student_100"
                                }
                            }
                        ]
                    },
                    "@id":None,
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2", "compair_student_100"])

                if lti_membership.lti_user.user_id == lti_user_instructor.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@test.com")
                elif lti_membership.lti_user.user_id == lti_user_student_1.user_id:
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_1@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Two")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_2@test.com")
                elif lti_membership.lti_user.user_id == "compair_student_3è":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Six")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_3è@test.com")
                elif lti_membership.lti_user.user_id == "compair_instructor_2":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Instructor")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "One")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_instructor_2@email.com")
                elif lti_membership.lti_user.user_id == "compair_student_100":
                    self.assertEqual(lti_membership.lti_user.lis_person_name_given, "Student One")
                    self.assertEqual(lti_membership.lti_user.lis_person_name_family, "Hundred")
                    self.assertEqual(lti_membership.lti_user.lis_person_contact_email_primary, "compair_student_100@test.com")

            # test minimual membership response
            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[
                            {
                            "status":"Active",
                            "role":[
                                "urn:lti:role:ims/lis/Instructor"
                            ],
                            "member":{
                                "userId":lti_user_instructor.user_id
                            }
                            },
                            {
                            "status":"Active",
                            "role":[
                                "urn:lti:role:ims/lis/Learner"
                            ],
                            "member":{
                                "userId":lti_user_student_1.user_id
                            }
                            },
                            {
                            "status":"Active",
                            "role":[
                                "urn:lti:role:ims/lis/Learner"
                            ],
                            "member":{
                                "userId":"compair_student_2"
                            }
                            },
                            {
                            "status":"Active",
                            "role":[
                                "urn:lti:role:ims/lis/TeachingAssistant"
                            ],
                            "member":{
                                "userId":"compair_student_3è"
                            }
                            },
                            {
                            "status":"Active",
                            "role":[
                                "urn:lti:role:ims/lis/TeachingAssistant"
                            ],
                            "member":{
                                "userId":"compair_instructor_2"
                            }
                            },
                            {
                            "status":"Inactive",
                            "role":[
                                "urn:lti:role:ims/lis/Learner"
                            ],
                            "member":{
                                "userId":"compair_student_100"
                            }
                            }
                        ]
                    },
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 5 members (all old users besides instructor should be dropped)
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user_instructor.user_id, lti_user_student_1.user_id,
                    "compair_student_2", "compair_student_3è", "compair_instructor_2"])
                self.assertIsNone(lti_membership.lti_user.lis_person_name_given)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_family)
                self.assertIsNone(lti_membership.lti_user.lis_person_contact_email_primary)


            # test ensure current user is not unenrolled from course on membership fetch
            mocked_get_membership_request.return_value = {
                "@id":None,
                "@type":"Page",
                "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                "differences":None,
                "nextPage":None,
                "pageOf":{
                    "membershipPredicate":"http://www.w3.org/ns/org#membership",
                    "membershipSubject":{
                        "name":"Test Course",
                        "@type":"Context",
                        "contextId":"4dde05e8ca1973bcca9bffc13e1548820eee93a3",
                        "membership":[
                            {
                                "status":"Active",
                                "role":[
                                    "urn:lti:role:ims/lis/Learner"
                                ],
                                "member":{
                                    "userId":lti_user_student_1.user_id
                                }
                            }
                        ]
                    },
                    "@context":"http://purl.imsglobal.org/ctx/lis/v2/MembershipContainer",
                    "@type":"LISMembershipContainer"
                }
            }

            rv = self.client.post(url, data={}, content_type='application/json')
            self.assert200(rv)

            # 1 members (+ current user instructor)
            # verify user course roles
            for user_course in course.user_courses:
                if user_course.user_id == instructor.id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                elif user_course.user_id == student_1.id:
                    self.assertEqual(user_course.course_role, CourseRole.student)
                else:
                    #everyone else should be dropped
                    self.assertEqual(user_course.course_role, CourseRole.dropped)

            # verify membership table
            lti_memberships = LTIMembership.query \
                .filter_by(compair_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 1)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, lti_user_student_1.user_id)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_given)
                self.assertIsNone(lti_membership.lti_user.lis_person_name_family)
                self.assertIsNone(lti_membership.lti_user.lis_person_contact_email_primary)
