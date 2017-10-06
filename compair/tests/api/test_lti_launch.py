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

            # user_id_override ------
            lti_consumer.user_id_override = "custom_puid"
            db.session.commit()

            # user_id_override parameter is missing
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

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # user_id_override parameter is present (new user)
            custom_puid = "puid123456789_"+lti_role
            with self.lti_launch(lti_consumer, lti_resource_link_id,
                    user_id=lti_user_id, context_id=lti_context_id, roles=lti_role,
                    assignment_uuid=assignment.uuid, follow_redirects=False,
                    custom_puid=custom_puid) as rv:
                self.assertRedirects(rv, '/app/#/lti')

            lti_user = LTIUser.query.all()[-1]
            self.assertEqual(lti_user.user_id, custom_puid)
            lti_user_resource_link = LTIUserResourceLink.query.all()[-1]

            # check session
            with self.client.session_transaction() as sess:
                self.assertTrue(sess.get('LTI'))
                self.assertEqual(lti_consumer.id, sess.get('lti_consumer'))
                self.assertEqual(lti_resource_link.id, sess.get('lti_resource_link'))
                self.assertEqual(lti_user.id, sess.get('lti_user'))
                self.assertEqual(lti_context.id, sess.get('lti_context'))
                self.assertEqual(lti_user_resource_link.id, sess.get('lti_user_resource_link'))

                # user doesn't exist
                self.assertTrue(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertIsNone(sess.get('user_id'))

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            # link user account
            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            db.session.commit()

            # user_id_override parameter is present (existing user)
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

                # user already exists, oauth_create_user_link should be None
                self.assertIsNone(sess.get('oauth_create_user_link'))

                # check that user is logged in
                self.assertEqual(str(user.id), sess.get('user_id'))

            self.assertEqual(lti_resource_link.compair_assignment_id, assignment.id)

            lti_consumer.user_id_override = None
            db.session.commit()
            # done user_id_override ------

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

            # setup with existing user
            user = self.data.create_user(system_role)
            lti_user.compair_user = user
            db.session.commit()

            # setup lti session with existing user
            with self.lti_launch(lti_consumer, lti_resource_link.resource_link_id,
                    user_id=lti_user.user_id, context_id=lti_context.context_id, roles=lti_role,
                    lis_person_name_given="lti_given", lis_person_name_family="lti_family",
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
