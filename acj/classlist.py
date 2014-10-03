import os
import uuid
import csv
import string
import random

from bouncer.constants import EDIT, CREATE, READ
from flask import Blueprint, Flask, request, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from werkzeug.utils import secure_filename
from flask.ext.restful.reqparse import RequestParser
from . import dataformat

from .core import db

from .authorization import allow, require
from .core import event
from .models import CoursesAndUsers, Courses, Users, UserTypesForSystem, UserTypesForCourse
from .util import new_restful_api

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

new_course_user_parser = RequestParser()
new_course_user_parser.add_argument('usertypesforcourse_id', type=int)

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


# events
on_classlist_get = event.signal('CLASSLIST_GET')
on_classlist_upload = event.signal('CLASSSLIST_UPLOAD')

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def display_name_generator(firstname=None, role="Student"):
	name = firstname+"_" if firstname else ""
	return role.lower()+"_"+name+random_generator(4, string.digits)

def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def import_users(course_id, users):
	# initialize list of users and their statuses
	invalids = []	# invalid entry - eg. invalid # of columns
	success = []	# successfully enroled
	created = []	# successfully created new users
	dropped_users = []	# users not on new list; therefore dropped
	exist_displaynames = []

	# variables used in the intermediate steps
	valid = []	# successfully created new users' usernames
	normal_user = UserTypesForSystem.query.filter_by(name = UserTypesForSystem.TYPE_NORMAL).first().id
	if len(users) > 0: 	# check that there is a minimum of one entry
		length = len(users[0])		# get number of columns
	else:
		return {}

	# generate a list of existing users from the list of imported usernames
	usernames = [u[USERNAME] for u in users]
	exist_users = Users.query.filter(Users.username.in_(usernames)).all()
	exist_usernames = [e.username for e in exist_users]

	# generate a list of existing display names from list of imported dp names
	if length > DISPLAYNAME:
		displaynames = [u[DISPLAYNAME] for u in users]
		exist_users = Users.query.filter(Users.displayname.in_(displaynames)).all()
		exist_displaynames = [e.displayname for e in exist_users]
	for user in users:
		# user already exists
		if user[USERNAME] in exist_usernames:
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
		if length > DISPLAYNAME and user[DISPLAYNAME] != '' and user[DISPLAYNAME] not in exist_displaynames:
			u.displayname = user[DISPLAYNAME]
		else:
			# auto-generate if one is not given
			tmp_displayname = display_name_generator(u.firstname)
			exists = Users.query.filter(Users.displayname==tmp_displayname).scalar()
			while (exists is not None):
				tmp_displayname = display_name_generator(u.firstname)
				exists = Users.query.filter(Users.displayname==tmp_displayname).scalar()
			u.displayname = tmp_displayname

		# password
		if length > PASSWORD and user[PASSWORD] != '':
			u.password = user[PASSWORD]
		else:
			u.password = user[USERNAME]
		created.append({'user': u, 'message': 'created'})
		db.session.add(u)
		# add new user to list of existing users
		exist_usernames.append(u.username)
		exist_displaynames.append(u.displayname)
		valid.append(u.username)
	db.session.commit() # commit the new users first

	student = UserTypesForCourse.query.filter_by(name="Student").first().id
	dropped = UserTypesForCourse.query.filter_by(name="Dropped").first().id
	enroled = CoursesAndUsers.query.filter_by(courses_id=course_id).\
		filter(CoursesAndUsers.usertypesforcourse_id.in_([student, dropped])).all()
	enroled_userIds = [e.users_id for e in enroled]
	enroled_userIds = dict(zip(enroled_userIds, enroled_userIds))

	users = Users.query.filter(Users.username.in_(valid)).all()
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
		dropped = UserTypesForCourse.query.filter_by(name="Dropped").first().id
		classlist = CoursesAndUsers.query. \
			filter_by(courses_id=course_id).\
			filter(CoursesAndUsers.usertypesforcourse_id!=dropped).all()

		on_classlist_get.send(
			current_app._get_current_object(),
			event_name=on_classlist_get.name,
			user=current_user,
			course_id=course_id)

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
			current_app.logger.debug("Importing for course " + str(course_id) + " with " + filename)
			with open(tmpName, 'rU') as csvfile:
				spamreader = csv.reader(csvfile)
				users = []
				for row in spamreader:
					if row:
						users.append(row)
				results = import_users(course_id, users)
				on_classlist_upload.send(
					current_app._get_current_object(),
					event_name=on_classlist_upload.name,
					user=current_user,
					course_id=course_id)
			os.remove(os.path.join(app.config['UPLOAD_FOLDER'], tmpName))
			current_app.logger.debug("Class Import for course " + str(course_id) + " is successful. Removed file.")
			return results
		else:
			return {'error':'Wrong file type'}, 400
api.add_resource(ClasslistRootAPI, '')

class EnrolAPI(Resource):
	@login_required
	def post(self, course_id, user_id):
		course = Courses.query.get_or_404(course_id)
		user = Users.query.get_or_404(user_id)
		coursesandusers = CoursesAndUsers.query.filter_by(users_id=user.id, courses_id=course.id).first()
		if not coursesandusers:
			coursesandusers = CoursesAndUsers(courses_id = course.id)
		require(EDIT, coursesandusers)
		params = new_course_user_parser.parse_args()
		# defaults to instructor if no usertypesforcourse_id is given
		role_id = params.get('usertypesforcourse_id')
		if not role_id:
			role_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).first().id
		type = UserTypesForCourse.query.get_or_404(role_id)
		coursesandusers.users_id = user.id
		coursesandusers.usertypesforcourse_id = type.id
		result = {'user': {'id': user.id, 'fullname': user.fullname}, 'usertypesforcourse': {'id': type.id, 'name': type.name}}
		db.session.add(coursesandusers)
		db.session.commit()
		return result
	@login_required
	def delete(self, course_id, user_id):
		course = Courses.query.get_or_404(course_id)
		user = Users.query.get_or_404(user_id)
		coursesandusers = CoursesAndUsers.query.filter_by(users_id=user.id, courses_id=course.id).first_or_404()
		require(EDIT, coursesandusers)
		drop = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first()
		coursesandusers.usertypesforcourse_id = drop.id
		result = {'user': {'id': user.id, 'fullname': user.fullname}, 'usertypesforcourse': {'id': drop.id, 'name': drop.name}}
		db.session.add(coursesandusers)
		db.session.commit()
		return result
api.add_resource(EnrolAPI, '/<int:user_id>/enrol')

# /instructors/labels - return list of TAs and Instructors labels
class TeachersAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		instructors = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter(UserTypesForCourse.name.in_([UserTypesForCourse.TYPE_TA, UserTypesForCourse.TYPE_INSTRUCTOR])).all()
		instructor_ids = {u.users_id: u.usertypeforcourse.name for u in instructors}
		return {'instructors': instructor_ids}
api.add_resource(TeachersAPI, '/instructors/labels')

# /instructors - return list of Instructors in the course
class InstructorsAPI(Resource):
	@login_required
	def get(self, course_id):
		Courses.query.get_or_404(course_id)
		coursesandusers = CoursesAndUsers(courses_id=course_id)
		require(READ, coursesandusers)
		instructors = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).all()
		instructor_ids = {u.users_id: u.user.fullname for u in instructors}
		return {'instructors': instructor_ids}
api.add_resource(InstructorsAPI, '/instructors')

# /students - return list of Students in the course
class StudentsAPI(Resource):
	@login_required
	def get(self, course_id):
		Courses.query.get_or_404(course_id)
		coursesandusers = CoursesAndUsers(courses_id=course_id)
		require(READ, coursesandusers)
		students = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_STUDENT).all()
		student_ids = {u.users_id: u.user.fullname for u in students}
		return {'students': student_ids}
api.add_resource(StudentsAPI, '/students')
