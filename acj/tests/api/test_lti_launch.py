import json

from data.fixtures.test_data import SimpleAssignmentTestData, LTITestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import User, SystemRole, CourseRole, UserCourse, \
    LTIConsumer, LTIContext, LTIUser, LTIResourceLink, LTIUserResourceLink
from acj.core import db


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
        self.assertEqual(rv.json['id'], lti_context.acj_course_id)


