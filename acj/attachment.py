from bouncer.constants import EDIT, CREATE
from flask import Blueprint, Flask, request, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from acj import dataformat, db
from acj.authorization import allow, require
from acj.models import PostsForQuestions, FilesForPosts
from acj.util import new_restful_api
import os, uuid, shutil

attachment_api = Blueprint('attachment_api', __name__)
api = new_restful_api(attachment_api)

# TODO put in config file
UPLOAD_FOLDER = os.getcwd() + '/tmpUpload'
PERMANENT_UPLOAD_FOLDER = os.getcwd() + '/acj/static/pdf'
ALLOWED_EXTENSIONS = set(['pdf'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_UPLOAD_FOLDER'] = PERMANENT_UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#/
class AttachmentAPI(Resource):
	@login_required
	def post(self):
		file = request.files['file']
		if file and allowed_file(file.filename):
			name = str(uuid.uuid4()) + '.pdf'
			tmpName = os.path.join(app.config['UPLOAD_FOLDER'], name)
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
		if file:
			return {'file': marshal(file, dataformat.getFilesForPosts())}
		return {'file': False}
api.add_resource(AttachmentPostIdAPI, '/post/<int:post_id>')

# /post/post_id/file_id
class AttachmentPostIdFileIdAPI(Resource):
	@login_required
	def delete(self, post_id, file_id):
		file = FilesForPosts.query.filter_by(posts_id=post_id).filter_by(id=file_id).first()
		if file:
			tmpName = os.path.join(app.config['PERMANENT_UPLOAD_FOLDER'], file.name)
			os.remove(tmpName)
			db.session.delete(file)
			db.session.commit()
			current_app.logger.debug("SuccessFully deleted " + file.name + " for post " + str(post_id))

api.add_resource(AttachmentPostIdFileIdAPI, '/post/<int:post_id>/<int:file_id>')

# move file from temporary location to "permanent" location
# makes a FilesForPosts entry
def addNewFile(alias, name, course_id, question_id, post_id):
	tmpName = str(course_id) + '_' + str(question_id) + '_' + str(post_id) + '.pdf'
	shutil.move(os.path.join(app.config['UPLOAD_FOLDER'], name), os.path.join(app.config['PERMANENT_UPLOAD_FOLDER'], tmpName))
	file = FilesForPosts(posts_id=post_id, author_id=current_user.id, name=tmpName, alias=alias)
	db.session.add(file)
	db.session.commit()
	current_app.logger.debug("Moved and renamed " + name + " from " + app.config['UPLOAD_FOLDER'] + " to " + os.path.join(app.config['PERMANENT_UPLOAD_FOLDER'], tmpName))

# delete file from Post
def deleteFile(post_id):
	# TODO: delete ALL files under post with post_id
	file = FilesForPosts.query.filter_by(posts_id=post_id).first()
	if file:
		os.remove(os.path.join(app.config['PERMANENT_UPLOAD_FOLDER'], file.name))
		current_app.logger.debug("Successfully deleted file " + file.name + " for post " + str(post_id))