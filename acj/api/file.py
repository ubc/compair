import os
import uuid
import shutil
import random
import string
import errno

from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from flask_restful import Resource, marshal

from . import dataformat
from acj.core import db, event
from acj.models import File, Assignment, Answer
from .util import new_restful_api

file_api = Blueprint('file_api', __name__)
api = new_restful_api(file_api)

# events
on_save_tmp_file = event.signal('TMP_FILE_CREATE')
on_file_get = event.signal('FILE_GET')
on_file_delete = event.signal('FILE_DELETE')


def allowed_file(filename, allowed):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in allowed


def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# /
class FileAPI(Resource):
    @login_required
    def post(self):
        uploaded_file = request.files['file']

        on_save_tmp_file.send(
            self,
            event_name=on_save_tmp_file.name,
            user=current_user,
            data={'file': uploaded_file.filename})

        if uploaded_file and allowed_file(uploaded_file.filename, current_app.config['ATTACHMENT_ALLOWED_EXTENSIONS']):
            name = str(uuid.uuid4()) + '.pdf'
            tmp_name = os.path.join(current_app.config['UPLOAD_FOLDER'], name)
            uploaded_file.save(tmp_name)
            current_app.logger.debug("Temporarily saved {}/{}".format(current_app.config['UPLOAD_FOLDER'], name))
            return {'name': name}

        return False
api.add_resource(FileAPI, '')


# /file_uuid
class FileIdAPI(Resource):
    @login_required
    def get(self, file_uuid):
        uploaded_file = File.get_active_by_uuid_or_404(file_uuid)

        on_file_get.send(
            self,
            event_name=on_file_get.name,
            user=current_user,
            data={'file_id': uploaded_file.id})

        return {'file': marshal(uploaded_file, dataformat.get_file())}

    @login_required
    def delete(self, file_uuid):
        uploaded_file = File.get_by_uuid_or_404(file_uuid)

        on_file_delete.send(
            self,
            event_name=on_file_delete.name,
            user=current_user,
            data={'file_id': uploaded_file.id})

        if uploaded_file:
            tmp_name = os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], uploaded_file.name)
            os.remove(tmp_name)

            assignments = Assignment.query \
                .filter_by(file_id=uploaded_file.id) \
                .all()
            for assignment in assignments:
                assignment.file_id = None

            answers = Answer.query \
                .filter_by(file_id=uploaded_file.id) \
                .all()
            for answer in answers:
                answer.file_id = None

            db.session.delete(uploaded_file)
            db.session.commit()
            current_app.logger.debug("SuccessFully deleted " + uploaded_file.name)

api.add_resource(FileIdAPI, '/<uuid:file_uuid>')



# move file from temporary location to "permanent" location
# makes a File entry
def add_new_file(alias, name, model_name, model_id):
    tmp_name = str(model_name) + '_' + str(model_id) + '.pdf'

    shutil.move(os.path.join(
        current_app.config['UPLOAD_FOLDER'], name),
        os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name))

    uploaded_file = File(user_id=current_user.id, name=tmp_name, alias=alias)

    db.session.add(uploaded_file)
    db.session.commit()
    current_app.logger.debug(
        "Moved and renamed " + name + " from " + current_app.config['UPLOAD_FOLDER'] +
        " to " + os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name))

    return uploaded_file

def duplicate_file(file, new_model_name, new_model_id):
    tmp_name = str(new_model_name) + '_' + str(new_model_id) + '.pdf'

    shutil.copy(
        os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], file.name),
        os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name)
    )

    duplicated_file = File(user_id=current_user.id, name=tmp_name, alias=file.alias)

    db.session.add(duplicated_file)
    db.session.commit()
    current_app.logger.debug(
        "copied file id:" + str(file.id) + " from " + os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], file.name) +
        " to " + os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name))

    return duplicated_file


# delete file
def delete_file(file_id):
    if file_id == None:
        return

    uploaded_file = File.query.get(file_id)
    if uploaded_file:
        try:
            os.remove(os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], uploaded_file.name))
            current_app.logger.debug("Successfully deleted file " + uploaded_file.name + " for with file id " + str(file_id))
        except OSError as e:
            if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                raise  # re-raise exception if a different error occured

        db.session.delete(uploaded_file)
        db.session.commit()