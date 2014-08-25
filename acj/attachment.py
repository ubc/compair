from bouncer.constants import EDIT, CREATE
from flask import Blueprint, Flask, request
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource
from acj import db
from acj.authorization import allow, require
from acj.models import PostsForQuestions, FilesForPosts
from acj.util import new_restful_api
import os, uuid

attachment_api = Blueprint('attachment_api', __name__)
api = new_restful_api(attachment_api)

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
			return {'name': name} 
		return False
api.add_resource(AttachmentAPI, '')

# /id
class AttachmentIdAPI(Resource):
	@login_required
	def get(self, post_id):
		file = FilesForPosts.query.filter_by(posts_id = post_id).first()
		if file:
			return {'file': {'id': file.posts_id, 'alias': file.alias}}
		return {'file': False}
	@login_required
	def delete(self, post_id):
		file = FilesForPosts.query.filter_by(posts_id=post_id).first_or_404()
		tmpName = os.path.join(app.config['PERMANENT_UPLOAD_FOLDER'], file.name)
		os.remove(tmpName)
		db.session.delete(file)
		db.session.commit()
api.add_resource(AttachmentIdAPI, '/<int:post_id>')
