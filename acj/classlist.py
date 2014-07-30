from bouncer.constants import EDIT
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from acj import dataformat, db
from acj.authorization import allow, require
from acj.models import CoursesAndUsers, Courses, Users
from acj.util import new_restful_api

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

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
api.add_resource(ClasslistRootAPI, '') 
