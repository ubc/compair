from bouncer.constants import READ, POST, DELETE
from flask import Blueprint, current_app, request
from flask.ext.restful import Resource, marshal_with, marshal, reqparse
from flask_login import login_required
from werkzeug.utils import secure_filename

from . import dataformat
from .authorization import require
from .core import db, event
from .models import Groups, GroupsAndCoursesAndUsers, CoursesAndUsers, Users, Courses, UserTypesForCourse
from .util import new_restful_api
from .attachment import allowed_file

import uuid, os, csv, json

groups_api = Blueprint('groups_api', __name__)
api = new_restful_api(groups_api)

groups_users_api = Blueprint('groups_users_api', __name__)
apiU = new_restful_api(groups_users_api)

USER_IDENTIFIER = 0
GROUP_NAME = 1

# events
#on_group_create = event.signal('GROUP_POST')
#on_group_disable = event.signal('GROUP_DELETE')

def import_members(course_id, members):
	# initialize list of users and their statuses
	invalids = []  #invalid entry - eg. no group name
	user_infile = [] # for catching duplicate users
	count = 0	# keep track of active groups
	dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

	# require at least one entry and all rows to have 2 columns
	if len(members) < 1 and len(members[0]) != 2:
		return {'success': count}

	# make all groups and members inactive initially
	exist_groups = Groups.query.filter_by(courses_id=course_id).all()
	for group in exist_groups:
		group.active = 0
		db.session.add(group)
		for member in group.members:
			member.active = 0
			db.session.add(member)
	db.session.commit()

	# add groups
	groups = set(g[GROUP_NAME] for g in members)
	for group_name in groups:
		# invalid group name
		if not group_name:
			# skip for now - generate errors below
			continue

		group = Groups.query.filter_by(courses_id=course_id, name=group_name).first()
		if group:	# existing group
			group.active = 1
		else:		# new group
			group = Groups()
			group.name = group_name
			group.courses_id = course_id
		db.session.add(group)
		count += 1
	db.session.commit()

	active_groups = Groups.query.filter_by(courses_id=course_id, active=True).all()
	active_groups = {g.name:g.id for g in active_groups}

	# enrol users to groups
	for member in members:
		if member[USER_IDENTIFIER] in user_infile:
			message = 'This user already exists in the file.'
			invalids.append({'member': json.dumps(member), 'message': message})
			continue
		if not member[GROUP_NAME]:
			message = 'The group name is invalid.'
			invalids.append({'member': json.dumps(member), 'message': message})
			continue

		enroled = CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==course_id,
			CoursesAndUsers.usertypesforcourse_id!=dropped).join(Users)\
			.filter_by(username=member[USER_IDENTIFIER]).first()
		if enroled:
			group_member = GroupsAndCoursesAndUsers.query.filter_by(groups_id=active_groups[member[GROUP_NAME]])\
				.filter_by(coursesandusers_id=enroled.id).first()
			if group_member:
				group_member.active = 1
			else:
				group_member = GroupsAndCoursesAndUsers()
				group_member.groups_id = active_groups[member[GROUP_NAME]]
				group_member.coursesandusers_id = enroled.id
			user_infile.append(member[USER_IDENTIFIER])
			db.session.add(group_member)
		else:
			message = 'The user is not enroled in the course'
			invalids.append({'member': json.dumps(member), 'message': message})
			continue
	db.session.commit()

	return {
		'success': count,
		'invalids': invalids
	}

# remove the user from all other groups in the course
def unenrol_group(coursesandusers_id):
		# remove the user from all other groups in the course
		groups = GroupsAndCoursesAndUsers.query.filter_by(coursesandusers_id=coursesandusers_id, active=True).all()
		for group in groups:
			group.active = False
			db.session.add(group)
		db.session.commit()

# /
class GroupRootAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		group = Groups(courses_id=course_id)
		require(READ, group)
		groups = Groups.query.filter(Groups.courses_id==course.id, Groups.active).all()
		return {'groups': marshal(groups, dataformat.getGroups())}
	@login_required
	def post(self, course_id):
		Courses.query.get_or_404(course_id)
		group = Groups(courses_id=course_id)
		require(POST, group)
		# require(CREATE, Groups())
		file = request.files['file']
		if file and allowed_file(file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
			unique = str(uuid.uuid4())
			filename = unique + secure_filename(file.filename)
			tmpName = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
			file.save(tmpName)
			current_app.logger.debug("Import groups for course "+str(course_id)+" with "+ filename)
			with open(tmpName, 'rU') as csvfile:
				spamreader = csv.reader(csvfile)
				members = []
				for row in spamreader:
					if row:
						members.append(row)
				results = import_members(course_id, members)
				# TODO: event
			os.remove(tmpName)
			current_app.logger.debug("Group Import for course " + str(course_id) + " is successful. Removed file.")
			return results
		else:
			return {'error': 'Wrong file type'}, 400
api.add_resource(GroupRootAPI, '')

# /users/:user_id/groups/:group_id
class GroupUserIdAPI(Resource):
	@login_required
	def post(self, course_id, user_id, group_id):
		# check group exists (and active) and in course
		Groups.query.filter_by(courses_id=course_id, id=group_id, active=True).first_or_404()
		dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

		# check that the user is enroled in the course
		coursesandusers = CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==course_id,
			CoursesAndUsers.users_id==user_id,CoursesAndUsers.usertypesforcourse_id!=dropped)\
			.first_or_404()

		member = GroupsAndCoursesAndUsers(coursesandusers=coursesandusers)
		require(POST, member)

		# remove user from all groups in course
		unenrol_group(coursesandusers.id)

		group = GroupsAndCoursesAndUsers.query.filter_by(coursesandusers_id=coursesandusers.id,
			groups_id=group_id).first()
		if group:
			group.active = True
		else:
			group = GroupsAndCoursesAndUsers()
			group.groups_id = group_id
			group.coursesandusers_id = coursesandusers.id
		db.session.add(group)
		db.session.commit()
		return {'groups_name': group.groups_name}
apiU.add_resource(GroupUserIdAPI, '/<int:group_id>')

# /users/:user_id/groups
class GroupUserAPI(Resource):
	@login_required
	def delete(self, course_id, user_id):
		dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id
		# check that the user is enroled in the course
		coursesandusers = CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==course_id,
			CoursesAndUsers.users_id==user_id,CoursesAndUsers.usertypesforcourse_id!=dropped)\
			.first_or_404()

		member = GroupsAndCoursesAndUsers(coursesandusers=coursesandusers)
		require(DELETE, member)

		unenrol_group(coursesandusers.id)
		return {'user_id': user_id, 'course_id': course_id}
apiU.add_resource(GroupUserAPI, '')
