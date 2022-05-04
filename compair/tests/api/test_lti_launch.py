# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIMembership, ThirdPartyUser, \
    LTIResourceLink, LTIUserResourceLink, ThirdPartyType
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
        lti_resource_link_id = self.lti_data.generate_resource_link_id()
        lti_user_id = self.lti_data.generate_user_id()
        lti_context_id = self.lti_data.generate_context_id()

        # invalid request - invalid lti_consumer
        invalid_lti_consumer = LTIConsumer(
            oauth_consumer_key=generate_token(),
            oauth_consumer_secret=generate_token()
        )
        with self.lti_launch(invalid_lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id) as rv:
            self.assert400(rv)

        # invalid request - bad oauth signature
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                oauth_signature="FFGTSFanGnwNZclLi5PA70SaGkU=",
                invalid_launch=True) as rv:
            self.assert400(rv, "Invalid Request: There is something wrong with the LTI tool consumer's request.")

        # invalid request - no resource_link_id
        with self.lti_launch(lti_consumer, None,
                user_id=lti_user_id, context_id=lti_context_id,
                invalid_launch=True) as rv:
            self.assert400(rv, "ComPAIR requires the LTI tool consumer to provide a resource link id.")

        # invalid request - no resource_link_id (with return url)
        with self.lti_launch(lti_consumer, None,
                user_id=lti_user_id, context_id=lti_context_id,
                invalid_launch=True,
                launch_presentation_return_url="http://test.url",
                follow_redirects=False) as rv:
            self.assertRedirects(rv, 'http://test.url?lti_errormsg=ComPAIR+requires+the+LTI+tool+consumer+to+provide+a+resource+link+id.')

        # invalid request - missing lti version
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lti_version=None, invalid_launch=True) as rv:
            self.assert400(rv, "Invalid Request: There is something wrong with the LTI tool consumer's request.")

        # invalid request - invalid lti versions
        invalid_lti_versions = ["LTI-1p1", "LTI-1", "LTI-1.0", "LTI-2p0"]
        for lti_version in invalid_lti_versions:
            # invalid request - invalid lti version
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id,
                    lti_version=lti_version) as rv:
                self.assert400(rv)

            # invalid request - invalid lti version (with return url)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id,
                    lti_version=lti_version,
                    launch_presentation_return_url="http://test.url",
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, 'http://test.url?lti_errormsg=ComPAIR+requires+the+LTI+tool+consumer+to+use+the+LTI+1.0+or+1.1+specification.')

        # valid request - valid lti versions
        valid_lti_versions = ["LTI-1p0"]
        for lti_version in valid_lti_versions:
            # invalid request - invalid lti version
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id,
                    lti_version=lti_version) as rv:
                self.assert200(rv)

        # invalid request - missing lti message type
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lti_message_type=None, invalid_launch=True) as rv:
            self.assert400(rv, "Invalid Request: There is something wrong with the LTI tool consumer's request.")

        # invalid request - invalid lti message type
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lti_message_type="a-basic-lti-launch-request", invalid_launch=True) as rv:
            self.assert400(rv)

        # invalid request - invalid lti message type (with return url)
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                launch_presentation_return_url="http://test.url",
                lti_message_type="a-basic-lti-launch-request", invalid_launch=True,
                follow_redirects=False) as rv:
            self.assertRedirects(rv, 'http://test.url?lti_errormsg=ComPAIR+requires+the+LTI+tool+consumer+to+send+a+basic+lti+launch+request.')

        # invalid request - no user id
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=None, context_id=lti_context_id) as rv:
            self.assert400(rv)

        # invalid request - no user id (with return url)
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=None, context_id=lti_context_id,
                launch_presentation_return_url="http://test.url",
                follow_redirects=False) as rv:
            self.assertRedirects(rv, 'http://test.url?lti_errormsg=ComPAIR+requires+the+LTI+tool+consumer+to+provide+a+user%27s+user_id.')

        # test launch with email but no name
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lis_person_contact_email_primary="test@email.com") as rv:
            self.assert200(rv)
        lti_user = LTIUser.query \
            .filter_by(user_id=lti_user_id) \
            .first()
        self.assertIsNotNone(lti_user)
        self.assertEqual(lti_user.lis_person_contact_email_primary, "test@email.com")
        self.assertIsNone(lti_user.lis_person_name_given)
        self.assertIsNone(lti_user.lis_person_name_family)
        self.assertIsNone(lti_user.lis_person_name_full)

        # test launch with given/family but no full name
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lis_person_name_given="first", lis_person_name_family="last") as rv:
            self.assert200(rv)
        self.assertIsNotNone(lti_user)
        self.assertIsNone(lti_user.lis_person_contact_email_primary)
        self.assertEqual(lti_user.lis_person_name_given, "first")
        self.assertEqual(lti_user.lis_person_name_family, "last")
        self.assertIsNone(lti_user.lis_person_name_full)

        # test launch with full name but no given or family names
        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lis_person_name_full="first middle last") as rv:
            self.assert200(rv)
        self.assertIsNotNone(lti_user)
        self.assertIsNone(lti_user.lis_person_contact_email_primary)
        self.assertEqual(lti_user.lis_person_name_given, "first middle")
        self.assertEqual(lti_user.lis_person_name_family, "last")
        self.assertEqual(lti_user.lis_person_name_full, "first middle last")

        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lis_person_name_full="only") as rv:
            self.assert200(rv)
        self.assertIsNotNone(lti_user)
        self.assertIsNone(lti_user.lis_person_contact_email_primary)
        self.assertEqual(lti_user.lis_person_name_given, "only")
        self.assertEqual(lti_user.lis_person_name_family, "only")
        self.assertEqual(lti_user.lis_person_name_full, "only")

        with self.lti_launch(lti_consumer, lti_resource_link_id,
                user_id=lti_user_id, context_id=lti_context_id,
                lis_person_name_full="first last") as rv:
            self.assert200(rv)
        self.assertIsNotNone(lti_user)
        self.assertIsNone(lti_user.lis_person_contact_email_primary)
        self.assertEqual(lti_user.lis_person_name_given, "first")
        self.assertEqual(lti_user.lis_person_name_family, "last")
        self.assertEqual(lti_user.lis_person_name_full, "first last")

        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Faculty": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Faculty": (SystemRole.instructor, CourseRole.instructor),
            "Staff": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Staff": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "urn:lti:role:ims/lis/Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant),
            "urn:lti:role:ims/lis/TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant),
            "random_role": (SystemRole.student, CourseRole.student),
            "urn:lti:instrole:ims/lis/Alumni": (SystemRole.student, CourseRole.student),
            None: (SystemRole.student, CourseRole.student)
        }

        index = 0
        for lti_role, (system_role, course_role) in roles.items():
            index += 1
            lti_resource_link_id = self.lti_data.generate_resource_link_id()
            lti_user_id = self.lti_data.generate_user_id()
            lti_context_id = self.lti_data.generate_context_id()

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
            self.assertEqual(lti_resource_link.resource_link_id, lti_resource_link_id)
            lti_user = LTIUser.query.all()[-1]
            self.assertEqual(lti_user.user_id, lti_user_id)
            lti_context = LTIContext.query.all()[-1]
            self.assertEqual(lti_context.context_id, lti_context_id)
            lti_user_resource_link = LTIUserResourceLink.query.all()[-1]

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # first request for user, lti_create_user_link should be True
                self.assertTrue(sess.get('lti_create_user_link'))

                # check that user is not logged in
                self.assertIsNone(sess.get('_user_id'))

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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))


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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

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

                # first request for user, lti_create_user_link should be True
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            # verify lti_resource_link does not retain the invalid assignment_id
            self.assertIsNone(lti_resource_link.compair_assignment_id)

            # will not link assignment from another course
            course_invalid = self.data.create_course()
            assignment_invalid = self.data.create_assignment_in_answer_period(course_invalid, self.data.get_authorized_instructor())

            # valid request - user with account and course linked (with assignment)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment_invalid.uuid, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

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

            # student_number_param ------
            lti_consumer.student_number_param = "custom_student_number"
            lti_consumer.custom_param_regex_sanitizer = "^\\$.+$"
            db.session.commit()

            # student_number_param parameter is missing
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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            self.assertIsNone(lti_user.student_number)
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # student_number_param parameter is present
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, custom_student_number="1234567"+str(index),
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            self.assertEqual(lti_user.student_number, "1234567"+str(index))
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # student_number_param parameter is sanitized
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, custom_student_number="$1234567"+str(index),
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            self.assertIsNone(lti_user.student_number)
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            lti_consumer.student_number_param = None
            lti_consumer.custom_param_regex_sanitizer = None
            db.session.commit()
            # done student_number_param ------

            # global_unique_identifier_param ------
            lti_consumer.global_unique_identifier_param = "custom_puid"
            lti_consumer.custom_param_regex_sanitizer = "^\\$.+$"
            db.session.commit()

            # global_unique_identifier_param parameter is missing
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

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            lti_user = LTIUser.query.all()[-1]
            self.assertIsNone(lti_user.global_unique_identifier)
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # global_unique_identifier_param parameter is present but sanitized
            custom_puid = "$puid123456789_"+str(lti_role)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    custom_puid=custom_puid) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            lti_user = LTIUser.query.all()[-1]
            self.assertIsNone(lti_user.global_unique_identifier)
            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # global_unique_identifier_param parameter is present (new user)
            custom_puid = "puid123456789_"+str(lti_role)
            lti_user_id = self.lti_data.generate_user_id()
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    custom_puid=custom_puid) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            lti_user = LTIUser.query.all()[-1]
            self.assertEqual(lti_user.global_unique_identifier, custom_puid)
            lti_user_resource_link = LTIUserResourceLink.query.all()[-1]
            user = User.query.all()[-1]
            self.assertEqual(user.global_unique_identifier, custom_puid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user exists
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(sess.get('_user_id'), str(lti_user.compair_user_id))

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # global_unique_identifier_param parameter is present (existing user linked)
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    custom_puid=custom_puid) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # global_unique_identifier_param parameter is present (existing user unlinked)
            custom_puid = "puid123456789_"+str(lti_role)+"_2"
            user = self.data.create_user(system_role)
            user.global_unique_identifier = custom_puid
            lti_user_id = self.lti_data.generate_user_id()

            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    custom_puid=custom_puid) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid+'/assignment/'+assignment.uuid)

            lti_user = LTIUser.query.all()[-1]
            self.assertEqual(lti_user.user_id, lti_user_id)
            lti_user_resource_link = LTIUserResourceLink.query.all()[-1]

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user already exists, lti_create_user_link should be None
                self.assertIsNone(sess.get('lti_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('_user_id'))

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            lti_consumer.global_unique_identifier_param = None
            lti_consumer.custom_param_regex_sanitizer = None
            db.session.commit()
            # done global_unique_identifier_param ------

        # test automatic upgrading of system role for existing accounts
        for lti_role, (system_role, course_role) in roles.items():
            for compair_system_role in [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]:
                lti_context = self.lti_data.create_context(lti_consumer)
                lti_user = self.lti_data.create_user(lti_consumer, system_role)
                lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
                lti_user_resource_link = self.lti_data.create_user_resource_link(
                    lti_user, lti_resource_link, CourseRole.instructor)

                user = self.data.create_user(compair_system_role)
                lti_user.compair_user = user
                course = self.data.create_course()
                lti_context.compair_course = course

                db.session.commit()

                # valid request - user with account and existing context_id
                with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                        user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                        follow_redirects=False) as rv:
                    self.assertRedirects(rv, '/app/#/course/'+course.uuid)

                # compair user system role will upgrade
                if compair_system_role == SystemRole.student:
                    if system_role == SystemRole.sys_admin:
                        self.assertEqual(user.system_role, SystemRole.sys_admin)
                    elif system_role == SystemRole.instructor:
                        self.assertEqual(user.system_role, SystemRole.instructor)
                    else:
                        self.assertEqual(user.system_role, SystemRole.student)
                elif compair_system_role == SystemRole.instructor:
                    if system_role == SystemRole.sys_admin:
                        self.assertEqual(user.system_role, SystemRole.sys_admin)
                    else:
                        self.assertEqual(user.system_role, SystemRole.instructor)
                elif compair_system_role == SystemRole.sys_admin:
                    self.assertEqual(user.system_role, SystemRole.sys_admin)


        # test automatic overwrite of user profile for students
        for lti_role, (system_role, course_role) in roles.items():
            lti_consumer.student_number_param = None
            lti_context = self.lti_data.create_context(lti_consumer)
            lti_user = self.lti_data.create_user(lti_consumer, system_role)
            lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
            lti_user_resource_link = self.lti_data.create_user_resource_link(
                lti_user, lti_resource_link, CourseRole.instructor)

            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            course = self.data.create_course()
            lti_context.compair_course = course

            original_firstname = user.firstname
            original_lastname = user.lastname
            original_email = user.email
            original_student_number = user.student_number
            new_student_number = original_student_number+"123" if user.student_number else None
            db.session.commit()

            # check that values are not overwritten
            self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = True
            self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = True
            self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = True
            self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = True

            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="f_student", lis_person_name_family="l_student",
                    lis_person_contact_email_primary="student@email.com",
                    custom_student_number=new_student_number,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            self.assertEqual(user.firstname, original_firstname)
            self.assertEqual(user.lastname, original_lastname)
            self.assertEqual(user.email, original_email)
            if system_role == SystemRole.student:
                self.assertEqual(user.student_number, original_student_number)
            else:
                self.assertIsNone(user.student_number)

            # check that values are overwritten for students (except for student number as student_number_param is not set)
            self.app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_NAME'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'] = False
            self.app.config['ALLOW_STUDENT_CHANGE_EMAIL'] = False

            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="f_student", lis_person_name_family="l_student",
                    lis_person_contact_email_primary="student@email.com",
                    custom_student_number=new_student_number,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            if system_role == SystemRole.student:
                self.assertEqual(user.firstname, "f_student")
                self.assertEqual(user.lastname, "l_student")
                self.assertEqual(user.email, "student@email.com")
                self.assertEqual(user.student_number, original_student_number)
            else:
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertIsNone(user.student_number)

            # check that values are overwritten for students
            lti_consumer.student_number_param = "custom_student_number"
            db.session.commit()

            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="f_student", lis_person_name_family="l_student",
                    lis_person_contact_email_primary="student@email.com",
                    custom_student_number=new_student_number,
                    follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/course/'+course.uuid)

            if system_role == SystemRole.student:
                self.assertEqual(user.firstname, "f_student")
                self.assertEqual(user.lastname, "l_student")
                self.assertEqual(user.email, "student@email.com")
                self.assertEqual(user.student_number, new_student_number)
            else:
                self.assertEqual(user.firstname, original_firstname)
                self.assertEqual(user.lastname, original_lastname)
                self.assertEqual(user.email, original_email)
                self.assertIsNone(user.student_number)

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
            "urn:lti:role:ims/lis/Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Faculty": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Faculty": (SystemRole.instructor, CourseRole.instructor),
            "Staff": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Staff": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "urn:lti:role:ims/lis/Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant),
            "urn:lti:role:ims/lis/TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
        }

        index = 0
        for lti_role, (system_role, course_role) in roles.items():
            lti_consumer.student_number_param = "custom_student_number"
            # test new user (no compair user yet)
            lti_context = self.lti_data.create_context(lti_consumer)
            lti_user = self.lti_data.create_user(lti_consumer, system_role)
            lti_resource_link = self.lti_data.create_resource_link(lti_consumer, lti_context)
            lti_user_resource_link = self.lti_data.create_user_resource_link(
                lti_user, lti_resource_link, CourseRole.instructor)

            index += 1
            custom_student_number = "1234567"+str(index) if system_role == SystemRole.student else None

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
            self.assertIsNone(status['user']['student_number'])
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
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    context_title="lti_context_title") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['course']['exists'])
            self.assertIsNone(status['course']['id'])
            self.assertEqual(status['course']['name'], "lti_context_title")
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup lti session with custom assignment id
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    context_title="lti_context_title") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['course']['exists'])
            self.assertIsNone(status['course']['id'])
            self.assertEqual(status['course']['name'], "lti_context_title")
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup lti session with non existing user
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="lti_given", lis_person_name_family="lti_family",
                    custom_student_number=custom_student_number,
                    lis_person_contact_email_primary="lti_email") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertFalse(status['user']['exists'])
            self.assertEqual(status['user']['firstname'], "lti_given")
            self.assertEqual(status['user']['lastname'], "lti_family")
            self.assertIsNotNone(status['user']['displayname'])
            self.assertEqual(status['user']['student_number'], custom_student_number)
            self.assertEqual(status['user']['email'], "lti_email")
            self.assertEqual(status['user']['system_role'], system_role.value)

            # setup with existing user
            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            db.session.commit()

            # setup lti session with existing user
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="lti_given", lis_person_name_family="lti_family",
                    custom_student_number=custom_student_number,
                    lis_person_contact_email_primary="lti_email") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['user']['exists'])
            self.assertEqual(status['user']['firstname'], "lti_given")
            self.assertEqual(status['user']['lastname'], "lti_family")
            self.assertIsNotNone(status['user']['displayname'])
            self.assertEqual(status['user']['student_number'], custom_student_number)
            self.assertEqual(status['user']['email'], "lti_email")
            self.assertEqual(status['user']['system_role'], system_role.value)

            # setup with existing course
            course = self.data.create_course()
            lti_context.compair_course_id = course.id
            db.session.commit()

            # setup lti session with existing course
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    context_title="lti_context_title") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['course']['exists'])
            self.assertEqual(status['course']['id'], course.uuid)
            self.assertEqual(status['course']['name'], "lti_context_title")
            self.assertEqual(status['course']['course_role'], course_role.value)

            # setup lti session with existing course
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    context_title="lti_context_title") as rv:
                self.assert200(rv)

            rv = self.client.get(url, data={}, content_type='application/json')
            self.assert200(rv)
            status = rv.json['status']
            self.assertTrue(status['valid'])

            self.assertTrue(status['course']['exists'])
            self.assertEqual(status['course']['id'], course.uuid)
            self.assertEqual(status['course']['name'], "lti_context_title")
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

    def test_new_cas_auth_via_lti_launch(self):
        auth_data = ThirdPartyAuthTestData()

        lti_consumer = self.lti_data.get_consumer()
        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Faculty": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Faculty": (SystemRole.instructor, CourseRole.instructor),
            "Staff": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Staff": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "urn:lti:role:ims/lis/Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant),
            "urn:lti:role:ims/lis/TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
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

            unique_identifier = "unique_identifier_"+lti_role+"_1"

            with self.cas_login(unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas) \
                    .one()
                self.assertIsNotNone(third_party_user)
                user = third_party_user.user
                self.assertIsNotNone(user)

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is created
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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

            unique_identifier = "unique_identifier_"+lti_role+"_2"

            with self.cas_login(unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.cas) \
                    .one()
                self.assertIsNotNone(third_party_user)
                user = third_party_user.user
                self.assertIsNotNone(user)

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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

    def test_existing_cas_auth_via_lti_launch(self):
        auth_data = ThirdPartyAuthTestData()

        lti_consumer = self.lti_data.get_consumer()
        roles = {
            "Instructor": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Instructor": (SystemRole.instructor, CourseRole.instructor),
            "Faculty": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Faculty": (SystemRole.instructor, CourseRole.instructor),
            "Staff": (SystemRole.instructor, CourseRole.instructor),
            "urn:lti:role:ims/lis/Staff": (SystemRole.instructor, CourseRole.instructor),
            "Student": (SystemRole.student, CourseRole.student),
            "urn:lti:role:ims/lis/Student": (SystemRole.student, CourseRole.student),
            "TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant),
            "urn:lti:role:ims/lis/TeachingAssistant": (SystemRole.student, CourseRole.teaching_assistant)
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
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.cas)

            with self.cas_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.cas)

            with self.cas_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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

    def test_new_saml_auth_via_lti_launch(self):
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

            unique_identifier = "unique_identifier_"+lti_role+"_1"

            with self.saml_login(unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml) \
                    .one()
                self.assertIsNotNone(third_party_user)
                user = third_party_user.user
                self.assertIsNotNone(user)

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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

            unique_identifier = "unique_identifier_"+lti_role+"_2"

            with self.saml_login(unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                third_party_user = ThirdPartyUser.query \
                    .filter_by(unique_identifier=unique_identifier, third_party_type=ThirdPartyType.saml) \
                    .one()
                self.assertIsNotNone(third_party_user)
                user = third_party_user.user
                self.assertIsNotNone(user)

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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

    def test_existing_saml_auth_via_lti_launch(self):
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
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.saml)

            with self.saml_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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
            third_party_user = auth_data.create_third_party_user(user=user, third_party_type=ThirdPartyType.saml)

            with self.saml_login(third_party_user.unique_identifier, follow_redirects=False) as rv:
                self.assertRedirects(rv, '/app/#/lti')

                # check session
                with self.client.session_transaction() as sess:
                    self.assertTrue(sess.get('LTI'))

                    # check that lti_create_user_link is None
                    self.assertIsNone(sess.get('lti_create_user_link'))

                    # check that user is logged in
                    self.assertEqual(str(user.id), sess.get('_user_id'))

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
