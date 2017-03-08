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
from oauthlib.common import generate_token, generate_nonce, generate_timestamp

class LTILaunchAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LTILaunchAPITests, self).setUp()
        self.data = SimpleAssignmentTestData()
        self.lti_data = LTITestData()

    def test_lti_auth(self):
        lti_consumer = self.lti_data.get_consumer()
        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
        }

        for lti_role, (system_role, course_role) in roles.items():
            lti_resource_link_id = self.lti_data.generate_resource_link_id()
            lti_user_id = self.lti_data.generate_user_id()
            lti_context_id = self.lti_data.generate_context_id()

            # invalid request - invalid lti_consumer
            invalid_lti_consumer = LTIConsumer(
                oauth_consumer_key=generate_token(),
                oauth_consumer_secret=generate_token()
            )
            with self.lti_launch(invalid_lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role) as rv:
                self.assert400(rv)

            # invalid request - no user id
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=None, context_id=lti_context_id, roles=lti_role) as rv:
                self.assert400(rv)

            # test LTI auth disabled
            self.app.config['LTI_LOGIN_ENABLED'] = False
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assert403(rv)
            self.app.config['LTI_LOGIN_ENABLED'] = True

            # valid request - user without account
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

            lti_resource_link = LTIResourceLink.query.all()[-1]
            lti_user = LTIUser.query.all()[-1]
            lti_context = LTIContext.query.all()[-1]
            lti_user_resource_link = LTIUserResourceLink.query.all()[-1]

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # first request for user, oauth_create_user_link should be True
                self.assertTrue(sess.get('oauth_create_user_link'))

                # check that user is not logged in
                self.assertIsNone(sess.get('user_id'))

            # link user account
            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            db.session.commit()

            # valid request - user with account and request missing context_id
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=None, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/')

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertIsNone(sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, oauth_create_user_link should be None
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))


            # valid request - user with account but no course
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, oauth_create_user_link should be None
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))

            # link course - user should be auto enrolled into course
            course = self.data.create_course()
            lti_context.compair_course_id = course.id
            db.session.commit()

            # valid request - user with account and course linked (no assignment)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # first request for user, oauth_create_user_link should be True
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))

            # verify enrollment
            user_course = UserCourse.query \
                .filter_by(
                    user_id=user.id,
                    course_id=course.id,
                    course_role=course_role
                ) \
                .one_or_none()
            self.assertIsNotNone(user_course)

            # valid request - user with account and course linked (assignment doesn't exist in db)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid="999", follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, oauth_create_user_link should be None
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))

            # verify lti_resource_link does not retain the invalid assignment_id
            self.assertIsNone(lti_resource_link.compair_assignment_id)

            # create assignment - should be automatically linked when custom_assignment is set
            assignment = self.data.create_assignment_in_answer_period(course, self.data.get_authorized_instructor())

            # valid request - user with account and course linked (with assignment)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, oauth_create_user_link should be None
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))

            # verify lti_resource_link does not retain the invalid assignment_id
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # ensure replay attacks do not work for lti launch requests
            nonce = generate_nonce()
            timestamp = generate_timestamp()
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    nonce=nonce, timestamp=timestamp) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    nonce=nonce, timestamp=timestamp) as rv:
                self.assert400(rv)

    def test_lti_status(self):
        url = '/api/lti/status'

        # test lti session required
        rv = self.client.get(url, data={}, content_type='application/json')
        self.assert200(rv)
        status = rv.json['status']
        self.assertFalse(status['valid'])

        lti_consumer = self.lti_data.get_consumer()
        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
        }

        for lti_role, (system_role, course_role) in roles.items():
            # test new user (no compair user yet)
            lti_context = self.lti_data.create_context(lti_consumer)
            lti_user = self.lti_data.create_user(lti_consumer, system_role)
            lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
            lti_user_resource_link = self.lti_data.create_user_resource_link(
                lti_user, lti_resource_link, CourseRole.instructor)

            # setup lti session with no context id
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=None, roles=lti_role) as rv:
                self.assert200(rv)

            # get status
            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['user']['exists'])
            self.assertEqual(status['user']['firstname'], lti_user.lis_person_name_given)
            self.assertEqual(status['user']['lastname'], lti_user.lis_person_name_family)
            self.assertIsNotNone(status['user']['displayname'])
            self.assertEqual(status['user']['email'], lti_user.lis_person_contact_email_primary)
            self.assertEqual(status['user']['system_role'], system_role.value)

            self.assertFalse(status['course']['exists'])
            self.assertIsNone(status['course']['id'])
            self.assertIsNone(status['course']['name'])
            self.assertEqual(status['course']['course_role'], course_role.value)

            self.assertFalse(status['assignment']['exists'])
            self.assertIsNone(status['assignment']['id'])

            # setup lti session with context id
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['course']['exists'])
            self.assertIsNone(status['course']['id'])
            self.assertEqual(status['course']['name'], lti_context.context_title)
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup lti session with custom assignment id
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['course']['exists'])
            self.assertIsNone(status['course']['id'])
            self.assertEqual(status['course']['name'], lti_context.context_title)
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup with existing user
            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            db.session.commit()

            # setup lti session with existing user
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['user']['exists'])
            self.assertEqual(status['user']['firstname'], lti_user.lis_person_name_given)
            self.assertEqual(status['user']['lastname'], lti_user.lis_person_name_family)
            self.assertIsNotNone(status['user']['displayname'])
            self.assertEqual(status['user']['email'], lti_user.lis_person_contact_email_primary)
            self.assertEqual(status['user']['system_role'], system_role.value)

            # setup with existing course
            course = self.data.create_course()
            lti_context.compair_course_id = course.id
            db.session.commit()

            # setup lti session with existing course
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['course']['exists'])
            self.assertEqual(status['course']['id'], course.uuid)
            self.assertEqual(status['course']['name'], lti_context.context_title)
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup lti session with existing course
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['course']['exists'])
            self.assertEqual(status['course']['id'], course.uuid)
            self.assertEqual(status['course']['name'], lti_context.context_title)
            self.assertEqual(status['course']['course_role'], course_role.value)

            # with no custom assignment param
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['assignment']['exists'])
            self.assertIsNone(status['assignment']['id'])

            # with custom assignment param that doesn't exist
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    assignment_uuid="999") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['assignment']['exists'])
            self.assertIsNone(status['assignment']['id'])

            # with custom assignment param that exist
            instructor = self.data.create_instructor()
            self.data.enrol_instructor(instructor, course)
            assignment = self.data.create_assignment_in_answer_period(course, instructor)

            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid) as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['assignment']['exists'])
            self.assertEqual(status['assignment']['id'], assignment.uuid)

    def test_lti_course_link(self):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        url = '/api/lti/course/'+course.uuid+'/link'

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
            self.assertEqual(str(instructor.id), sess.get('user_id'))
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
            self.assertEqual(str(instructor.id), sess.get('user_id'))
            self.assertEqual(lti_context.id, sess.get('lti_context'))

        # link course
        rv = self.client.post(url, data={}, content_type='application/json')
        self.assert200(rv)


    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._send_membership_request')
    def test_lti_course_link_with_membership(self, mocked_send_membership_request):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        current_users = [(user_course.user_id, user_course.course_role) for user_course in course.user_courses]

        url = '/api/lti/course/'+course.uuid+'/link'

        lti_consumer = self.lti_data.lti_consumer
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

            mocked_send_membership_request.return_value = """
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

            mocked_send_membership_request.return_value = """
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

            mocked_send_membership_request.return_value = """
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
                    <user_id>compair_student_3</user_id>
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
                    "compair_student_3", "compair_instructor_2"])

    @mock.patch('compair.models.lti_models.lti_membership.LTIMembership._send_membership_request')
    def test_lti_membership(self, mocked_send_membership_request):
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
            mocked_send_membership_request.return_value = """
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
            mocked_send_membership_request.return_value = """
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
            mocked_send_membership_request.return_value = """
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
                    <user_id>compair_student_3</user_id>
                    <user_image>http://www.gravatar.com/avatar/4</user_image>
                    <roles>TeachingAssistant</roles>
                    <person_sourcedid>compair_student_3</person_sourcedid>
                    <person_contact_email_primary>compair_student_3@test.com</person_contact_email_primary>
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
            """.format(instructor_user_id=lti_user_instructor.user_id,
                student_user_id=lti_user_student_1.user_id)

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
                    "compair_student_2", "compair_student_3", "compair_instructor_2"])

            # test minimual membership response
            mocked_send_membership_request.return_value = """
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
                    <user_id>compair_student_3</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                    <member>
                    <user_id>compair_instructor_2</user_id>
                    <roles>TeachingAssistant</roles>
                    </member>
                </memberships>
                </message_response>
            """.format(instructor_user_id=lti_user_instructor.user_id,
                student_user_id=lti_user_student_1.user_id)

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
                    "compair_student_2", "compair_student_3", "compair_instructor_2"])


            # test ensure current user is not unenrolled from course on membership fetch
            mocked_send_membership_request.return_value = """
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

        with self.login(self.data.get_unauthorized_instructor().username):
            course_2 = self.data.secondary_course
            url_2 = '/api/lti/course/'+course_2.uuid+'/membership'

            # requires course linked to at least one lti context
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "Your LTI link settings has no course context. Please edit your LTI link settings and try again.")

            # requires at least one linked lti context to support membership
            lti_context_2 = self.lti_data.create_context(lti_consumer, compair_course=course_2)
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['title'], "Membership Not Updated")
            self.assertEqual(rv.json['message'],
                "The LTI link does not support the membership extension. Please edit your LTI link settings or contact your system administrator and try again.")

    def test_cas_auth_via_lti_launch(self):
        url = '/api/cas/auth?ticket=mock_ticket'
        auth_data = ThirdPartyAuthTestData()

        lti_consumer = self.lti_data.get_consumer()
        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
        }

        for lti_role, (system_role, course_role) in roles.items():
            lti_context = self.lti_data.create_context(lti_consumer)
            lti_user = self.lti_data.create_user(lti_consumer, system_role)
            lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
            lti_user_resource_link = self.lti_data.create_user_resource_link(
                lti_user, lti_resource_link, CourseRole.instructor)

            # linked third party user (no context id)
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=None, roles=lti_role) as rv:
                self.assert200(rv)

            user = self.data.create_user(system_role)
            third_party_user = auth_data.create_third_party_user(user=user)

            with self.cas_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that oauth_create_user_link is None
                    self.assertIsNone(sess.get('oauth_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('user_id'))

                    self.assertIsNone(sess.get('CAS_CREATE'))
                    self.assertIsNone(sess.get('CAS_UNIQUE_IDENTIFIER'))

                # check that lti_user is now linked
                self.assertEqual(lti_user.compair_user_id, user.id)

                # create fresh lti_user
                lti_user = self.lti_data.create_user(lti_consumer, system_role)

                course = self.data.create_course()
                lti_context.compair_course_id = course.id
                db.session.commit()

                # linked third party user (with linked context id)
                with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                        user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role) as rv:
                    self.assert200(rv)

            user = self.data.create_user(system_role)
            third_party_user = auth_data.create_third_party_user(user=user)

            with self.cas_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that oauth_create_user_link is None
                    self.assertIsNone(sess.get('oauth_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('user_id'))

                    self.assertIsNone(sess.get('CAS_CREATE'))
                    self.assertIsNone(sess.get('CAS_UNIQUE_IDENTIFIER'))

                # check that lti_user is now linked
                self.assertEqual(lti_user.compair_user_id, user.id)

                # verify enrollment
                user_course = UserCourse.query \
                    .filter_by(
                        user_id=user.id,
                        course_id=course.id,
                        course_role=course_role
                    ) \
                    .one_or_none()
                self.assertIsNotNone(user_course)
