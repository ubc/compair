import os
import uuid
import csv
import string

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
from .attachment import random_generator, allowed_file

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

new_course_user_parser = RequestParser()
new_course_user_parser.add_argument('usertypesforcourse_id', type=int)

#upload file column name to index number
USERNAME = 0
STUDENTNO = 1
FIRSTNAME = 2
LASTNAME = 3
EMAIL = 4
DISPLAYNAME = 5
PASSWORD = 6

# events
on_classlist_get = event.signal('CLASSLIST_GET')
on_classlist_upload = event.signal('CLASSLIST_UPLOAD')
on_classlist_enrol = event.signal('CLASSLIST_ENROL')
on_classlist_unenrol = event.signal('CLASSLIST_UNENROL')
on_classlist_instructor_label = event.signal('CLASSLIST_INSTRUCTOR_LABEL_GET')
on_classlist_instructor = event.signal('CLASSLIST_INSTRUCTOR_GET')
on_classlist_student = event.signal('CLASSLIST_STUDENT_GET')

def display_name_generator(role="Student"):
	return role.lower()+"_"+random_generator(8, string.digits)

def import_users(course_id, users):
	invalids = [] # invalid entries - eg. invalid # of columns
	# store unique user identifiers - eg. student number - throws error if duplicate in file
	exist_usernames = []
	exist_studentnos = []
	exist_displaynames = []
	count = 0 # store number of successful enrolments

	# create / update users in file
	normal_user = UserTypesForSystem.query.filter_by(name = UserTypesForSystem.TYPE_NORMAL).first().id
	for user in users:
		length = len(user)
		if (length < 1):
			continue	# skip empty row

		# TEMP USER
		temp = Users()
		temp.username = user[USERNAME] if length > USERNAME and user[USERNAME] else None
		temp.student_no = user[STUDENTNO] if length > STUDENTNO and user[STUDENTNO] else None
		temp.firstname = user[FIRSTNAME] if length > FIRSTNAME and user[FIRSTNAME] else None
		temp.lastname = user[LASTNAME] if length > LASTNAME and user[LASTNAME] else None
		temp.email = user[EMAIL] if length > EMAIL and user[EMAIL] else None
		temp.displayname = user[DISPLAYNAME] if length > DISPLAYNAME and user[DISPLAYNAME] else None

		# VALIDATION
		# validate username
		if not temp.username:
			invalids.append({'user': temp, 'message': 'The username is required.'})
			continue
		elif temp.username in exist_usernames:
			invalids.append({'user': temp, 'message': 'This username already exists in the file.'})
			continue

		u = Users.query.filter_by(username=temp.username).first()
		update = True
		if not u:
			u = Users(username=temp.username)
			update = False

		temp.password = user[PASSWORD] if length > PASSWORD and user[PASSWORD] else temp.username

		# validate student number (if not None)
		if temp.student_no:
			student_no_exist = Users.query.filter_by(student_no=temp.student_no).first()
			# invalid if exists but not the same user
			if update and student_no_exist and student_no_exist.id != u.id:
				invalids.append({'user': temp, 'message': 'This student number already exists in the system.'})
				continue
			# invalid if already showed up in file
			elif not update and temp.student_no in exist_studentnos:
				invalids.append({'user': temp, 'message': 'This student number already exists in the file.'})
				continue
			# invalid if student number already exists in the system
			elif not update and student_no_exist:
				invalids.append({'user': temp, 'message': 'This student number already exists in the system.'})
				continue

		# validate display name
		if temp.displayname:
			display_name_exists = Users.query.filter_by(displayname=temp.displayname).first()
			# reset to None when invalid
			if update and ((display_name_exists and display_name_exists != u.id) or (temp.displayname in exist_displaynames)):
				temp.displayname = None
			elif not update and (display_name_exists or temp.displayname in exist_displaynames):
				temp.displayname = None

		# update
		if update:
			u.student_no = temp.student_no if temp.student_no else u.student_no
			u.firstname = temp.firstname if temp.firstname else u.firstname
			u.lastname = temp.lastname if temp.lastname else u.lastname
			u.email = temp.email if temp.email else u.email
			u.displayname = temp.displayname if temp.displayname else u.displayname
		# create
		else:
			u = temp
			u.usertypesforsystem_id = normal_user
			if not temp.displayname:	# if display name is None
				tmp_displayname = display_name_generator()
				exists = Users.query.filter_by(displayname=tmp_displayname).scalar()
				while (exists is not None):
					tmp_displayname = display_name_generator()
					exists = Users.query.filter_by(displayname=tmp_displayname).scalar()
				u.displayname = tmp_displayname

		exist_usernames.append(u.username)
		exist_studentnos.append(u.student_no)
		exist_displaynames.append(u.displayname)
		db.session.add(u)
	db.session.commit()

	student = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first().id
	dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id
	enroled = CoursesAndUsers.query.filter_by(courses_id=course_id).\
		filter_by(usertypesforcourse_id=student).all()
	enroled = {e.users_id:e.users_id for e in enroled}

	# enrol valid users in file
	to_enrol = Users.query.filter(Users.username.in_(exist_usernames)).all()
	for user in to_enrol:
		enrol = CoursesAndUsers.query.filter_by(courses_id=course_id).filter_by(users_id=user.id).first()
		if not enrol:
			enrol = CoursesAndUsers(courses_id=course_id, users_id=user.id)
		enrol.usertypesforcourse_id = student
		db.session.add(enrol)
		if user.id in enroled:
			del enroled[user.id]
		count += 1
	db.session.commit()

	# unenrol users not in file anymore
	for userId in enroled:
		unenrol = CoursesAndUsers.query.filter_by(courses_id=course_id).filter_by(users_id=userId).first()
		unenrol.usertypesforcourse_id = dropped
		db.session.add(unenrol)
	db.session.commit()

	on_classlist_upload.send(
		current_app._get_current_object(),
		event_name=on_classlist_upload.name,
		user=current_user,
		course_id=course_id
	)

	return {
		'success': count,
		'invalids': marshal(invalids, dataformat.getImportUsersResults(False))
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
		if file and allowed_file(file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
			unique = str(uuid.uuid4())
			filename = unique + secure_filename(file.filename)
			tmpName = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
			os.remove(tmpName)
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

		on_classlist_enrol.send(
			current_app._get_current_object(),
			event_name=on_classlist_enrol.name,
			user=current_user,
			course_id=course_id,
			data={'user_id': user_id})

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

		on_classlist_unenrol.send(
			current_app._get_current_object(),
			event_name=on_classlist_unenrol.name,
			user=current_user,
			course_id=course_id,
			data={'user_id': user_id})

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

		on_classlist_instructor_label.send(
			current_app._get_current_object(),
			event_name=on_classlist_instructor_label.name,
			user=current_user,
			course_id=course_id)

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

		on_classlist_instructor.send(
			current_app._get_current_object(),
			event_name=on_classlist_instructor.name,
			user=current_user,
			course_id=course_id)

		return {'instructors': instructor_ids}
api.add_resource(InstructorsAPI, '/instructors')

# /students - return list of Students in the course
class StudentsAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		coursesandusers = CoursesAndUsers(courses_id=course_id)
		require(READ, course)
		students = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_STUDENT).all()

		if allow(READ, coursesandusers):
			users = [{'user': {'id': u.user.id, 'name': u.user.fullname}} for u in students]
		else:
			users = [{'user': {'id': u.user.id, 'name': u.user.displayname}} for u in students]

		on_classlist_student.send(
			current_app._get_current_object(),
			event_name=on_classlist_student.name,
			user=current_user,
			course_id=course_id
		)

		return {'students': users}
api.add_resource(StudentsAPI, '/students')
