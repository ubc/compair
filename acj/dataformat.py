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

def getCriteria():
	return {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String,
		'modified': fields.DateTime,
		'created': fields.DateTime
	}

def getCriteriaAndCourses():
	return {
		'id': fields.Integer,
		'criteria': fields.Nested(getCriteria())
	}

def getCourses():
	return {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String,
		'available': fields.Boolean,
		'criteriaandcourses': fields.Nested(getCriteriaAndCourses()),
		'enable_student_create_questions': fields.Boolean,
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
		format['user'] = fields.Nested(getUsers(restrict_user))
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
	answer = getPostsForAnswers(restrict_users)
	del post['course']
	return {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'title': fields.String,
		'answers_count': fields.Integer,
		'modified': fields.DateTime,
		'answers': fields.List(fields.Nested(answer))
	}

def getPostsForAnswers(restrict_users=True):
	post = getPosts(restrict_users)
	comments = getPostsForQuestionsOrAnswersAndPostsForComments(restrict_users)
	del post['course']
	return {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'comments': fields.List(fields.Nested(comments))
	}

def getPostsForComments(retrict_users=True):
	post = getPosts(retrict_users)
	del post['course']
	return {
		'id': fields.Integer,
		'post': fields.Nested(post)
	}

def getPostsForQuestionsOrAnswersAndPostsForComments(restrict_users=True):
	comment = getPostsForComments(restrict_users)
	return {
		'id': fields.Integer,
		'postsforcomments': fields.Nested(comment),
		'content': fields.String
	}

