# Specify what columns should be sent out by the API
from flask.ext.restful import fields

def getUserTypesForCourse():
	return {
		'id': fields.Integer,
		'name': fields.String
	}

def getUserTypesForSystem():
	return {
		'id': fields.Integer,
		'name': fields.String
	}

def getUsers(restrict_users=True):
	restricted = {
		'id': fields.Integer,
		'displayname': fields.String,
		'avatar': fields.String
	}
	if restrict_users:
		return restricted
	unrestricted = {
		'username': fields.String,
		'firstname': fields.String,
		'lastname': fields.String,
		'email': fields.String,
		'fullname': fields.String,
		'created': fields.DateTime,
		'modified': fields.DateTime,
		'lastonline': fields.DateTime,
		'usertypesforsystem_id': fields.Integer,
		'usertypeforsystem': fields.Nested(getUserTypesForSystem())
	}
	unrestricted.update(restricted)
	return unrestricted

def getCourses():
	return {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String,
		'available': fields.Boolean,
		'enable_student_posts': fields.Boolean,
		'enable_student_create_tags': fields.Boolean,
		'modified': fields.DateTime,
		'created': fields.DateTime
	}

def getCoursesAndUsers(restrict_user=True, include_user=True):
	format = {
		'id': fields.Integer,
		'course': fields.Nested(getCourses()),
		'usertypesforcourse': fields.Nested(getUserTypesForCourse()),
		'modified': fields.DateTime,
		'created': fields.DateTime
	}
	if include_user:
		format['user'] = getUsers(restrict_user)
	return format

def getPosts(restrict_users=True):
	return  {
		'id': fields.Integer,
		'user': fields.Nested(getUsers(restrict_users)),
		'course': fields.Nested(getCourses()),
		'content': fields.String,
		'modified': fields.DateTime,
		'created': fields.DateTime
	}

def getPostsForQuestions(restrict_users=True):
	post = getPosts(restrict_users)
	del post['course']
	return {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'title': fields.String,
		'modified': fields.DateTime
	}
