import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership,  \
    LTIResourceLink, LTIUserResourceLink
from acj.core import db
from oauthlib.common import generate_nonce, generate_timestamp

class LTILaunchAPITests(ACJAPITestCase):
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

            # invalid request - no user id
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=None, context_id=lti_context_id, roles=lti_role) as rv:
                self.assert400(rv)

            # valid request - user without account
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/static/index.html#/lti')

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
            lti_user.acj_user = user
            db.session.commit()

            # valid request - user with account and request missing context_id
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=None, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/static/index.html#/')

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertIsNone(sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # first request for user, oauth_create_user_link should be True
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))


            # valid request - user with account but no course
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:

                if course_role == CourseRole.instructor:
                    self.assertRedirects(rv, '/static/index.html#/lti')
                else:
                    #TODO: confirm message sent
                    self.assertRedirects(rv, '/static/index.html#/')

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

            # link course - user should be auto enrolled into course
            course = self.data.create_course()
            lti_context.acj_course_id = course.id
            db.session.commit()

            # valid request - user with account and course linked (no assignment)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/static/index.html#/course/'+str(course.id))

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

            # create assignment - should be automatically linked when custom_assignment is set
            assignment = self.data.create_assignment_in_answer_period(course, self.data.get_authorized_instructor())

            # valid request - user with account and course linked (with assignment)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_id=assignment.id, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/static/index.html#/course/'+str(course.id)+'/assignment/'+str(assignment.id))

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

            # ensure replay attacks do not work for lti launch requests
            nonce = generate_nonce()
            timestamp = generate_timestamp()
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_id=assignment.id, follow_redirects=False,
                    nonce=nonce, timestamp=timestamp) as rv:
                self.assertRedirects(rv, '/static/index.html#/course/'+str(course.id)+'/assignment/'+str(assignment.id))

            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_id=assignment.id, follow_redirects=False,
                    nonce=nonce, timestamp=timestamp) as rv:
                self.assert400(rv)

    def test_lti_course_link(self):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        url = '/api/lti/course/'+str(course.id)+'/link'

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
            self.assert404(rv)

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
        self.assert404(rv)

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


    @mock.patch('acj.models.lti.lti_membership.LTIMembership._send_membership_request')
    def test_lti_course_link_with_membership(self, mocked_send_membership_request):
        instructor = self.data.get_authorized_instructor()
        course = self.data.get_course()
        current_user_ids = [user_course.user_id for user_course in course.user_courses]

        url = '/api/lti/course/'+str(course.id)+'/link'

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(lti_consumer)
        lti_user = self.lti_data.create_user(lti_consumer, SystemRole.instructor, instructor)
        lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
        lti_user_resource_link = self.lti_data.create_user_resource_link(
            lti_user, lti_resource_link, CourseRole.instructor)

        # test invalid request
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mock_membership_url.com") as rv:
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
            self.assertIn('warning', rv.json)
            # membership should not change
            for user_course in course.user_courses:
                self.assertIn(user_course.user_id, current_user_ids)

        # test empty membership response
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mock_membership_url.com") as rv:
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
            self.assertIn('warning', rv.json)
            # membership should not change
            for user_course in course.user_courses:
                self.assertIn(user_course.user_id, current_user_ids)


        # test successful membership response (minimual returned data)
        with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                user_id=lti_user.user_id, context_id=lti_context.context_id, roles="Instructor",
                ext_ims_lis_memberships_id="123", ext_ims_lis_memberships_url="https://mock_membership_url.com") as rv:
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
            self.assertNotIn('warning', rv.json)
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
                .filter_by(acj_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 5)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, [lti_user.user_id, "compair_student_1", "compair_student_2",
                    "compair_student_3", "compair_instructor_2"])

    @mock.patch('acj.models.lti.lti_membership.LTIMembership._send_membership_request')
    def test_lti_course_link_with_membership(self, mocked_send_membership_request):
        course = self.data.get_course()
        instructor = self.data.get_authorized_instructor()
        student_1 = self.data.authorized_student
        student_2 = self.data.create_normal_user()
        self.data.enrol_student(student_2, course)

        current_user_ids = [user_course.user_id for user_course in course.user_courses]

        url = '/api/lti/course/'+str(course.id)+'/membership'

        lti_consumer = self.lti_data.lti_consumer
        lti_context = self.lti_data.create_context(
            lti_consumer,
            acj_course_id=course.id,
            ext_ims_lis_memberships_id="123",
            ext_ims_lis_memberships_url="https://mock_membership_url.com"
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
            self.assertEqual(rv.json['error'], "LTI membership request was invalid. Please relaunch the ComPAIR course from the LTI consumer and try again")

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
            self.assertEqual(rv.json['error'], "LTI membership service did not return any users")

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
                .filter_by(acj_course_id=course.id) \
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
                .filter_by(acj_course_id=course.id) \
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
                .filter_by(acj_course_id=course.id) \
                .all()

            self.assertEqual(len(lti_memberships), 1)
            for lti_membership in lti_memberships:
                self.assertIn(lti_membership.lti_user.user_id, lti_user_student_1.user_id)

        with self.login(self.data.get_unauthorized_instructor().username):
            course_2 = self.data.secondary_course
            url_2 = '/api/lti/course/'+str(course_2.id)+'/membership'

            # requires course linked to at least one lti context
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['error'], "Course not linked to lti context")

            # requires at least one linked lti context to support membership
            lti_context_2 = self.lti_data.create_context(lti_consumer, acj_course=course_2)
            rv = self.client.post(url_2, data={}, content_type='application/json')
            self.assert400(rv)
            self.assertEqual(rv.json['error'], "LTI membership service is not supported for this course")