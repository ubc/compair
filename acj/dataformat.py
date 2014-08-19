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
		'avatar': fields.String,
		'lastonline': fields.DateTime,
		'created': fields.DateTime
	}
	if restrict_users:
		return restricted
	unrestricted = {
		'username': fields.String,
		'firstname': fields.String,
		'lastname': fields.String,
		'email': fields.String,
		'fullname': fields.String,
		'modified': fields.DateTime,
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
		'usertypeforcourse': fields.Nested(getUserTypesForCourse()),
		'modified': fields.DateTime,
		'created': fields.DateTime
	}
	if include_user:
		format['user'] = fields.Nested(getUsers(restrict_user))
	return format

def getCriteria():
	format = {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String,
		'modified': fields.DateTime,
		'created': fields.DateTime
	}
	return format

def getCriteriaAndCourses():
	format = {
		'id': fields.Integer,
		'criterion': fields.Nested(getCriteria()),
		'courses_id': fields.Integer
	}
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
		'answers': fields.List(fields.Nested(answer)),
		'comments_count': fields.Integer,
		'total_comments_count': fields.Integer,
		'available': fields.Boolean,
		'answer_period': fields.Boolean,
		'judging_period': fields.Boolean,
		'after_judging': fields.Boolean,
		'answer_start': fields.DateTime,
		'answer_end': fields.DateTime,
		'judge_start': fields.DateTime,
		'judge_end': fields.DateTime,
		'date_set': fields.Boolean
	}

def getPostsForAnswers(restrict_users=True, include_comments=True):
	post = getPosts(restrict_users)
	comments = getPostsForQuestionsOrAnswersAndPostsForComments(restrict_users)
	score = getScores()
	del post['course']
	ret = {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'scores': fields.Nested(score),
		'flagged': fields.Boolean
	}
	# can see who flagged this post if user can view unrestricted data
	if not restrict_users:
		ret['flagger'] = fields.Nested(getUsers(restrict_users))
	if include_comments:
		ret['comments'] = fields.List(fields.Nested(comments))
		ret['comments_count'] = fields.Integer
	return ret

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

def getAnswerPairings():
	return {
		'id': fields.Integer,
		'postsforquestions_id': fields.Integer,
		'postsforanswers_id1': fields.Integer,
		'postsforanswers_id2': fields.Integer
	}

def getJudgements():
	return {
		'id': fields.Integer,
		'answerpairing': fields.Nested(getAnswerPairings()),
		'users_id': fields.Integer,
		'postsforanswers_id_winner': fields.Integer,
		'course_criterion': fields.Nested(getCriteriaAndCourses())
	}

def getImportUsersResults(restrict_users=True):
	user = getUsers(restrict_users)
	return {
		'user': fields.Nested(user),
		'message': fields.String
	}

def getScores():
	return {
		'id': fields.Integer,
		'criteriaandcourses_id': fields.Integer,
		'postsforanswers_id': fields.Integer,
		'rounds': fields.Integer,
		'wins': fields.Integer,
		'score': fields.Float
	}
