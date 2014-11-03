from bouncer.constants import READ, CREATE, DELETE
from flask import Blueprint, current_app, request
from flask.ext.restful import Resource, marshal_with, marshal, reqparse
from flask_login import login_required
from werkzeug.utils import secure_filename
from flask.ext.restful.reqparse import RequestParser
from flask.ext.login import current_user

from . import dataformat
from .authorization import require, allow
from .core import db, event
from .models import Groups, GroupsAndUsers, CoursesAndUsers, Users, Courses, UserTypesForCourse
from .util import new_restful_api
from .attachment import allowed_file

import uuid, os, csv, json

groups_api = Blueprint('groups_api', __name__)
api = new_restful_api(groups_api)

groups_users_api = Blueprint('groups_users_api', __name__)
apiU = new_restful_api(groups_users_api)

USER_IDENTIFIER = 0
GROUP_NAME = 1

import_parser = RequestParser()
import_parser.add_argument('userIdentifier', type=str, required=True)

# events
on_group_create = event.signal('GROUP_POST')
on_group_delete = event.signal('GROUP_DELETE')
on_group_course_get = event.signal('GROUP_COURSE_GET')
on_group_import = event.signal('GROUP_IMPORT')
on_group_get = event.signal('GROUP_GET')

on_group_user_create = event.signal('GROUP_USER_CREATE')
on_group_user_delete = event.signal('GROUP_USER_DELETE')

def import_members(course_id, identifier, members):
	# initialize list of users and their statuses
	invalids = []  #invalid entry - eg. no group name
	user_infile = [] # for catching duplicate users
	count = 0	# keep track of active groups
	dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

	# require all rows to have two columns if there are a minimum of one entry
	if len(members) > 0 and len(members[0]) != 2:
		return {'success': count}
	elif identifier not in ['username', 'student_no']:
		invalids.append({'member': {}, 'message': 'A valid user identifier is not given.'})
		return {'success': count, 'invalids': invalids}

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

		if identifier == 'username':
			user = Users.query.filter_by(username=member[USER_IDENTIFIER]).first()
			value = identifier
		else:
			user = Users.query.filter_by(student_no=member[USER_IDENTIFIER]).first()
			value = 'student number'

		if not user:
			invalids.append({'member': json.dumps(member), 'message': 'No user with this '+value+' exists.'})
			continue

		enroled = CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==course_id,
			CoursesAndUsers.usertypesforcourse_id!=dropped, CoursesAndUsers.users_id==user.id).first()
		if enroled:
			group_member = GroupsAndUsers.query.filter_by(groups_id=active_groups[member[GROUP_NAME]])\
				.filter_by(users_id=user.id).first()
			if group_member:
				group_member.active = 1
			else:
				group_member = GroupsAndUsers()
				group_member.groups_id = active_groups[member[GROUP_NAME]]
				group_member.users_id = user.id
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
def unenrol_group(course_id, user_id):
		# authenticate
		group = Groups(courses_id=course_id)
		member = GroupsAndUsers(group=group)
		require(DELETE, member)

		# remove the user from all other groups in the course
		groups = GroupsAndUsers.query.filter_by(users_id=user_id, active=True).join(Groups)\
			.filter_by(courses_id=course_id).all()
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

		on_group_course_get.send(
			current_app._get_current_object(),
			event_name=on_group_course_get.name,
			user=current_user,
			course_id=course_id
		)

		return {'groups': marshal(groups, dataformat.getGroups())}
	@login_required
	def post(self, course_id):
		Courses.query.get_or_404(course_id)
		group = Groups(courses_id=course_id)
		require(CREATE, group)
		params = import_parser.parse_args()
		identifier = params.get('userIdentifier')
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
				results = import_members(course_id, identifier, members)
				# TODO: event
			os.remove(tmpName)

			on_group_import.send(
				current_app._get_current_object(),
				event_name=on_group_import.name,
				user=current_user,
				course_id=course_id,
				data={'filename': tmpName}
			)

			current_app.logger.debug("Group Import for course " + str(course_id) + " is successful. Removed file.")
			return results
		else:
			return {'error': 'Wrong file type'}, 400
api.add_resource(GroupRootAPI, '')

# /:group_id
class GroupIdAPI(Resource):
	@login_required
	def get(self, course_id, group_id):
		course = Courses.query.get_or_404(course_id)
		group = Groups(courses_id=course.id)
		member = GroupsAndUsers(group=group)
		require(READ, member)
		restrict_users = not allow(READ, member)

		members = GroupsAndUsers.query.filter_by(groups_id=group_id, active=True).all()

		on_group_get.send(
			current_app._get_current_object(),
			event_name=on_group_get.name,
			user=current_user,
			course_id=course_id,
			data={'group_id': group_id})

		return {'students': marshal(members, dataformat.getGroupsAndUsers(restrict_users))}
api.add_resource(GroupIdAPI, '/<int:group_id>')

# /users/:user_id/groups/:group_id
class GroupUserIdAPI(Resource):
	@login_required
	def post(self, course_id, user_id, group_id):
		# check group exists (and active) and in course
		group = Groups.query.filter_by(courses_id=course_id, id=group_id, active=True).first_or_404()
		dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

		# check that the user is enroled in the course
		CoursesAndUsers.query.filter(CoursesAndUsers.courses_id==course_id,
			CoursesAndUsers.users_id==user_id,CoursesAndUsers.usertypesforcourse_id!=dropped)\
			.first_or_404()

		member = GroupsAndUsers(group=group)
		require(CREATE, member)

		# remove user from all groups in course
		unenrol_group(course_id, user_id)

		group = GroupsAndUsers.query.filter_by(users_id=user_id, groups_id=group_id).first()
		if group:
			group.active = True
		else:
			group = GroupsAndUsers()
			group.groups_id = group_id
			group.users_id = user_id
		db.session.add(group)

		on_group_user_create.send(
			current_app._get_current_object(),
			event_name=on_group_user_create.name,
			user=current_user,
			course_id=course_id,
			data={'user_id': user_id})

		db.session.commit()
		return {'groups_name': group.groups_name}
apiU.add_resource(GroupUserIdAPI, '/<int:group_id>')

# /users/:user_id/groups
class GroupUserAPI(Resource):
	@login_required
	def delete(self, course_id, user_id):
		Courses.query.get_or_404(course_id)
		Users.query.get_or_404(user_id)
		CoursesAndUsers.query.filter_by(courses_id=course_id, users_id=user_id).first_or_404()
		unenrol_group(course_id, user_id)

		on_group_user_delete.send(
			current_app._get_current_object(),
			event_name=on_group_user_delete,
			user=current_user,
			course_id=course_id,
			data={'user_id': user_id})

		return {'user_id': user_id, 'course_id': course_id}
apiU.add_resource(GroupUserAPI, '')
