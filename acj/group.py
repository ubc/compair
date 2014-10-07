from bouncer.constants import MANAGE
from flask import Blueprint, current_app, request
from flask.ext.restful import Resource, marshal_with, marshal, reqparse
from flask_login import login_required
from werkzeug.utils import secure_filename

from . import dataformat
from .authorization import require
from .core import db, event
from .models import Groups, GroupsAndCoursesAndUsers, CoursesAndUsers, Users
from .util import new_restful_api
from .attachment import allowed_file

import uuid, os, csv, json

groups_api = Blueprint('groups_api', __name__)
api = new_restful_api(groups_api)

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

		enroled = CoursesAndUsers.query.filter_by(courses_id=course_id).join(Users)\
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

# /
class GroupRootAPI(Resource):
	@login_required
	def post(self, course_id):
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