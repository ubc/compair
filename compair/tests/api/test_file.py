# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import io
import os
import mock
from six import text_type

from flask import current_app
from flask import make_response

from data.fixtures.test_data import TestFixture
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db
from compair.models import KalturaMedia


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
                    extensions = [
                        ('pdf', 'application/pdf'),
                        ('mp3', 'audio/mpeg'),
                        ('mp4', 'video/mp4'),
                        ('jpg', 'image/jpeg'),
                        ('jpeg', 'image/jpeg'),
                        ('png', 'image/png')
                    ]
                    for (extension, mimetype) in extensions:
                        db_file = self.fixtures.add_file(self.fixtures.instructor, name="file_name."+extension)
                        filename = db_file.name
                        url = self.base_url + '/attachment/' + filename

                        self.client.get(url)
                        if extension == 'pdf':
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                attachment_filename=None,
                                as_attachment=False,
                                mimetype=mimetype
                            )
                        else:
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                attachment_filename=None,
                                as_attachment=True,
                                mimetype=mimetype
                            )
                        mock_send_file.reset_mock()

                        # test overriding attachment filename
                        override_name = "override."+db_file.extension
                        self.client.get(url+"?name="+override_name)

                        if extension == 'pdf':
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                attachment_filename=None,
                                as_attachment=False,
                                mimetype=mimetype
                            )
                        else:
                            mock_send_file.assert_called_once_with(
                                '{}/{}'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], filename),
                                attachment_filename=override_name,
                                as_attachment=True,
                                mimetype=mimetype
                            )
                        mock_send_file.reset_mock()


    def test_create_attachment(self):
        url = '/api/attachment'
        test_formats = [
            ('pdf', 'application/pdf'),
            ('mp3', 'audio/mpeg'),
            ('mp4', 'video/mp4'),
            ('webm', 'video/webm'),
            ('jpg', 'image/jpeg'),
            ('jpeg', 'image/jpeg')
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
            self.assertEqual("File Not Uploaded", rv.json['title'])
            self.assertEqual("Sorry, no file was found to upload. Please try uploading again.", rv.json['message'])

            # test no file uploaded
            filename = 'alias.xyz'
            uploaded_file = io.BytesIO(b"this is a test")
            rv = self.client.post(url, data=dict(file=(uploaded_file, filename)))
            self.assert400(rv)
            self.assertEqual("File Not Uploaded", rv.json['title'])
            self.assertEqual("Please try again with an approved file type, which includes: JPEG, JPG, MP3, MP4, PDF, PNG, WEBM.",
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

                # test with uppercase extension
                filename = 'alias.'+extension.upper()

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


    @mock.patch('compair.kaltura.kaltura_session.KalturaSession._api_start')
    @mock.patch('compair.kaltura.kaltura_session.KalturaSession._api_end')
    @mock.patch('compair.kaltura.upload_token.UploadToken._api_add')
    def test_get_kaltura(self, mocked_upload_token_add, mocked_kaltura_session_end, mocked_kaltura_session_start):
        url = '/api/attachment/kaltura'
        current_app.config['KALTURA_ENABLED'] = True
        current_app.config['KALTURA_SERVICE_URL'] = "https://www.kaltura.com"
        current_app.config['KALTURA_PARTNER_ID'] = 123
        current_app.config['KALTURA_USER_ID'] = "test@test.com"
        current_app.config['KALTURA_SECRET'] = "abc"
        current_app.config['KALTURA_PLAYER_ID'] = 456

        mocked_kaltura_session_start.return_value = "ks_mock"
        mocked_kaltura_session_end.return_value = {}
        mocked_upload_token_add.return_value = {
            "id": "mocked_upload_token_id"
        }
        expected_upload_url = "https://www.kaltura.com/api_v3/service/uploadtoken/action/upload?format=1&uploadTokenId=mocked_upload_token_id&ks=ks_mock"


        # test login required
        rv = self.client.get(url)
        self.assert401(rv)

        with self.login(self.fixtures.instructor.username):
            # test kaltura disabled
            current_app.config['KALTURA_ENABLED'] = False
            rv = self.client.get(url)
            self.assert400(rv)

            # test kaltura enabled
            current_app.config['KALTURA_ENABLED'] = True
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(rv.json['upload_url'], expected_upload_url)

            self.assertEqual(mocked_kaltura_session_start.call_count, 2)
            mocked_kaltura_session_start.assert_any_call("test@test.com")
            mocked_kaltura_session_start.assert_any_call("test@test.com",
                privileges="edit:mocked_upload_token_id,urirestrict:/api_v3/service/uploadtoken/action/upload*")
            mocked_kaltura_session_start.reset_mock()

            mocked_kaltura_session_end.assert_called_once_with("ks_mock")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_add.assert_called_once_with("ks_mock")
            mocked_upload_token_add.reset_mock()

            kaltura_media_items = KalturaMedia.query.all()
            self.assertEqual(len(kaltura_media_items), 1)
            self.assertEqual(kaltura_media_items[0].user_id, self.fixtures.instructor.id)
            self.assertEqual(kaltura_media_items[0].partner_id, 123)
            self.assertEqual(kaltura_media_items[0].player_id, 456)
            self.assertEqual(kaltura_media_items[0].upload_ks, "ks_mock")
            self.assertEqual(kaltura_media_items[0].upload_token_id, "mocked_upload_token_id")
            self.assertIsNone(kaltura_media_items[0].file_name)
            self.assertIsNone(kaltura_media_items[0].entry_id)
            self.assertIsNone(kaltura_media_items[0].download_url)

            # use global unique identifer (user has no global unique identifer)
            current_app.config['KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER'] = True
            mocked_upload_token_add.return_value = {
                "id": "mocked_upload_token_id2"
            }
            expected_upload_url = "https://www.kaltura.com/api_v3/service/uploadtoken/action/upload?format=1&uploadTokenId=mocked_upload_token_id2&ks=ks_mock"
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(rv.json['upload_url'], expected_upload_url)

            self.assertEqual(mocked_kaltura_session_start.call_count, 2)
            mocked_kaltura_session_start.assert_any_call("test@test.com")
            mocked_kaltura_session_start.assert_any_call("test@test.com",
                privileges="edit:mocked_upload_token_id2,urirestrict:/api_v3/service/uploadtoken/action/upload*")
            mocked_kaltura_session_start.reset_mock()

            mocked_kaltura_session_end.assert_called_once_with("ks_mock")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_add.assert_called_once_with("ks_mock")
            mocked_upload_token_add.reset_mock()

            kaltura_media_items = KalturaMedia.query.all()
            self.assertEqual(len(kaltura_media_items), 2)
            self.assertEqual(kaltura_media_items[1].user_id, self.fixtures.instructor.id)


            # use global unique identifer (user has global unique identifer)
            self.fixtures.instructor.global_unique_identifier = "1234567890@test.com"
            mocked_upload_token_add.return_value = {
                "id": "mocked_upload_token_id3"
            }
            expected_upload_url = "https://www.kaltura.com/api_v3/service/uploadtoken/action/upload?format=1&uploadTokenId=mocked_upload_token_id3&ks=ks_mock"
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(rv.json['upload_url'], expected_upload_url)

            self.assertEqual(mocked_kaltura_session_start.call_count, 2)
            mocked_kaltura_session_start.assert_any_call("1234567890@test.com")
            mocked_kaltura_session_start.assert_any_call("1234567890@test.com",
                privileges="edit:mocked_upload_token_id3,urirestrict:/api_v3/service/uploadtoken/action/upload*")
            mocked_kaltura_session_start.reset_mock()

            mocked_kaltura_session_end.assert_called_once_with("ks_mock")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_add.assert_called_once_with("ks_mock")
            mocked_upload_token_add.reset_mock()

            kaltura_media_items = KalturaMedia.query.all()
            self.assertEqual(len(kaltura_media_items), 3)
            self.assertEqual(kaltura_media_items[2].user_id, self.fixtures.instructor.id)

            current_app.config['KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER'] = False

    @mock.patch('compair.kaltura.kaltura_session.KalturaSession._api_start')
    @mock.patch('compair.kaltura.kaltura_session.KalturaSession._api_end')
    @mock.patch('compair.kaltura.upload_token.UploadToken._api_get')
    @mock.patch('compair.kaltura.media.Media._api_add')
    @mock.patch('compair.kaltura.media.Media._api_add_content')
    def test_post_kaltura(self, mocked_kaltura_media_add_content, mocked_kaltura_media_add, mocked_upload_token_get,
            mocked_kaltura_session_end, mocked_kaltura_session_start):
        url = '/api/attachment/kaltura/mocked_upload_token_id'
        invalid_url = '/api/attachment/kaltura/mocked_upload_token_id_invalid'
        current_app.config['KALTURA_ENABLED'] = True
        current_app.config['KALTURA_SERVICE_URL'] = "https://www.kaltura.com"
        current_app.config['KALTURA_PARTNER_ID'] = 123
        current_app.config['KALTURA_USER_ID'] = "test@test.com"
        current_app.config['KALTURA_SECRET'] = "abc"
        current_app.config['KALTURA_PLAYER_ID'] = 456

        mocked_kaltura_session_start.return_value = "ks_mock"
        mocked_kaltura_session_end.return_value = {}
        mocked_upload_token_get.return_value = {
            "id": "mocked_upload_token_id",
            "fileName": "uploaded_audio_file.mp3"
        }
        mocked_kaltura_media_add.return_value = {
            "id": "mock_entry_id"
        }
        mocked_kaltura_media_add_content.return_value = {
            "id": "mock_entry_id",
            "downloadUrl": "http://www.download/url.com"
        }

        kaltura_media = KalturaMedia(
            user=self.fixtures.instructor,
            service_url="https://www.kaltura.com",
            partner_id=123,
            player_id=456,
            upload_ks="upload_ks_mock",
            upload_token_id="mocked_upload_token_id"
        )
        db.session.add(kaltura_media)

        kaltura_media2 = KalturaMedia(
            user=self.fixtures.instructor,
            service_url="https://www.kaltura.com",
            partner_id=123,
            player_id=456,
            upload_ks="upload_ks_mock2",
            upload_token_id="mocked_upload_token_id2"
        )
        db.session.add(kaltura_media)

        kaltura_media3 = KalturaMedia(
            user=self.fixtures.instructor,
            service_url="https://www.kaltura.com",
            partner_id=123,
            player_id=456,
            upload_ks="upload_ks_mock3",
            upload_token_id="mocked_upload_token_id3"
        )
        db.session.add(kaltura_media)

        invalid_kaltura_media =  KalturaMedia(
            user=self.fixtures.instructor,
            service_url="https://www.kaltura.com",
            partner_id=123,
            player_id=456,
            upload_ks="upload_ks_mock",
            upload_token_id="mocked_upload_token_id_invalid",
            entry_id="def"
        )
        db.session.add(invalid_kaltura_media)
        db.session.commit()

        # test login required
        rv = self.client.post(url)
        self.assert401(rv)

        with self.login(self.fixtures.instructor.username):
            # test kaltura disabled
            current_app.config['KALTURA_ENABLED'] = False
            rv = self.client.post(url)
            self.assert400(rv)

            # test invalid upload_token_id
            current_app.config['KALTURA_ENABLED'] = True
            rv = self.client.post(invalid_url)
            self.assert400(rv)

            # test valid
            rv = self.client.post(url)
            self.assert200(rv)
            self.assertEqual(rv.json['file']['id'], kaltura_media.files.all()[0].uuid)
            self.assertEqual(kaltura_media.file_name, "uploaded_audio_file.mp3")
            self.assertEqual(kaltura_media.entry_id, "mock_entry_id")
            self.assertEqual(kaltura_media.download_url, "http://www.download/url.com")
            self.assertEqual(kaltura_media.service_url, "https://www.kaltura.com")

            mocked_kaltura_session_start.assert_called_once_with("test@test.com")
            mocked_kaltura_session_start.reset_mock()

            self.assertEqual(mocked_kaltura_session_end.call_count, 2)
            mocked_kaltura_session_end.assert_any_call("ks_mock")
            mocked_kaltura_session_end.assert_any_call("upload_ks_mock")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_get.assert_called_once_with("ks_mock", "mocked_upload_token_id")
            mocked_upload_token_get.reset_mock()

            mocked_kaltura_media_add.assert_called_once_with("ks_mock", 5)
            mocked_kaltura_media_add.reset_mock()

            mocked_kaltura_media_add_content.assert_called_once_with("ks_mock", "mock_entry_id", "mocked_upload_token_id")
            mocked_kaltura_media_add_content.reset_mock()

            # test direct download from kaltura via /attachment
            kaltura_attachment_url = self.base_url + '/attachment/' + rv.json['file']['name'] + '?name=uploaded_audio_file.mp3'
            rv = self.client.get(kaltura_attachment_url)
            self.assertTrue(rv.location.startswith(kaltura_media.download_url))  # redirecting to Kaltura
            mocked_kaltura_session_start.assert_called_once_with("test@test.com", \
                expiry=60, \
                privileges='sview:'+kaltura_media.entry_id+',urirestrict:/url.com/*'
                )
            mocked_kaltura_session_start.reset_mock()

            # use global unique identifer (user has no global unique identifer)
            current_app.config['KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER'] = True
            url = '/api/attachment/kaltura/mocked_upload_token_id2'
            mocked_upload_token_get.return_value = {
                "id": "mocked_upload_token_id2",
                "fileName": "uploaded_audio_file2.mp3"
            }
            mocked_kaltura_media_add.return_value = {
                "id": "mock_entry_id2"
            }
            mocked_kaltura_media_add_content.return_value = {
                "id": "mock_entry_id2",
                "downloadUrl": "www.download/url2.com"
            }
            rv = self.client.post(url)
            self.assert200(rv)
            self.assertEqual(rv.json['file']['id'], kaltura_media2.files.all()[0].uuid)
            self.assertEqual(kaltura_media2.file_name, "uploaded_audio_file2.mp3")
            self.assertEqual(kaltura_media2.entry_id, "mock_entry_id2")
            self.assertEqual(kaltura_media2.download_url, "www.download/url2.com")
            self.assertEqual(kaltura_media2.service_url, "https://www.kaltura.com")

            mocked_kaltura_session_start.assert_called_once_with("test@test.com")
            mocked_kaltura_session_start.reset_mock()

            self.assertEqual(mocked_kaltura_session_end.call_count, 2)
            mocked_kaltura_session_end.assert_any_call("ks_mock")
            mocked_kaltura_session_end.assert_any_call("upload_ks_mock2")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_get.assert_called_once_with("ks_mock", "mocked_upload_token_id2")
            mocked_upload_token_get.reset_mock()

            mocked_kaltura_media_add.assert_called_once_with("ks_mock", 5)
            mocked_kaltura_media_add.reset_mock()

            mocked_kaltura_media_add_content.assert_called_once_with("ks_mock", "mock_entry_id2", "mocked_upload_token_id2")
            mocked_kaltura_media_add_content.reset_mock()

            # use global unique identifer (user has global unique identifer)
            self.fixtures.instructor.global_unique_identifier = "1234567890@test.com"
            url = '/api/attachment/kaltura/mocked_upload_token_id3'
            mocked_upload_token_get.return_value = {
                "id": "mocked_upload_token_id3",
                "fileName": "uploaded_audio_file3.mp3"
            }
            mocked_kaltura_media_add.return_value = {
                "id": "mock_entry_id3"
            }
            mocked_kaltura_media_add_content.return_value = {
                "id": "mock_entry_id3",
                "downloadUrl": "www.download/url3.com"
            }
            rv = self.client.post(url)
            self.assert200(rv)
            self.assertEqual(rv.json['file']['id'], kaltura_media3.files.all()[0].uuid)
            self.assertEqual(kaltura_media3.file_name, "uploaded_audio_file3.mp3")
            self.assertEqual(kaltura_media3.entry_id, "mock_entry_id3")
            self.assertEqual(kaltura_media3.download_url, "www.download/url3.com")
            self.assertEqual(kaltura_media3.service_url, "https://www.kaltura.com")

            mocked_kaltura_session_start.assert_called_once_with("1234567890@test.com")
            mocked_kaltura_session_start.reset_mock()

            self.assertEqual(mocked_kaltura_session_end.call_count, 2)
            mocked_kaltura_session_end.assert_any_call("ks_mock")
            mocked_kaltura_session_end.assert_any_call("upload_ks_mock3")
            mocked_kaltura_session_end.reset_mock()

            mocked_upload_token_get.assert_called_once_with("ks_mock", "mocked_upload_token_id3")
            mocked_upload_token_get.reset_mock()

            mocked_kaltura_media_add.assert_called_once_with("ks_mock", 5)
            mocked_kaltura_media_add.reset_mock()

            mocked_kaltura_media_add_content.assert_called_once_with("ks_mock", "mock_entry_id3", "mocked_upload_token_id3")
            mocked_kaltura_media_add_content.reset_mock()

            current_app.config['KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER'] = False