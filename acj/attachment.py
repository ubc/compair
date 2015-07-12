import os
import uuid
import shutil
import random
import string

from flask import Blueprint, request, current_app
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


# /
class AttachmentAPI(Resource):
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
			current_app.logger.debug("Temporarily saved tmpUpload/" + name)
			return {'name': name} 
		return False
api.add_resource(AttachmentAPI, '')


# /post/post_id
class AttachmentPostIdAPI(Resource):
	@login_required
	def get(self, post_id):
		# TODO: change to return list of attachments
		uploaded_file = FilesForPosts.query.filter_by(posts_id=post_id).first()

		on_attachment_get.send(
			self,
			event_name=on_attachment_get.name,
			user=current_user,
			data={'post_id': post_id})

		if uploaded_file:
			return {'file': marshal(uploaded_file, dataformat.get_files_for_posts())}
		return {'file': False}
api.add_resource(AttachmentPostIdAPI, '/post/<int:post_id>')


# /post/post_id/file_id
class AttachmentPostIdFileIdAPI(Resource):
	@login_required
	def delete(self, post_id, file_id):
		uploaded_file = FilesForPosts.query.filter_by(posts_id=post_id).filter_by(id=file_id).first()

		on_attachment_delete.send(
			self,
			event_name=on_attachment_delete.name,
			user=current_user,
			data={'post_id': post_id, 'file_id': file_id})

		if uploaded_file:
			tmp_name = os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], uploaded_file.name)
			os.remove(tmp_name)
			db.session.delete(uploaded_file)
			db.session.commit()
			current_app.logger.debug("SuccessFully deleted " + uploaded_file.name + " for post " + str(post_id))

api.add_resource(AttachmentPostIdFileIdAPI, '/post/<int:post_id>/<int:file_id>')


# move file from temporary location to "permanent" location
# makes a FilesForPosts entry
def add_new_file(alias, name, course_id, question_id, post_id):
	tmp_name = str(course_id) + '_' + str(question_id) + '_' + str(post_id) + '.pdf'
	shutil.move(os.path.join(
		current_app.config['UPLOAD_FOLDER'], name),
		os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name))
	uploaded_file = FilesForPosts(
		posts_id=post_id, author_id=current_user.id,
		name=tmp_name, alias=alias)
	db.session.add(uploaded_file)
	db.session.commit()
	current_app.logger.debug(
		"Moved and renamed " + name + " from " + current_app.config['UPLOAD_FOLDER'] +
		" to " + os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], tmp_name))


# delete file from Post
def delete_file(post_id):
	# TODO: delete ALL files under post with post_id
	uploaded_file = FilesForPosts.query.filter_by(posts_id=post_id).first()
	if uploaded_file:
		os.remove(os.path.join(current_app.config['ATTACHMENT_UPLOAD_FOLDER'], uploaded_file.name))
		current_app.logger.debug("Successfully deleted file " + uploaded_file.name + " for post " + str(post_id))
