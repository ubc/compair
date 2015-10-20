import csv
import json
import io

from data.fixtures.test_data import BasicTestData
from acj.tests.test_acj import ACJAPITestCase
from acj.models import UserTypesForCourse


class ClassListAPITest(ACJAPITestCase):
    def setUp(self):
        super(ClassListAPITest, self).setUp()
        self.data = BasicTestData()
        self.url = "/api/courses/" + str(self.data.get_course().id) + "/users"

    def test_get_classlist(self):
        # test login required
        rv = self.client.get(self.url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(self.url)
            self.assert403(rv)

        expected = [
            self.data.get_authorized_instructor(),
            self.data.get_authorized_ta(),
            self.data.get_authorized_student()]
        expected.sort(key=lambda x: x.firstname)

        with self.login(self.data.get_authorized_instructor().username):
            # test authorized user
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, user in enumerate(expected):
                self.assertEqual(user.id, rv.json['objects'][key]['id'])

            # test export csv
            rv = self.client.get(self.url, headers={'Accept': 'text/csv'})
            self.assert200(rv)
            self.assertEqual('text/csv', rv.content_type)
            reader = csv.reader(rv.data.decode(encoding='UTF-8').splitlines(), delimiter=',')
            self.assertEqual(['username', 'student_no', 'firstname', 'lastname', 'email', 'displayname'], next(reader))

            for key, user in enumerate(expected):
                self.assertEqual(
                    [user.username, user.student_no or '', user.firstname, user.lastname, user.email, user.displayname],
                    next(reader)
                )

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(self.url)
            self.assert200(rv)
            self.assertEqual(len(expected), len(rv.json['objects']))
            for key, user in enumerate(expected):
                self.assertEqual(user.id, rv.json['objects'][key]['id'])

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
                str(self.data.get_authorized_ta().id): 'Teaching Assistant',
                str(self.data.get_authorized_instructor().id): 'Instructor'
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
            students = rv.json['students']
            expected = {
                'id': self.data.get_authorized_student().id,
                'name': self.data.get_authorized_student().fullname
            }
            self.assertEqual(students[0]['user']['id'], expected['id'])
            self.assertEqual(students[0]['user']['name'], expected['name'])

        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['students']
            expected = {
                'id': self.data.get_authorized_student().id,
                'name': self.data.get_authorized_student().fullname
            }
            self.assertEqual(students[0]['user']['id'], expected['id'])
            self.assertEqual(students[0]['user']['name'], expected['name'])

        # test success - student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert200(rv)
            students = rv.json['students']
            expected = {
                'id': self.data.get_authorized_student().id,
                'name': self.data.get_authorized_student().displayname
            }
            self.assertEqual(students[0]['user']['id'], expected['id'])
            self.assertEqual(students[0]['user']['name'], expected['name'] + ' (You)')

    def test_enrol_instructor(self):
        url = self._create_enrol_url(self.url, self.data.get_dropped_instructor().id)
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
            invalid_url = '/api/courses/999/users/instructors/' + str(self.data.get_dropped_instructor().id) + '/enrol'
            rv = self.client.post(
                invalid_url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert404(rv)

            # test invalid user id
            invalid_url = self._create_enrol_url(self.url, 999)
            rv = self.client.post(
                invalid_url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert404(rv)

            # test enrolling dropped instructor
            expected = {
                'user_id': self.data.get_dropped_instructor().id,
                'fullname': self.data.get_dropped_instructor().fullname,
                'course_role': UserTypesForCourse.TYPE_INSTRUCTOR
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

            # test enrolling new instructor
            url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().id)
            expected = {
                'user_id': self.data.get_unauthorized_instructor().id,
                'fullname': self.data.get_unauthorized_instructor().fullname,
                'course_role': UserTypesForCourse.TYPE_INSTRUCTOR
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

            # test enrolling a different role - eg. Student
            ta_role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_TA).first().id
            role = {'course_role_id': str(ta_role_id)}
            expected = {
                'user_id': self.data.get_unauthorized_instructor().id,
                'fullname': self.data.get_unauthorized_instructor().fullname,
                'course_role': UserTypesForCourse.TYPE_TA
            }
            rv = self.client.post(
                url,
                data=json.dumps(role),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

    def test_unenrol_instructor(self):
        url = self._create_enrol_url(self.url, self.data.get_authorized_instructor().id)
        dropped_role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test invalid course id
        invalid_url = '/api/courses/999/users/instructors/' + str(self.data.get_authorized_instructor().id) + '/enrol'
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test invalid user id
            invalid_url = self._create_enrol_url(self.url, 999)
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test existing user not in existing course
            invalid_url = self._create_enrol_url(self.url, self.data.get_unauthorized_instructor().id)
            rv = self.client.delete(invalid_url)
            self.assert404(rv)

            # test success
            expected = {
                'user': {
                    'id': self.data.get_authorized_instructor().id,
                    'fullname': self.data.get_authorized_instructor().fullname
                },
                'usertypesforcourse': {
                    'id': dropped_role_id,
                    'name': UserTypesForCourse.TYPE_DROPPED
                }
            }
            rv = self.client.delete(url)
            self.assert200(rv)
            self.assertEqual(expected, rv.json)

    def test_import_classlist(self):
        url = '/api/courses/' + str(self.data.get_course().id) + '/users'
        auth_student = self.data.get_authorized_student()
        filename = "classlist.csv"

        # test login required
        uploaded_file = io.BytesIO(auth_student.username.encode())
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
        self.assert401(rv)
        uploaded_file.close()

        # test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_student().username):
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_ta().username):
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert403(rv)
            uploaded_file.close()

        with self.login(self.data.get_authorized_instructor().username):
            # test invalid course id
            invalid_url = '/api/courses/999/users'
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(invalid_url, data=dict(file=(uploaded_file, filename)))
            uploaded_file.close()
            self.assert404(rv)

            # test invalid file type
            invalid_filetype = "classlist.png"
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, invalid_filetype)))
            uploaded_file.close()
            self.assert400(rv)

            # test no username provided
            content = "".join([",\n", auth_student.username, ",", auth_student.student_no])
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(None, result['invalids'][0]['user']['username'])
            self.assertEqual('The username is required.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate usernames in file
            content = "".join([auth_student.username, "\n", auth_student.username])
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual(auth_student.username, result['invalids'][0]['user']['username'])
            self.assertEqual('This username already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test duplicate student number in system
            content = "".join(['username1,', auth_student.student_no, "\n", auth_student.username])
            uploaded_file = io.BytesIO(content.encode())
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
                auth_student.username, ",", auth_student.student_no, "\n",
                "username1,", auth_student.student_no])
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(1, len(result['invalids']))
            self.assertEqual("username1", result['invalids'][0]['user']['username'])
            self.assertEqual('This student number already exists in the file.', result['invalids'][0]['message'])
            uploaded_file.close()

            # test existing display
            content = "username1,,,,," + auth_student.displayname
            uploaded_file = io.BytesIO(content.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - new user
            uploaded_file = io.BytesIO(b'username2')
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

            # test authorized instructor - existing user
            uploaded_file = io.BytesIO(auth_student.username.encode())
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            result = rv.json
            self.assertEqual(1, result['success'])
            self.assertEqual(0, len(result['invalids']))
            uploaded_file.close()

    def _create_enrol_url(self, url, user_id):
        return url + '/' + str(user_id)
