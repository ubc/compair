import os
import uuid
import shutil
import random
import string
import errno

from flask import Blueprint, request, current_app
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask_login import login_required, current_user
from flask_restful import Resource, marshal

from compair.authorization import allow, require
from . import dataformat
from compair.core import db, event, abort
from compair.models import File, Assignment, Answer, \
    KalturaMedia
from compair.kaltura import KalturaAPI
from .util import new_restful_api

file_api = Blueprint('file_api', __name__)
api = new_restful_api(file_api)

# events
on_save_file = event.signal('FILE_CREATE')
on_get_kaltura_token = event.signal('FILE_GET_KALTURA_TOKEN')
on_save_kaltura_file = event.signal('FILE_CREATE_KALTURA_FILE')

def allowed_file(filename, allowed):
    return '.' in filename and \
        filename.lower().rsplit('.', 1)[1] in allowed


def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# /
class FileAPI(Resource):
    @login_required
    def post(self):
        uploaded_file = request.files.get('file')

        if not uploaded_file:
            abort(400, title="File Not Uploaded", message="Sorry, no file was found to upload. Please try uploading again.")
        elif not allowed_file(uploaded_file.filename, current_app.config['ATTACHMENT_ALLOWED_EXTENSIONS']):
            extensions = [extension.upper() for extension in list(current_app.config['ATTACHMENT_ALLOWED_EXTENSIONS'])]
            extensions.sort()
            extensions = ", ".join(extensions)
            abort(400, title="File Not Uploaded", message="Please try again with an approved file type, which includes: "+extensions+".")

        on_save_file.send(
            self,
            event_name=on_save_file.name,
            user=current_user,
            data={'file': uploaded_file.filename})

        try:
            db_file = File(
                user_id=current_user.id,
                name='',
                alias=uploaded_file.filename
            )
            db.session.add(db_file)
            db.session.commit()

            # use uuid generated by file model for name
            name = db_file.uuid + '.' + uploaded_file.filename.lower().rsplit('.', 1)[1]

            # create new file with name
            full_path = os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], name)
            uploaded_file.save(full_path)
            current_app.logger.debug("Saved attachment {}/{}".format(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], name))

            # update file record with name
            db_file.name = name
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return {'file': marshal(db_file, dataformat.get_file())}

api.add_resource(FileAPI, '')



# /kaltura
class FileKalturaAPI(Resource):
    @login_required
    def get(self):
        if not KalturaAPI.enabled():
            abort(400, title="File Not Uploaded",
                message="Please use a valid upload method to attach files. You are not able to upload with this method based on the current settings.")

        upload_url = KalturaAPI.generate_new_upload_token()

        on_get_kaltura_token.send(
            self,
            event_name=on_get_kaltura_token.name,
            user=current_user,
            data={'upload_url': upload_url})

        return {'upload_url': upload_url}


api.add_resource(FileKalturaAPI, '/kaltura')

# /kaltura/upload_token_id
class FileKalturaUploadTokenAPI(Resource):
    @login_required
    def post(self, upload_token_id):
        if not KalturaAPI.enabled():
            abort(400, title="File Not Uploaded",
                message="Please use a valid upload method to attach files. You are not able to upload with this method based on the current settings.")

        kaltura_media = KalturaAPI.complete_upload_for_token(upload_token_id)

        on_save_kaltura_file.send(
            self,
            event_name=on_save_kaltura_file.name,
            user=current_user,
            data={'upload_token_id': upload_token_id})

        try:
            db_file = File(
                user_id=current_user.id,
                name='',
                alias=kaltura_media.file_name,
                kaltura_media=kaltura_media
            )
            db.session.add(db_file)
            db.session.commit()

            # use uuid generated by file model for name
            name = db_file.uuid + '.' + kaltura_media.extension

            # update file record with name
            db_file.name = name
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return {'file': marshal(db_file, dataformat.get_file())}


api.add_resource(FileKalturaUploadTokenAPI, '/kaltura/<upload_token_id>')