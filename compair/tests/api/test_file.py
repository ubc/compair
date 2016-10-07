import io
import os
import mock

from flask import current_app
from flask import make_response

from data.fixtures.test_data import TestFixture
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db


class FileRetrieveTests(ComPAIRAPITestCase):
    base_url = '/app'
    fixtures = None

    def setUp(self):
        super(FileRetrieveTests, self).setUp()
        self.fixtures = TestFixture().add_course(
            num_students=5, num_assignments=1, num_groups=0,
            num_answers=1, with_draft_student=True)
        self.files_to_cleanup = []

    def tearDown(self):
        folder = current_app.config['ATTACHMENT_UPLOAD_FOLDER']

        for file_name in self.files_to_cleanup:
            file_path = os.path.join(folder, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(e)

    def test_view_file(self):
        db_file = self.fixtures.add_file(self.fixtures.instructor)
        filename = db_file.name
        url = self.base_url + '/pdf/' + filename

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # TODO: no authorization control right now and needs to be added in the future
        # test unauthorized user
        # with self.login(self.fixtures.unauthorized_instructor.username):
        #     rv = self.client.get(url)
        #     self.assert403(rv)

        # participation with valid instructor
        with self.login(self.fixtures.instructor.username):
            # invalid file name
            rv = self.client.get(self.base_url + '/pdf/'+filename)
            self.assert404(rv)
            self.assertEqual('invalid file name', str(rv.get_data(as_text=True)))

            with mock.patch('compair.api.os.path.exists', return_value=True):
                with mock.patch('compair.api.send_file', return_value=make_response("OK")) as mock_send_file:
                    self.client.get(url)
                    mock_send_file.assert_called_once_with(
                        '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                        mimetype='application/pdf'
                    )

    def test_create_attachment(self):
        url = '/api/attachment'
        filename = 'alais.pdf'

        # test login required
        uploaded_file = io.BytesIO(b"this is a test")
        rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
        self.assert401(rv)
        uploaded_file.close()

        with self.login(self.fixtures.instructor.username):
            uploaded_file = io.BytesIO(b"this is a test")
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert200(rv)
            uploaded_file.close()

            actual_file = rv.json['file']
            self.files_to_cleanup.append(actual_file['name'])
            self.assertEqual(actual_file['id']+".pdf", actual_file['name'])
            self.assertEqual(filename, actual_file['alias'])

    def test_delete_attachment(self):
        # test file not attached to answer or assignment
        db_file = self.fixtures.add_file(self.fixtures.instructor)
        url = '/api/attachment/' + db_file.uuid

        # test login required
        rv = self.client.delete(url)
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # valid instructor
        with self.login(self.fixtures.instructor.username):
            # invalid file id
            rv = self.client.delete('/api/attachment/9999')
            self.assert404(rv)

            rv = self.client.delete(url)
            self.assert200(rv)
            actual_file = rv.json
            self.assertEqual(db_file.uuid, actual_file['id'])
            self.assertFalse(db_file.active)

            rv = self.client.delete(url)
            self.assert404(rv)

        # test file attached to assignment
        db_file = self.fixtures.add_file(self.fixtures.ta)
        self.fixtures.assignment.file_id = db_file.id
        db.session.commit()
        url = '/api/attachment/' + db_file.uuid

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test unauthorized user
        with self.login(self.fixtures.students[0].username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # valid instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.delete(url)
            self.assert200(rv)
            actual_file = rv.json
            self.assertEqual(db_file.uuid, actual_file['id'])
            self.assertFalse(db_file.active)

        # test file attached to answer
        student = self.fixtures.answers[0].user
        db_file = self.fixtures.add_file(student)
        self.fixtures.answers[0].file_id = db_file.id
        db.session.commit()
        url = '/api/attachment/' + db_file.uuid

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_student.username):
            rv = self.client.delete(url)
            self.assert403(rv)

        # author
        with self.login(student.username):
            rv = self.client.delete(url)
            self.assert200(rv)
            actual_file = rv.json
            self.assertEqual(db_file.uuid, actual_file['id'])
            self.assertFalse(db_file.active)

        # test file attached to answer
        student = self.fixtures.answers[0].user
        db_file = self.fixtures.add_file(student)
        self.fixtures.answers[0].file_id = db_file.id
        db.session.commit()
        url = '/api/attachment/' + db_file.uuid

        # valid instructor
        with self.login(self.fixtures.instructor.username):
            rv = self.client.delete(url)
            self.assert200(rv)
            actual_file = rv.json
            self.assertEqual(db_file.uuid, actual_file['id'])
            self.assertFalse(db_file.active)