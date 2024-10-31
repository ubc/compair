import zipfile

from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask_login import login_required
from flask_restful import Resource
from sqlalchemy import and_, or_
from sqlalchemy.orm import contains_eager

from compair.authorization import require
from compair.models import Answer, Assignment, Course, CourseRole, File, \
                           UserCourse
from .util import new_restful_api

from flask import current_app

assignment_attachment_api = Blueprint('assignment_attachment_api', __name__)
api = new_restful_api(assignment_attachment_api)

# If you're looking for file uploads, look at file.py.
# This API is only for downloading all attachments from an assignment.
# Organizationally, this probably fits better in file.py but since the api path
# differs completely from that used by file.py, I've had to split it out.


# given an assignment, download all student attachments in that assignment.
# This is restricted to only student answers to match the behaviour of the
# "Participation" tab in the UI, where it only lists students.
# /api/courses/<course>/assignments/<assignment>/attachments/download_students
class DownloadAllStudentAttachmentsAPI(Resource):
    DELIM = ' - '

    @login_required
    def get(self, course_uuid, assignment_uuid):
        # course unused, but we need to call it to check if it's a valid course
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        # permission checks
        require(MANAGE, assignment,
                title="Unable to download attachments",
                message="Sorry, your system role does not allow downloading all attachments")

        # grab answers so we can see how many has files
        answers = self.getStudentAnswersByAssignment(assignment)
        fileIds = []
        fileAuthors = {}
        for answer in answers:
            if not answer.file_id:
                continue
            # answer has an attachment
            fileIds.append(answer.file_id)
            # the user who uploaded the file can be different from the answer
            # author (e.g. instructor can upload on behalf of student), so
            # we need to use the answer author instead of file uploader
            author = answer.user_fullname
            if answer.user_student_number:
                author += self.DELIM + answer.user_student_number
            fileAuthors[answer.file_id] = author

        if not fileIds:
            return {'msg': 'Assignment has no attachments'}

        # grab files so we can get the real file location
        files = self.getFilesByIds(fileIds)

        # zip up the tmp dir and save it to the report dir
        zipName = '{} [attachments-{}].zip'.format(assignment.name,
                                                   assignment.uuid)
        zipPath = '{}/{}'.format(current_app.config['REPORT_FOLDER'], zipName)
        # we're using compression level 6 as a compromise between speed &
        # compression (this is Z_DEFAULT_COMPRESSION in zlib)
        with zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED, True, 6) as zipFile:
            for srcFile in files:
                srcFilePath = '{}/{}'.format(
                    current_app.config['ATTACHMENT_UPLOAD_FOLDER'],
                    srcFile.name
                )
                # filename should be 'full name - student number - uuid.ext'
                # student number is omitted if user doesn't have one
                srcFileName = fileAuthors[srcFile.id] + self.DELIM + srcFile.name
                #current_app.logger.debug("writing " + srcFileName)
                zipFile.write(srcFilePath, srcFileName)
        #current_app.logger.debug("Writing zip file")

        return {'file': 'report/' + zipName, 'filename': zipName}

    # this really should be abstracted out into the Answer model, but I wasn't
    # able to get the join with UserCourse to work inside the Answer model.
    def getStudentAnswersByAssignment(self, assignment):
        return Answer.query \
            .outerjoin(UserCourse, and_(
                Answer.user_id == UserCourse.user_id,
                assignment.course_id == UserCourse.course_id
            )) \
            .filter(and_(
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                or_(
                    and_(
                        UserCourse.course_role == CourseRole.student,
                        Answer.user_id != None
                    ),
                    Answer.group_id != None
                )
            )) \
            .all()

    def getFilesByIds(self, fileIds):
        return File.query.join(File.user).options(contains_eager(File.user)). \
                    filter(File.id.in_(fileIds)).all()


api.add_resource(DownloadAllStudentAttachmentsAPI, '/download_students')
