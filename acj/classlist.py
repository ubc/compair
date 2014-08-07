from bouncer.constants import EDIT, CREATE
from flask import Blueprint, Flask, request
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from acj import dataformat, db
from acj.authorization import allow, require
from acj.models import CoursesAndUsers, Courses, Users, UserTypesForSystem, UserTypesForCourse
from acj.util import new_restful_api
from werkzeug.utils import secure_filename
import os, uuid, csv

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

#upload file column name to index number
USERNAME = 0
FIRSTNAME = 1
LASTNAME = 2
EMAIL = 3
DISPLAYNAME = 4
PASSWORD = 5

UPLOAD_FOLDER = os.getcwd() + '/tmpUpload'
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def import_users(course_id, users):
	# initialize list of users and their statuses
	invalids = []	# invalid entry - eg. invalid # of columns
	success = []	# successfully enroled
	created = []	# successfully created new users
	dropped_users = []	# users not on new list; therefore dropped

	# variables used in the intermediate steps
	valid = []	# successfully created new users' usernames
	normal_user = UserTypesForSystem.query.filter_by(name = 'Normal User').first().id
	if len(users) > 0: 	# check that there is a minimum of one entry
		length = len(users[0])		# get number of columns
	else:
		return {}

	# generate a list of existing users from the list of imported usernames
	usernames = [u[USERNAME] for u in users]
	exist_users = Users.query.filter(Users.username.in_(usernames)).all()
	exist_usernames = [e.username for e in exist_users]
	existing_users = dict(zip(exist_usernames, exist_users))

	# generate a list of existing display names from list of imported dp names
	if length > DISPLAYNAME:
		displaynames = [u[DISPLAYNAME] for u in users]
		exist_users = Users.query.filter(Users.displayname.in_(displaynames)).all()
		exist_displaynames = [e.displayname for e in exist_users]
		exist_displaynames = dict(zip(exist_displaynames, exist_displaynames))	
	for user in users:	
		# user already exists
		if user[USERNAME] in existing_users.keys():
			valid.append(user[USERNAME])
			continue 
		elif user[USERNAME] == '':
			invalids.append({'user': user, 'message':'The username is required.'})
			continue	# skip blank row
		u = Users()
		u.username = user[USERNAME]

		# firstname
		if length > FIRSTNAME and user[FIRSTNAME] != '':
			u.firstname = user[FIRSTNAME]
		else:
			u.firstname = None

		# lastname
		if length > LASTNAME and user[LASTNAME] != '':
			u.lastname = user[LASTNAME]
		else:
			u.lastname = None

		# email
		if length > EMAIL and user[EMAIL] != '':
			u.email = user[EMAIL]
		else:
			u.email = None

		# default to normal user
		u.usertypesforsystem_id = normal_user

		# display name
		if length > DISPLAYNAME and user[DISPLAYNAME] != '' and user[DISPLAYNAME] not in exist_displaynames.keys():
			u.displayname = user[DISPLAYNAME]
		else:
			u.displayname = None

		# password
		if length > PASSWORD and user[PASSWORD] != '':
			u.password = user[PASSWORD]
		else:
			u.password = user[USERNAME]
		created.append({'user': u, 'message': 'created'})
		db.session.add(u)
		valid.append(u.username)
	db.session.commit() # commit the new users first

	student = UserTypesForCourse.query.filter_by(name="Student").first().id
	dropped = UserTypesForCourse.query.filter_by(name="Dropped").first().id
	enroled = CoursesAndUsers.query.filter_by(courses_id=course_id).\
		filter(CoursesAndUsers.usertypesforcourse_id.in_([student, dropped])).all()
	enroled_userIds = [e.users_id for e in enroled]
	enroled_userIds = dict(zip(enroled_userIds, enroled_userIds))

	users = Users.query.filter(Users.username.in_(valid)).all()
	usernames = [u.username for u in users]
	usernames = dict(zip(usernames, users))
	for user in users:
		enrol = CoursesAndUsers()
		if user.id in enroled_userIds.keys():
			enrol = CoursesAndUsers.query.filter_by(courses_id=course_id).filter_by(users_id=user.id).first()
			enrol.usertypesforcourse_id = student
			db.session.commit()
			del enroled_userIds[enrol.users_id]
			success.append({'user':user, 'message':"Enroled"})
			continue
		enrol.courses_id = course_id
		enrol.users_id = user.id
		enrol.usertypesforcourse_id = student
		db.session.add(enrol)
		success.append({'user':user, 'message':"Enroled"})
	db.session.commit()

	for id in enroled_userIds:
		enrol = CoursesAndUsers.query.filter_by(courses_id=course_id).filter_by(users_id=id).first()
		if enrol.usertypesforcourse_id == student:
			dropped_users.append({'user':enrol.user, 'message':'User Dropped'})
		enrol.usertypesforcourse_id = dropped
		db.session.commit()
	
	return {
		'created': marshal(created, dataformat.getImportUsersResults(False)),
		'dropped': marshal(dropped_users, dataformat.getImportUsersResults(False)),
		'success':marshal(success, dataformat.getImportUsersResults(False)),
		'invalids':marshal(invalids, dataformat.getImportUsersResults(False))
	}

# /
class ClasslistRootAPI(Resource):

	# TODO Pagination
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		#only users that can edit the course can view enrolment
		require(EDIT, course)
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course_id))
		include_user = True
		classlist = CoursesAndUsers.query. \
			filter(CoursesAndUsers.courses_id == course_id).all()
		return {'objects':marshal(classlist, dataformat.getCoursesAndUsers(restrict_users, include_user))}
	@login_required
	def post(self, course_id):
		require(CREATE, Users())
		file = request.files['file']
		if file and allowed_file(file.filename):
			unique = str(uuid.uuid4())
			filename = unique + secure_filename(file.filename)
			tmpName = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(tmpName)
			with open(tmpName, 'rU') as csvfile:
				spamreader = csv.reader(csvfile)
				users = []
				for row in spamreader:
					if row:
						users.append(row)
				results = import_users(course_id, users)
			return results
		else:
			return {'error':'Wrong file type'}, 400
api.add_resource(ClasslistRootAPI, '') 
