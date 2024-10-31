# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import zipfile

from flask import current_app

from data.fixtures.test_data import TestFixture
from compair.tests.test_compair import ComPAIRAPITestCase
from compair.core import db

from PIL import Image


class AssignmentAttachmentTests(ComPAIRAPITestCase):
    base_url = '/app'
    fixtures = None

    def setUp(self):
        super(AssignmentAttachmentTests, self).setUp()
        self.fixtures = TestFixture().add_course(
            num_students=25, num_assignments=1, num_groups=0,
            num_answers=20, with_draft_student=True)
        self.filePathsToCleanup = []

    def tearDown(self):
        for filePath in self.filePathsToCleanup:
            try:
                if os.path.isfile(filePath):
                    os.remove(filePath)
            except Exception as e:
                print(e)

    def _getUrl(self, courseUuid=None, assignmentUuid=None):
        if courseUuid is None:
            courseUuid = self.fixtures.course.uuid
        if assignmentUuid is None:
            assignmentUuid = self.fixtures.assignment.uuid
        return "/api/courses/" + courseUuid + "/assignments/" + assignmentUuid \
            + "/attachments/download_students"

    # we need to create actual files
    # isFileUploadedByInstructor simulates when instructors submit answers on
    # behalf of students, the file would be owned by the instructor instead of
    # the student
    def _createAttachmentsInAssignment(
            self,
            assignment,
            isFileUploadedByInstructor=False
    ):
        uploadDir = current_app.config['ATTACHMENT_UPLOAD_FOLDER']

        for answer in assignment.answers:
            uploader = answer.user
            if isFileUploadedByInstructor:
                uploader = self.fixtures.instructor
            attachFile = self.fixtures.add_file(uploader)
            attachFilename = attachFile.uuid + '.png'
            attachFile.name = attachFilename
            attachFile.uuid = attachFile.uuid
            attachFilePath = uploadDir + '/' + attachFilename
            img = Image.new('RGB', (60, 30), color = 'red')
            img.save(attachFilePath)
            self.filePathsToCleanup.append(attachFilePath)
            answer.file_id = attachFile.id
            db.session.add(assignment)
            db.session.add(attachFile)
            db.session.add(answer)
            db.session.commit()

    def _downloadAndCheckFiles(self):
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self._getUrl())
            self.assert200(rv)
            # make sure that we got download path and filename in return
            expectedFilename = '{} [attachments-{}].zip'.format(
                self.fixtures.assignment.name, self.fixtures.assignment.uuid)
            self.assertEqual(expectedFilename, rv.json['filename'])
            self.assertEqual('report/' + expectedFilename, rv.json['file'])
            # check that the actual zip file created exists
            zipFilePath = '{}/{}'.format(current_app.config['REPORT_FOLDER'],
                                         expectedFilename)
            self.assertTrue(os.path.isfile(zipFilePath))
            self.filePathsToCleanup.append(zipFilePath)
            # check that the contents of the zip file are as expected
            archive = zipfile.ZipFile(zipFilePath)
            self.assertEqual(None, archive.testzip())
            actualAttachments = archive.namelist()
            for answer in self.fixtures.assignment.answers:
                if not answer.file_id:
                    continue
                # we don't include inactive, draft, or practice answers
                if not answer.active or answer.draft or answer.practice:
                    continue
                # we only want current active students
                if answer.user not in self.fixtures.students:
                    continue
                expectedAttachment = '{} - {} - {}'.format(
                    answer.user.fullname,
                    answer.user.student_number,
                    answer.file.name
                )
                self.assertTrue(expectedAttachment in actualAttachments)

    def test_download_all_attachments_block_unauthorized_users(self):
        # test login required
        rv = self.client.get(self._getUrl())
        self.assert401(rv)

        # test unauthorized user
        with self.login(self.fixtures.unauthorized_instructor.username):
            rv = self.client.get(self._getUrl())
            self.assert403(rv)

    def test_download_all_attachments_require_valid_course_and_assignment(self):
        with self.login(self.fixtures.instructor.username):
            # invalid course
            url = self._getUrl("invalidUuid")
            rv = self.client.get(url)
            self.assert404(rv)
            # invalid assignment
            url = self._getUrl(None, "invalidUuid")
            rv = self.client.get(url)
            self.assert404(rv)

    def test_download_all_attachments_return_msg_if_no_attachments(self):
        with self.login(self.fixtures.instructor.username):
            rv = self.client.get(self._getUrl())
            self.assert200(rv)
            self.assertEqual('Assignment has no attachments', rv.json['msg'])

    def test_download_all_attachments(self):
        self._createAttachmentsInAssignment(self.fixtures.assignment)
        self._downloadAndCheckFiles()

    def test_files_named_for_answer_author_not_uploader(self):
        self._createAttachmentsInAssignment(self.fixtures.assignment, True)
        self._downloadAndCheckFiles()

