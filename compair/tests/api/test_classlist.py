# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import io
import unicodecsv as csv
import six

from compair.core import db
from data.fixtures.test_data import BasicTestData, ThirdPartyAuthTestData
from compair.tests.test_compair import ComPAIRAPITestCase, ComPAIRAPIDemoTestCase
from compair.models import CourseRole, UserCourse, ThirdPartyType, Course, Group


class ClassListAPITest(ComPAIRAPITestCase):
    def setUp(self):
        super(ClassListAPITest, self).setUp()
        self.data = BasicTestData()
        self.auth_data = ThirdPartyAuthTestData()
        self.url = "/api/courses/" + self.data.get_course().uuid + "/users"

        self.delimiter = ",".encode('utf-8') if six.PY2 else ","

    def test_get_classlist(self):
        # test login required
        rv = self.client.get(self.url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(self.url)
            self.assert403(rv)

        expected = [
            (self.data.get_authorized_instructor(), ''),
            (self.data.get_authorized_ta(), ''),
            (self.data.get_authorized_student(), '')]
        expected.sort(key=lambda x: x[0].lastname)

        with self.login(self.data.get_authorized_instructor().username):
            # test authorized user
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, (user, group_name) in enumerate(expected):
                self.assertEqual(user.uuid, rv.json['objects'][key]['id'])

            # test export csv without email
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = False
            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=self.delimiter)

            self.assertEqual(['username', 'student_number', 'firstname', 'lastname', 'displayname', 'group_name'], next(reader))
            for user, group_name in expected:
                self.assertEqual(
                    [user.username, user.student_number or '', user.firstname, user.lastname, user.displayname, group_name],
                    next(reader)
                )

            # test export csv with email
            self.app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'] = True
            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=self.delimiter)

            self.assertEqual(['username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, group_name in expected:
                self.assertEqual(
                    [user.username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

            instructor_group = self.data.create_group(self.data.main_course)
            ta_group = self.data.create_group(self.data.main_course)
            student_group = self.data.create_group(self.data.main_course)

            # test export csv with group names
            for user_course in self.data.main_course.user_courses:
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    user_course.group_id = instructor_group.id
                elif user_course.user_id == self.data.get_authorized_ta().id:
                    user_course.group_id = ta_group.id
                elif user_course.user_id == self.data.get_authorized_student().id:
                    user_course.group_id = student_group.id
            db.session.commit()

            expected = [
                (self.data.get_authorized_instructor(), instructor_group.name),
                (self.data.get_authorized_ta(), ta_group.name),
                (self.data.get_authorized_student(), student_group.name)
            ]
            expected.sort(key=lambda x: x[0].lastname)

            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=self.delimiter)

            self.assertEqual(
                ['username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'],
                next(reader)
            )
            for user, group_name in expected:
                self.assertEqual(
                    [user.username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

            # test export csv with cas and saml usernames
            self.app.config['EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR'] = True
            cas_student = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.cas
            )
            saml_student = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.saml
            )
            cas_instructor = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_instructor(),
                third_party_type=ThirdPartyType.cas
            )
            saml_instructor = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_instructor(),
                third_party_type=ThirdPartyType.saml
            )
            cas_ta = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_ta(),
                third_party_type=ThirdPartyType.cas
            )
            saml_ta = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_ta(),
                third_party_type=ThirdPartyType.saml
            )
            db.session.commit()

            expected = [
                (self.data.get_authorized_instructor(), saml_instructor.unique_identifier, cas_instructor.unique_identifier, instructor_group.name),
                (self.data.get_authorized_ta(), saml_ta.unique_identifier, cas_ta.unique_identifier, ta_group.name),
                (self.data.get_authorized_student(), saml_student.unique_identifier, cas_student.unique_identifier, student_group.name)]
            expected.sort(key=lambda x: x[0].lastname)

            # test every combination of cas/saml enabled
            for cas_enabled, saml_enabled in [(False, False), (True, False), (False, True), (True, True)]:
                self.app.config['CAS_LOGIN_ENABLED'] = cas_enabled
                self.app.config['SAML_LOGIN_ENABLED'] = saml_enabled

                rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
                self.assert200(rv)
                self.assertEqual('text/csv', rv.content_type)
                reader = csv.reader(rv.data.splitlines(), delimiter=self.delimiter)

                expected_header = ['username', 'saml_username', 'cas_username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name']
                if not cas_enabled:
                    expected_header.pop(2)
                if not saml_enabled:
                    expected_header.pop(1)
                self.assertEqual(expected_header, next(reader))
                for user, saml_username, cas_username, group_name in expected:
                    expected_row = [user.username, saml_username, cas_username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name]
                    if not cas_enabled:
                        expected_row.pop(2)
                    if not saml_enabled:
                        expected_row.pop(1)
                    self.assertEqual(expected_row, next(reader))

            # test export csv with cas usernames (student has multiple cas_usernames). should use first username
            cas_student2 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.cas
            )
            cas_student3 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.cas
            )
            cas_student4 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.cas
            )
            cas_saml2 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.saml
            )
            cas_saml3 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.saml
            )
            cas_saml4 = self.auth_data.create_third_party_user(
                user=self.data.get_authorized_student(),
                third_party_type=ThirdPartyType.saml
            )
            db.session.commit()

            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=self.delimiter)

            self.assertEqual(['username', 'saml_username', 'cas_username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, saml_username, cas_username, group_name in expected:
                self.assertEqual(
                    [user.username, saml_username, cas_username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, (user, saml_username, cas_username, group_name) in enumerate(expected):
                self.assertEqual(user.uuid, rv.json['objects'][key]['id'])

        with self.login("root"):
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, (user, saml_username, cas_username, group_name) in enumerate(expected):
                self.assertEqual(user.uuid, rv.json['objects'][key]['id'])

    def test_get_students_course(self):
        url = self.url + "/students"

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test dropped instructor - unauthorized
        with self.login(self.data.get_dropped_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test unauthorized instructor
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get('/api/courses/999/users/students')
            self.assert404(rv)

            # test success - instructor
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['objects']
            expected = {
                'id': self.data.get_authorized_student().uuid,
                'name': self.data.get_authorized_student().fullname_sortable,
                'group_id': None,
                'role': 'Student',
            }
            self.assertEqual(students[0]['id'], expected['id'])
            self.assertEqual(students[0]['name'], expected['name'])
            self.assertEqual(students[0]['group_id'], expected['group_id'])
            self.assertEqual(students[0]['role'], expected['role'])

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['objects']
            expected = [
                {
                    'id': self.data.get_authorized_student().uuid,
                    'name': self.data.get_authorized_student().fullname_sortable,
                    'group_id': None,
                    'role': 'Student'
                }
            ]

            self.assertEqual(len(students), len(expected))
            for index, expect in enumerate(expected):
                self.assertEqual(students[index]['id'], expect['id'])
                self.assertEqual(students[index]['name'], expect['name'])
                self.assertEqual(students[index]['group_id'], expect['group_id'])
                self.assertEqual(students[index]['role'], expect['role'])

        # test success - student
        student =self.data.get_authorized_student()
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.get(url)
                self.assert200(rv)
                students = rv.json['objects']
                expected = [
                    {
                        'id': self.data.get_authorized_student().uuid,
                        'name': self.data.get_authorized_student().displayname + ' (You)',
                        'group_id': None,
                        'role': 'Student'
                    }
                ]

                self.assertEqual(len(students), len(expected))
                for index, expect in enumerate(expected):
                    self.assertEqual(students[index]['id'], expect['id'])
                    self.assertEqual(students[index]['name'], expect['name'])
                    self.assertEqual(students[index]['group_id'], expect['group_id'])
                    self.assertEqual(students[index]['role'], expect['role'])

    def test_get_instructors_course(self):
        url = self.url + "/instructors"

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # test dropped instructor - unauthorized
        with self.login(self.data.get_dropped_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # test unauthorized instructor
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.get('/api/courses/999/users/instructors')
            self.assert404(rv)

            # test success - instructor
            rv = self.client.get(url)
            self.assert200(rv)
            instructors = rv.json['objects']
            expected = sorted([self.data.get_authorized_ta(), self.data.get_authorized_instructor()],
                key=lambda user: (user.lastname, user.firstname)
            )
            self.assertEqual(len(instructors), len(expected))
            for index, user in enumerate(expected):
                self.assertEqual(instructors[index]['id'], user.uuid)
                self.assertEqual(instructors[index]['name'], user.fullname_sortable)
                self.assertEqual(instructors[index]['group_id'], None)
                if user.id == self.data.get_authorized_instructor().id:
                    self.assertEqual(instructors[index]['role'], CourseRole.instructor.value)
                else:
                    self.assertEqual(instructors[index]['role'], CourseRole.teaching_assistant.value)

        # test success - student
        student =self.data.get_authorized_student()
        for user_context in [self.login(student.username), self.impersonate(self.data.get_authorized_instructor(), student)]:
            with user_context:
                rv = self.client.get(url)
                self.assert200(rv)
                instructors = rv.json['objects']
                expected = sorted([self.data.get_authorized_ta(), self.data.get_authorized_instructor()],
                    key=lambda user: (user.lastname, user.firstname)
                )

                self.assertEqual(len(instructors), len(expected))
                for index, user in enumerate(expected):
                    self.assertEqual(instructors[index]['id'], user.uuid)
                    self.assertEqual(instructors[index]['name'], user.displayname)
                    self.assertEqual(instructors[index]['group_id'], None)
                    if user.id == self.data.get_authorized_instructor().id:
                        self.assertEqual(instructors[index]['role'], CourseRole.instructor.value)
                    else:
                        self.assertEqual(instructors[index]['role'], CourseRole.teaching_assistant.value)

    def test_enrol_instructor(self):
        url = self._create_enrol_url(self.url, self.data.get_dropped_instructor().uuid)
        role = {'course_role': 'Instructor'}  # defaults to Instructor

        # test login required
        rv = self.client.post(
            url,
            data=json.dumps(role),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert403(rv)

        # test invalid course id
        with self.login(self.data.get_authorized_instructor().username):
            invalid_url = '/api/courses/999/users/' + self.data.get_dropped_instructor().uuid
            rv = self.client.post(
                invalid_url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert404(rv)

            # test invalid user id
            invalid_url = self._create_enrol_url(self.url, "999")
            rv = self.client.post(
                invalid_url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert404(rv)

            # test enrolling dropped instructor
            expected = {
                'user_id': self.data.get_dropped_instructor().uuid,
                'fullname': self.data.get_dropped_instructor().fullname,
                'fullname_sortable': self.data.get_dropped_instructor().fullname_sortable,
                'course_role': CourseRole.instructor.value
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

            # test enrolling new instructor
            url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().uuid)
            expected = {
                'user_id': self.data.get_unauthorized_instructor().uuid,
                'fullname': self.data.get_unauthorized_instructor().fullname,
                'fullname_sortable': self.data.get_unauthorized_instructor().fullname_sortable,
                'course_role': CourseRole.instructor.value
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

            # test enrolling a different role - eg. Student
            role = {'course_role': CourseRole.teaching_assistant.value }
            expected = {
                'user_id': self.data.get_unauthorized_instructor().uuid,
                'fullname': self.data.get_unauthorized_instructor().fullname,
                'fullname_sortable': self.data.get_unauthorized_instructor().fullname_sortable,
                'course_role': CourseRole.teaching_assistant.value
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

    def test_unenrol_instructor(self):
        url = self._create_enrol_url(self.url, self.data.get_authorized_instructor().uuid)

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid course id
        invalid_url = '/api/courses/999/users/' + self.data.get_authorized_instructor().uuid
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test invalid user id
            invalid_url = self._create_enrol_url(self.url, "999")
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test existing user not in existing course
            invalid_url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().uuid)
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test success
            expected = {
                'user_id': self.data.get_authorized_instructor().uuid,
                'fullname': self.data.get_authorized_instructor().fullname,
                'fullname_sortable': self.data.get_authorized_instructor().fullname_sortable,
                'course_role': CourseRole.dropped.value
            }
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

    def test_import_compair_classlist(self):
        url = '/api/courses/' + self.data.get_course().uuid + '/users'
        student = self.data.get_authorized_student()
        instructor = self.data.get_authorized_instructor()
        ta = self.data.get_authorized_ta()

        filename = "classlist.csv"

        # test login required
        uploaded_file = io.BytesIO((student.username+",password").encode('utf-8'))
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
        self.assert401(rv)
        uploaded_file.close()

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            uploaded_file = io.BytesIO(student.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert403(rv)
            uploaded_file.close()

        for user_context in [ \
                self.login(student.username), \
                self.impersonate(instructor, student)]:
            with user_context:
                uploaded_file = io.BytesIO(student.username.encode('utf-8'))
                rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
                self.assert403(rv)
                uploaded_file.close()

        with self.login(self.data.get_authorized_ta().username):
            uploaded_file = io.BytesIO(student.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/users'
            uploaded_file = io.BytesIO(student.username.encode('utf-8'))
            rv = self.client.post(invalid_url, data=dict(file=(uploaded_file, filename)))
            uploaded_file.close()
            self.assert404(rv)

            # test invalid file type
            invalid_filetype = "classlist.png"
            uploaded_file = io.BytesIO(student.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, invalid_filetype)))
            uploaded_file.close()
            self.assert400(rv)

            # test no username provided
            content = "".join([",\n", student.username, ",password,", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(None, result['invalids'][0]['user']['username'])
            self.assertEqual('The username is required.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test no password provided
            content = "".join(["nopasswordusername"])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("nopasswordusername", result['invalids'][0]['user']['username'])
            self.assertEqual('The password is required.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test short password provided
            content = "".join(["shortpasswordusername", ",123"])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("shortpasswordusername", result['invalids'][0]['user']['username'])
            self.assertEqual('The password must be at least 4 characters long.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate usernames in file
            content = "".join([student.username, ",password\n", student.username, ",password"])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(student.username, result['invalids'][0]['user']['username'])
            self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in system
            content = "".join(['username1,password,', student.student_number, "\n", student.username, ',password'])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the system.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in file
            content = "".join([
                student.username, ",password,", student.student_number, "\n",
                "username1,password,", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test existing display
            content = "username1,password,,,," + student.displayname
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - new user
            uploaded_file = io.BytesIO(b'username2,password')
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - existing user (with password)
            current_password = student.password
            new_password = 'password123'

            uploaded_file = io.BytesIO((student.username+','+new_password).encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()
            self.assertEqual(student.password, current_password)
            self.assertNotEqual(student.password, new_password)

            student.last_online = None
            db.session.commit()

            uploaded_file = io.BytesIO((student.username+','+new_password).encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()
            self.assertNotEqual(student.password, current_password)
            self.assertEqual(student.password, new_password)

            new_password = 'password1234'
            for set_password in [new_password, '*', '']:
                uploaded_file = io.BytesIO((student.username+','+set_password).encode('utf-8'))
                rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
                self.assert200(rv)
                result = rv.json
                self.assertEqual(1, result['success'])
                self.assertEqual(0, len(result['invalids']))
                uploaded_file.close()
                self.assertEqual(student.password, new_password)

            # test invalid import type app login disabled
            self.app.config['APP_LOGIN_ENABLED'] = False
            uploaded_file = io.BytesIO(student.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert400(rv)
            uploaded_file.close()
            self.app.config['APP_LOGIN_ENABLED'] = True

            # test authorized instructor - existing instructor
            uploaded_file = io.BytesIO(instructor.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            instructor_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=instructor.id,
                    course_role=CourseRole.instructor
                ) \
                .one_or_none()
            self.assertIsNotNone(instructor_enrollment)

            # test authorized instructor - existing teaching assistant
            uploaded_file = io.BytesIO(ta.username.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            ta_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=ta.id,
                    course_role=CourseRole.teaching_assistant
                ) \
                .one_or_none()
            self.assertIsNotNone(ta_enrollment)

            # test authorized instructor - group enrollment
            content = "".join([
                student.username, ",*,,,,,,group_student\n",
                instructor.username, ",*,,,,,,group_instructor\n",
                ta.username, ",*,,,,,,group_ta\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            groups = Group.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    active=True
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            self.assertEqual(len(groups), 3)

            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertIsNotNone(user_course.group_id)
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group.name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group.name, 'group_instructor')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group.name, 'group_ta')

            for group in groups:
                self.assertIn(group.name, ['group_student', 'group_instructor', 'group_ta'])
                self.assertEqual(len(group.user_courses.all()), 1)

            # test authorized instructor - group unenrollment
            content = "".join([
                student.username, ",*,,,,,,\n",
                instructor.username, ",*,,,,,,\n",
                ta.username, ",*,,,,,,\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            groups = Group.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    active=True
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            self.assertEqual(len(groups), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertEqual(user_course.group_id, None)

            for group in groups:
                self.assertIn(group.name, ['group_student', 'group_instructor', 'group_ta'])
                self.assertEqual(len(group.user_courses.all()), 0)

            # test adding into existing groups
            content = "".join([
                student.username, ",*,,,,,,group_student\n",
                instructor.username, ",*,,,,,,group_instructor2\n",
                ta.username, ",*,,,,,,group_instructor2\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            groups = Group.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    active=True
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            self.assertEqual(len(groups), 4)

            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertIsNotNone(user_course.group_id)
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group.name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group.name, 'group_instructor2')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group.name, 'group_instructor2')

            for group in groups:
                self.assertIn(group.name, ['group_student', 'group_instructor', 'group_ta', 'group_instructor2'])
                if group.name in ['group_instructor', 'group_ta']:
                    self.assertEqual(len(group.user_courses.all()), 0)
                elif group.name == 'group_instructor2':
                    self.assertEqual(len(group.user_courses.all()), 2)
                else:
                    self.assertEqual(len(group.user_courses.all()), 1)


    def test_import_cas_classlist(self):
        url = '/api/courses/' + self.data.get_course().uuid + '/users'
        student = self.data.get_authorized_student()
        cas_student = self.auth_data.create_third_party_user(
            user=student,
            third_party_type=ThirdPartyType.cas
        )
        instructor = self.data.get_authorized_instructor()
        cas_instructor = self.auth_data.create_third_party_user(
            user=instructor,
            third_party_type=ThirdPartyType.cas
        )
        ta = self.data.get_authorized_ta()
        cas_ta = self.auth_data.create_third_party_user(
            user=ta,
            third_party_type=ThirdPartyType.cas
        )
        db.session.commit()

        filename = "classlist.csv"

        # test login required
        uploaded_file = io.BytesIO((cas_student.unique_identifier).encode('utf-8'))
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
        self.assert401(rv)
        uploaded_file.close()

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert403(rv)
            uploaded_file.close()

        for user_context in [ \
                self.login(student.username), \
                self.impersonate(instructor, student)]:
            with user_context:
                uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
                rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
                self.assert403(rv)
                uploaded_file.close()

        with self.login(self.data.get_authorized_ta().username):
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/users'
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(invalid_url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            uploaded_file.close()
            self.assert404(rv)

            # test invalid file type
            invalid_filetype = "classlist.png"
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, invalid_filetype), import_type=ThirdPartyType.cas.value))
            uploaded_file.close()
            self.assert400(rv)

            # test no username provided
            content = "".join([",\n", cas_student.unique_identifier, ",", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(None, result['invalids'][0]['user']['username'])
            self.assertEqual('The username is required.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate usernames in file
            content = "".join([cas_student.unique_identifier, "\n", cas_student.unique_identifier])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(cas_student.unique_identifier, result['invalids'][0]['user']['username'])
            self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in system
            content = "".join(['username1,', student.student_number, "\n", cas_student.unique_identifier])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the system.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in file
            content = "".join([
                cas_student.unique_identifier, ",", student.student_number, "\n",
                "username1,", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test existing display
            content = "username1,,,," + student.displayname
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - new user
            uploaded_file = io.BytesIO(b'username2')
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - existing user
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test invalid import type cas login disabled
            self.app.config['CAS_LOGIN_ENABLED'] = False
            uploaded_file = io.BytesIO(cas_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert400(rv)
            uploaded_file.close()
            self.app.config['CAS_LOGIN_ENABLED'] = True

            # test authorized instructor - existing instructor
            uploaded_file = io.BytesIO(cas_instructor.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            instructor_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=instructor.id,
                    course_role=CourseRole.instructor
                ) \
                .one_or_none()
            self.assertIsNotNone(instructor_enrollment)

            # test authorized instructor - existing teaching assistant
            uploaded_file = io.BytesIO(cas_ta.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            ta_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=ta.id,
                    course_role=CourseRole.teaching_assistant
                ) \
                .one_or_none()
            self.assertIsNotNone(ta_enrollment)

            # test authorized instructor - group enrollment
            content = "".join([
                cas_student.unique_identifier, ",,,,,,group_student\n",
                cas_instructor.unique_identifier, ",,,,,,group_instructor\n",
                cas_ta.unique_identifier, ",,,,,,group_ta\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertIsNotNone(user_course.group_id)
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group.name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group.name, 'group_instructor')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group.name, 'group_ta')

            # test authorized instructor - group unenrollment
            content = "".join([
                cas_student.unique_identifier, ",,,,,,\n",
                cas_instructor.unique_identifier, ",,,,,,\n",
                cas_ta.unique_identifier, ",,,,,,\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertEqual(user_course.group_id, None)

    def test_import_saml_classlist(self):
        url = '/api/courses/' + self.data.get_course().uuid + '/users'
        student = self.data.get_authorized_student()
        saml_student = self.auth_data.create_third_party_user(
            user=student,
            third_party_type=ThirdPartyType.saml
        )
        instructor = self.data.get_authorized_instructor()
        saml_instructor = self.auth_data.create_third_party_user(
            user=instructor,
            third_party_type=ThirdPartyType.saml
        )
        ta = self.data.get_authorized_ta()
        saml_ta = self.auth_data.create_third_party_user(
            user=ta,
            third_party_type=ThirdPartyType.saml
        )
        db.session.commit()

        filename = "classlist.csv"

        # test login required
        uploaded_file = io.BytesIO((saml_student.unique_identifier).encode('utf-8'))
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
        self.assert401(rv)
        uploaded_file.close()

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert403(rv)
            uploaded_file.close()

        for user_context in [ \
                self.login(student.username), \
                self.impersonate(instructor, student)]:
            with user_context:
                uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
                rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
                self.assert403(rv)
                uploaded_file.close()

        with self.login(self.data.get_authorized_ta().username):
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/users'
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(invalid_url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            uploaded_file.close()
            self.assert404(rv)

            # test invalid file type
            invalid_filetype = "classlist.png"
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, invalid_filetype), import_type=ThirdPartyType.saml.value))
            uploaded_file.close()
            self.assert400(rv)

            # test no username provided
            content = "".join([",\n", saml_student.unique_identifier, ",", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(None, result['invalids'][0]['user']['username'])
            self.assertEqual('The username is required.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate usernames in file
            content = "".join([saml_student.unique_identifier, "\n", saml_student.unique_identifier])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(saml_student.unique_identifier, result['invalids'][0]['user']['username'])
            self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in system
            content = "".join(['username1,', student.student_number, "\n", saml_student.unique_identifier])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the system.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in file
            content = "".join([
                saml_student.unique_identifier, ",", student.student_number, "\n",
                "username1,", student.student_number])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test existing display
            content = "username1,,,," + student.displayname
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - new user
            uploaded_file = io.BytesIO(b'username2')
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - existing user
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test invalid import type saml login disabled
            self.app.config['SAML_LOGIN_ENABLED'] = False
            uploaded_file = io.BytesIO(saml_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert400(rv)
            uploaded_file.close()
            self.app.config['SAML_LOGIN_ENABLED'] = True

            # test authorized instructor - existing instructor
            uploaded_file = io.BytesIO(saml_instructor.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            instructor_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=instructor.id,
                    course_role=CourseRole.instructor
                ) \
                .one_or_none()
            self.assertIsNotNone(instructor_enrollment)

            # test authorized instructor - existing teaching assistant
            uploaded_file = io.BytesIO(saml_ta.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(0, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            ta_enrollment = UserCourse.query \
                .filter_by(
                    course_id=self.data.get_course().id,
                    user_id=ta.id,
                    course_role=CourseRole.teaching_assistant
                ) \
                .one_or_none()
            self.assertIsNotNone(ta_enrollment)

            # test authorized instructor - group enrollment
            content = "".join([
                saml_student.unique_identifier, ",,,,,,group_student\n",
                saml_instructor.unique_identifier, ",,,,,,group_instructor\n",
                saml_ta.unique_identifier, ",,,,,,group_ta\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertIsNotNone(user_course.group_id)
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group.name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group.name, 'group_instructor')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group.name, 'group_ta')

            # test authorized instructor - group unenrollment
            content = "".join([
                saml_student.unique_identifier, ",,,,,,\n",
                saml_instructor.unique_identifier, ",,,,,,\n",
                saml_ta.unique_identifier, ",,,,,,\n",
            ])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.saml.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            user_courses = UserCourse.query \
                .filter(
                    UserCourse.course_id == self.data.get_course().id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .all()

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertEqual(user_course.group_id, None)


    def test_update_course_role_miltiple(self):
        url = self.url + '/roles'

        user_ids = [self.data.authorized_instructor.uuid, self.data.authorized_student.uuid, self.data.authorized_ta.uuid]
        params = {
            'ids': user_ids,
            'course_role': CourseRole.instructor.value
        }

        # test login required
        rv = self.client.post(
            url,
            data=json.dumps(params),
            content_type='application/json')
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert403(rv)

        # test with impersonating student
        student = self.data.authorized_student
        for user_context in [ \
                self.login(student.username), \
                self.impersonate(self.data.authorized_instructor, student)]:
            with user_context:
                rv = self.client.post(
                    url,
                    data=json.dumps(params),
                    content_type='application/json')
                self.assert403(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            rv = self.client.post(
                '/api/courses/999/users/roles',
                data=json.dumps(params),
                content_type='application/json')
            self.assert404(rv)

            # test missing user ids
            missing_ids = params.copy()
            missing_ids['ids'] = []
            rv = self.client.post(
                url,
                data=json.dumps(missing_ids),
                content_type='application/json')
            self.assert400(rv)

            # test invalid user ids
            invalid_ids = params.copy()
            invalid_ids['ids'] = [self.data.unauthorized_student.uuid]
            rv = self.client.post(
                url,
                data=json.dumps(invalid_ids),
                content_type='application/json')
            self.assert400(rv)

            # cannot change current_user's course role
            params_self = {
                'ids': [self.data.get_authorized_instructor().uuid],
                'course_role': CourseRole.teaching_assistant.value
            }
            rv = self.client.post(
                url,
                data=json.dumps(params_self),
                content_type='application/json')
            self.assert400(rv)

            # test changing role instructor
            rv = self.client.post(
                url,
                data=json.dumps(params),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['course_role'], CourseRole.instructor.value)

            for user_course in self.data.get_course().user_courses:
                # ingore changes for current_user
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                # other users should have course role updated
                elif user_course.user_id in user_ids:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)

            # test changing teaching assistant
            params_ta = params.copy()
            params_ta['course_role'] = CourseRole.teaching_assistant.value
            rv = self.client.post(
                url,
                data=json.dumps(params_ta),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['course_role'], CourseRole.teaching_assistant.value)

            for user_course in self.data.get_course().user_courses:
                # ingore changes for current_user
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                # other users should have course role updated
                elif user_course.user_id in user_ids:
                    self.assertEqual(user_course.course_role, CourseRole.teaching_assistant)

            # test changing role student
            params_student = params.copy()
            params_student['course_role'] = CourseRole.student.value
            rv = self.client.post(
                url,
                data=json.dumps(params_student),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['course_role'], CourseRole.student.value)

            for user_course in self.data.get_course().user_courses:
                # ingore changes for current_user
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                # other users should have course role updated
                elif user_course.user_id in user_ids:
                    self.assertEqual(user_course.course_role, CourseRole.student)

            # test changing dropped
            params_dropped = { 'ids': user_ids }
            rv = self.client.post(
                url,
                data=json.dumps(params_dropped),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(rv.json['course_role'], CourseRole.dropped.value)

            for user_course in self.data.get_course().user_courses:
                # ingore changes for current_user
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    self.assertEqual(user_course.course_role, CourseRole.instructor)
                # other users should have course role updated
                elif user_course.user_id in user_ids:
                    self.assertEqual(user_course.course_role, CourseRole.dropped)


    def _create_enrol_url(self, url, user_id):
        return url + '/' + user_id


class ClassListDemoAPITest(ComPAIRAPIDemoTestCase):
    def setUp(self):
        super(ClassListDemoAPITest, self).setUp()

    def test_import_demo_classlist(self):
        course = Course.query.get(1)
        url = '/api/courses/' + course.uuid + '/users'

        filename = "classlist.csv"
        content = "username1,,,,"

        with self.login("root"):
            # test import fails
            self.app.config['DEMO_INSTALLATION'] = True
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert400(rv)
            uploaded_file.close()

            # test import success
            self.app.config['DEMO_INSTALLATION'] = False
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            uploaded_file.close()

    def test_drop_demo_course_user(self):
        user_courses = UserCourse.query.all()

        for user_course in user_courses:
            url = '/api/courses/' + user_course.course.uuid + '/users/' + user_course.user.uuid

            with self.login('root'):
                # test deletion fails
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.delete(url)
                self.assert400(rv)

                # test deletion success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.delete(url)
                self.assert200(rv)

    def test_unenrol_demo_course_user(self):
        user_courses = UserCourse.query.all()

        for user_course in user_courses:
            url = '/api/courses/' + user_course.course.uuid + '/users/' + user_course.user.uuid

            expected = {'course_role': CourseRole.teaching_assistant.value }

            with self.login('root'):
                # test deletion by authorized instructor fails
                self.app.config['DEMO_INSTALLATION'] = True
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert400(rv)


                # test deletion by authorized instructor success
                self.app.config['DEMO_INSTALLATION'] = False
                rv = self.client.post(url, data=json.dumps(expected), content_type='application/json')
                self.assert200(rv)
