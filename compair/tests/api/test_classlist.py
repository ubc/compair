import csv
import json
import io
import unicodecsv as csv

from compair.core import db
from data.fixtures.test_data import BasicTestData, ThirdPartyUserFactory
from compair.tests.test_compair import ComPAIRAPITestCase, ComPAIRAPIDemoTestCase
from compair.models import CourseRole, UserCourse, ThirdPartyType, Course


class ClassListAPITest(ComPAIRAPITestCase):
    def setUp(self):
        super(ClassListAPITest, self).setUp()
        self.data = BasicTestData()
        self.url = "/api/courses/" + self.data.get_course().uuid + "/users"

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
            reader = csv.reader(rv.data.splitlines(), delimiter=',')

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
            reader = csv.reader(rv.data.splitlines(), delimiter=',')

            self.assertEqual(['username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, group_name in expected:
                self.assertEqual(
                    [user.username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

            # test export csv with group names
            for user_course in self.data.main_course.user_courses:
                if user_course.user_id == self.data.get_authorized_instructor().id:
                    user_course.group_name = "instructor_group"
                elif user_course.user_id == self.data.get_authorized_ta().id:
                    user_course.group_name = "ta_group"
                elif user_course.user_id == self.data.get_authorized_student().id:
                    user_course.group_name = "student_group"
            db.session.commit()

            expected = [
                (self.data.get_authorized_instructor(), "instructor_group"),
                (self.data.get_authorized_ta(), "ta_group"),
                (self.data.get_authorized_student(), "student_group")]
            expected.sort(key=lambda x: x[0].lastname)

            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=',')

            self.assertEqual(['username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, group_name in expected:
                self.assertEqual(
                    [user.username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

            # test export csv with cas usernames
            self.app.config['EXPOSE_CAS_USERNAME_TO_INSTRUCTOR'] = True
            third_party_student = ThirdPartyUserFactory(user=self.data.get_authorized_student())
            third_party_instructor = ThirdPartyUserFactory(user=self.data.get_authorized_instructor())
            third_party_ta = ThirdPartyUserFactory(user=self.data.get_authorized_ta())
            db.session.commit()

            expected = [
                (self.data.get_authorized_instructor(), third_party_instructor.unique_identifier, "instructor_group"),
                (self.data.get_authorized_ta(), third_party_ta.unique_identifier, "ta_group"),
                (self.data.get_authorized_student(), third_party_student.unique_identifier, "student_group")]
            expected.sort(key=lambda x: x[0].lastname)

            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=',')

            self.assertEqual(['username', 'cas_username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, cas_username, group_name in expected:
                self.assertEqual(
                    [user.username, cas_username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

            # test export csv with cas usernames (student has multiple cas_usernames). should use first username
            third_party_student2 = ThirdPartyUserFactory(user=self.data.get_authorized_student())
            third_party_student3 = ThirdPartyUserFactory(user=self.data.get_authorized_student())
            third_party_student4 = ThirdPartyUserFactory(user=self.data.get_authorized_student())
            db.session.commit()

            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.splitlines(), delimiter=',')

            self.assertEqual(['username', 'cas_username', 'student_number', 'firstname', 'lastname', 'email', 'displayname', 'group_name'], next(reader))
            for user, cas_username, group_name in expected:
                self.assertEqual(
                    [user.username, cas_username, user.student_number or '', user.firstname, user.lastname, user.email, user.displayname, group_name],
                    next(reader)
                )

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, (user, cas_username, group_name) in enumerate(expected):
                self.assertEqual(user.uuid, rv.json['objects'][key]['id'])

        with self.login("root"):
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, (user, cas_username, group_name) in enumerate(expected):
                self.assertEqual(user.uuid, rv.json['objects'][key]['id'])

        self.app.config['EXPOSE_CAS_USERNAME_TO_INSTRUCTOR'] = False

    def test_get_instructor_labels(self):
        url = self.url + "/instructors/labels"

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
            rv = self.client.get('/api/courses/999/users/instructors/labels')
            self.assert404(rv)

            # test success
            rv = self.client.get(url)
            self.assert200(rv)
            labels = rv.json['instructors']
            expected = {
                self.data.get_authorized_ta().uuid: 'Teaching Assistant',
                self.data.get_authorized_instructor().uuid: 'Instructor'
            }
            self.assertEqual(labels, expected)

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
                'name': self.data.get_authorized_student().fullname_sortable
            }
            self.assertEqual(students[0]['id'], expected['id'])
            self.assertEqual(students[0]['name'], expected['name'])

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['objects']
            expected = {
                'id': self.data.get_authorized_student().uuid,
                'name': self.data.get_authorized_student().fullname_sortable
            }
            self.assertEqual(students[0]['id'], expected['id'])
            self.assertEqual(students[0]['name'], expected['name'])

        # test success - student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['objects']
            expected = {
                'id': self.data.get_authorized_student().uuid,
                'name': self.data.get_authorized_student().displayname
            }
            self.assertEqual(students[0]['id'], expected['id'])
            self.assertEqual(students[0]['name'], expected['name'] + ' (You)')

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

        with self.login(self.data.get_authorized_student().username):
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

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group_name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group_name, 'group_instructor')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group_name, 'group_ta')

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

            self.assertEqual(len(user_courses), 3)
            for user_course in user_courses:
                self.assertIn(user_course.user_id, [student.id, instructor.id, ta.id])
                self.assertEqual(user_course.group_name, None)

    def test_import_cas_classlist(self):
        url = '/api/courses/' + self.data.get_course().uuid + '/users'
        student = self.data.get_authorized_student()
        third_party_student = ThirdPartyUserFactory(user=student)
        instructor = self.data.get_authorized_instructor()
        third_party_instructor = ThirdPartyUserFactory(user=instructor)
        ta = self.data.get_authorized_ta()
        third_party_ta = ThirdPartyUserFactory(user=ta)
        db.session.commit()

        filename = "classlist.csv"

        # test login required
        uploaded_file = io.BytesIO((third_party_student.unique_identifier).encode('utf-8'))
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
        self.assert401(rv)
        uploaded_file.close()

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_student().username):
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_ta().username):
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/users'
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(invalid_url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            uploaded_file.close()
            self.assert404(rv)

            # test invalid file type
            invalid_filetype = "classlist.png"
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, invalid_filetype), import_type=ThirdPartyType.cas.value))
            uploaded_file.close()
            self.assert400(rv)

            # test no username provided
            content = "".join([",\n", third_party_student.unique_identifier, ",", student.student_number])
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
            content = "".join([third_party_student.unique_identifier, "\n", third_party_student.unique_identifier])
            uploaded_file = io.BytesIO(content.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(third_party_student.unique_identifier, result['invalids'][0]['user']['username'])
            self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in system
            content = "".join(['username1,', student.student_number, "\n", third_party_student.unique_identifier])
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
                third_party_student.unique_identifier, ",", student.student_number, "\n",
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
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test invalid import type cas login disabled
            self.app.config['CAS_LOGIN_ENABLED'] = False
            uploaded_file = io.BytesIO(third_party_student.unique_identifier.encode('utf-8'))
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename), import_type=ThirdPartyType.cas.value))
            self.assert400(rv)
            uploaded_file.close()
            self.app.config['CAS_LOGIN_ENABLED'] = True

            # test authorized instructor - existing instructor
            uploaded_file = io.BytesIO(third_party_instructor.unique_identifier.encode('utf-8'))
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
            uploaded_file = io.BytesIO(third_party_ta.unique_identifier.encode('utf-8'))
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
                third_party_student.unique_identifier, ",,,,,,group_student\n",
                third_party_instructor.unique_identifier, ",,,,,,group_instructor\n",
                third_party_ta.unique_identifier, ",,,,,,group_ta\n",
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
                if user_course.user_id == student.id:
                    self.assertEqual(user_course.group_name, 'group_student')
                elif user_course.user_id == instructor.id:
                    self.assertEqual(user_course.group_name, 'group_instructor')
                elif user_course.user_id == ta.id:
                    self.assertEqual(user_course.group_name, 'group_ta')

            # test authorized instructor - group unenrollment
            content = "".join([
                third_party_student.unique_identifier, ",,,,,,\n",
                third_party_instructor.unique_identifier, ",,,,,,\n",
                third_party_ta.unique_identifier, ",,,,,,\n",
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
                self.assertEqual(user_course.group_name, None)


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
