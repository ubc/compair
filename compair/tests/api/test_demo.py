# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import datetime

from flask_bouncer import ensure
from flask_login import login_user, logout_user
from werkzeug.exceptions import Unauthorized

from data.fixtures import DefaultFixture, UserFactory
from compair.tests.test_compair import ComPAIRAPIDemoTestCase
from compair.models import SystemRole, User
from compair.core import db
from compair.api import register_demo_api_blueprints


class DemoAPITests(ComPAIRAPIDemoTestCase):
    def setUp(self):
        super(DemoAPITests, self).setUp()

    def test_create_demo_user(self):
        url = '/api/demo'

        invalid_data = {'system_role': "invalid"}
        student_data = {'system_role': SystemRole.student.value}
        instructor_data = {'system_role': SystemRole.instructor.value}
        system_admin_data = {'system_role': SystemRole.sys_admin.value}

        # test DEMO_INSTALLATION needs to be set
        self.app.config['DEMO_INSTALLATION'] = False
        rv = self.client.post(url, data=json.dumps(student_data), content_type='application/json')
        self.assert404(rv)

        # need to re-register api blueprints since we're changing DEMO_INSTALLATION
        self.app.config['DEMO_INSTALLATION'] = True
        self.app = register_demo_api_blueprints(self.app)

        # test invalid system role
        rv = self.client.post(url, data=json.dumps(invalid_data), content_type='application/json')
        self.assert400(rv)

        # test create student
        rv = self.client.post(url, data=json.dumps(student_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "student31")
        self.assertEqual(user.system_role, SystemRole.student)


        # ensure that username will be set even if 'next' username is taken
        db.session.add(UserFactory(
            username="student33",
            system_role=SystemRole.student
        ))
        db.session.commit()

        rv = self.client.post(url, data=json.dumps(student_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "student34")
        self.assertEqual(user.system_role, SystemRole.student)



        # test create instructor
        rv = self.client.post(url, data=json.dumps(instructor_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "instructor2")
        self.assertEqual(user.system_role, SystemRole.instructor)

        # ensure that username will be set even if 'next' username is taken
        db.session.add(UserFactory(
            username="instructor4",
            system_role=SystemRole.instructor
        ))
        db.session.commit()

        rv = self.client.post(url, data=json.dumps(instructor_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "instructor5")
        self.assertEqual(user.system_role, SystemRole.instructor)



        # test create system admin
        rv = self.client.post(url, data=json.dumps(system_admin_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "admin2")
        self.assertEqual(user.system_role, SystemRole.sys_admin)

        # ensure that username will be set even if 'next' username is taken
        db.session.add(UserFactory(
            username="admin4",
            system_role=SystemRole.sys_admin
        ))
        db.session.commit()

        rv = self.client.post(url, data=json.dumps(system_admin_data), content_type='application/json')
        self.assert200(rv)
        user = User.query.filter_by(uuid=rv.json['id']).first()
        self.assertEqual(user.username, "admin5")
        self.assertEqual(user.system_role, SystemRole.sys_admin)
