import os, uuid, shutil, random, string

from flask import Blueprint, Flask, request, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from . import dataformat
from .core import db, event
from .models import FilesForPosts
from .util import new_restful_api


attachment_api = Blueprint('attachment_api', __name__)
api = new_restful_api(attachment_api)

# events
on_save_tmp_file = event.signal('TMP_FILE_CREATE')
on_attachment_get = event.signal('ATTACHMENT_GET')
on_attachment_delete = event.signal('ATTACHMENT_DELETE')

def allowed_file(filename, allowed):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in allowed

def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

#/
class AttachmentAPI(Resource):
	@login_required
	def post(self):
		file = request.files['file']

		on_save_tmp_file.send(
			current_app._get_current_object(),
			event_name=on_save_tmp_file.name,
			user=current_user,
			data={'file': file.filename})

		if file and allowed_file(file.filename, current_app.config['ATTACHMENT_ALLOWED_EXTENSIONS']):
			name = str(uuid.uuid4()) + '.pdf'
			tmpName = os.path.join(current_app.config['UPLOAD_FOLDER'], name)
			file.save(tmpName)
			current_app.logger.debug("Temporarily saved tmpUpload/" + name)
			return {'name': name} 
		return False
api.add_resource(AttachmentAPI, '')

# /post/post_id
class AttachmentPostIdAPI(Resource):
	@login_required
	def get(self, post_id):
		# TODO: change to return list of attachments
		file = FilesForPosts.query.filter_by(posts_id = post_id).first()

		on_attachment_get.send(
			current_app._get_current_object(),
			event_name=on_attachment_get.name,
			user=current_user,
			data={'post_id': post_id})

		if file:
			return {'file': marshal(file, dataformat.getFilesForPosts())}
		return {'file': False}
api.add_resource(AttachmentPostIdAPI, '/post/<int:post_id>')

# /post/post_id/file_id
class AttachmentPostIdFileIdAPI(Resource):
	@login_required
	def delete(self, post_id, file_id):
		file = FilesForPosts.query.filter_by(posts_id=post_id).filter_by(id=file_id).first()

		on_attachment_delete.send(
			current_app._get_current_object(),
			event_name=on_attachment_delete.name,
			user=current_user,
			data={'post_id':post_id, 'file_id':file_id})

		if file:
			tmpName = os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], file.name)
			os.remove(tmpName)
			db.session.delete(file)
			db.session.commit()
			current_app.logger.debug("SuccessFully deleted " + file.name + " for post " + str(post_id))

api.add_resource(AttachmentPostIdFileIdAPI, '/post/<int:post_id>/<int:file_id>')

# move file from temporary location to "permanent" location
# makes a FilesForPosts entry
def addNewFile(alias, name, course_id, question_id, post_id):
	tmpName = str(course_id) + '_' + str(question_id) + '_' + str(post_id) + '.pdf'
	shutil.move(os.path.join(current_app.config['UPLOAD_FOLDER'], name), os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmpName))
	file = FilesForPosts(posts_id=post_id, author_id=current_user.id, name=tmpName, alias=alias)
	db.session.add(file)
	db.session.commit()
	current_app.logger.debug("Moved and renamed " + name + " from " + current_app.config['UPLOAD_FOLDER'] + " to " + os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmpName))

# delete file from Post
def deleteFile(post_id):
	# TODO: delete ALL files under post with post_id
	file = FilesForPosts.query.filter_by(posts_id=post_id).first()
	if file:
		os.remove(os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], file.name))
		current_app.logger.debug("Successfully deleted file " + file.name + " for post " + str(post_id))