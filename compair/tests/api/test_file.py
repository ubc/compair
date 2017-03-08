import io
import os
import mock
from six import text_type

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
        url = self.base_url + '/attachment/' + filename

        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # TODO: no authorization control right now and needs to be added in the future
        # test unauthorized user
        # with self.login(self.fixtures.unauthorized_instructor.username):
        #     rv = self.client.get(url)
        #     self.assert403(rv)

        # valid instructor
        with self.login(self.fixtures.instructor.username):
            # invalid file name (db is not actually touched)
            rv = self.client.get(self.base_url + '/attachment/'+filename)
            self.assert404(rv)
            self.assertEqual('invalid file name', text_type(rv.get_data(as_text=True)))

            with mock.patch('compair.api.os.path.exists', return_value=True):
                with mock.patch('compair.api.send_file', return_value=make_response("OK")) as mock_send_file:
                    # test all attachment types
                    for extension in ['pdf','mp3','mp4','jpg','jpeg','png']:
                        db_file = self.fixtures.add_file(self.fixtures.instructor, name="file_name."+extension)
                        filename = db_file.name
                        url = self.base_url + '/attachment/' + filename

                        self.client.get(url)
                        if extension == 'pdf':
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                mimetype=db_file.mimetype,
                                attachment_filename=None,
                                as_attachment=False
                            )
                        else:
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                mimetype=db_file.mimetype,
                                attachment_filename=None,
                                as_attachment=True
                            )
                        mock_send_file.reset_mock()

                        # test overriding attachment filename
                        override_name = "override."+db_file.extension
                        self.client.get(url+"?name="+override_name)

                        if extension == 'pdf':
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                mimetype=db_file.mimetype,
                                attachment_filename=None,
                                as_attachment=False
                            )
                        else:
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                mimetype=db_file.mimetype,
                                attachment_filename=override_name,
                                as_attachment=True
                            )
                        mock_send_file.reset_mock()


    def test_create_attachment(self):
        url = '/api/attachment'
        test_formats = [
            ('pdf', 'application/pdf'),
            ('PDF', 'application/pdf'),
            ('mp3', 'audio/mpeg'),
            ('MP3', 'audio/mpeg'),
            ('mp4', 'video/mp4'),
            ('MP4', 'video/mp4'),
            ('jpg', 'image/jpeg'),
            ('JPG', 'image/jpeg'),
            ('jpeg', 'image/jpeg'),
            ('JPEG', 'image/jpeg')
        ]

        # test login required
        uploaded_file = io.BytesIO(b"this is a test")
        rv = self.client.post(url, data=dict(file=(uploaded_file, 'alias.pdf')))
        self.assert401(rv)
        uploaded_file.close()

        with self.login(self.fixtures.instructor.username):
            # test no file uploaded
            filename = 'alias.pdf'
            rv = self.client.post(url, data=dict())
            self.assert400(rv)
            self.assertEqual("Attachment Not Uploaded", rv.json['title'])
            self.assertEqual("No file was found to upload. Please try again.", rv.json['message'])

            # test no file uploaded
            filename = 'alias.xyz'
            uploaded_file = io.BytesIO(b"this is a test")
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert400(rv)
            self.assertEqual("Attachment Not Uploaded", rv.json['title'])
            self.assertEqual("Only JPEG, JPG, MP3, MP4, PDF, PNG files can be uploaded. Please try again with a valid file.",
                rv.json['message'])

            for extension, mimetype in test_formats:
                filename = 'alias.'+extension

                uploaded_file = io.BytesIO(b"this is a test")
                rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
                self.assert200(rv)
                uploaded_file.close()

                actual_file = rv.json['file']
                self.files_to_cleanup.append(actual_file['name'])
                self.assertEqual(actual_file['id']+"."+extension.lower(), actual_file['name'])
                self.assertEqual(filename, actual_file['alias'])
                self.assertEqual(extension.lower(), actual_file['extension'])
                self.assertEqual(mimetype, actual_file['mimetype'])