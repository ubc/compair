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
		'student_no': fields.String,
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

def getCourses(include_details=True):
	format = {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String
	}
	if (include_details):
		details = {
			'available': fields.Boolean,
			'criteriaandcourses': fields.Nested(getCriteriaAndCourses()),
			'enable_student_create_questions': fields.Boolean,
			'enable_student_create_tags': fields.Boolean,
			'modified': fields.DateTime,
			'created': fields.DateTime
		}
		format.update(details)
	return format

def getCoursesAndUsers(restrict_user=True, include_user=True, include_groups=True):
	format = {
		'id': fields.Integer,
		'courses_id': fields.Integer,
		'usertypeforcourse': fields.Nested(getUserTypesForCourse()),
		'modified': fields.DateTime,
		'created': fields.DateTime
	}
	if include_user:
		format['user'] = fields.Nested(getUsers(restrict_user))
	if include_groups:
		format['groups'] = fields.Nested(getGroupsAndUsers())
	return format

def getGroupsAndUsers(restrict_user=True):
	format = {
		'groups_id': fields.Integer,
		'groups_name': fields.String
	}

	if not restrict_user:
		format['user'] = fields.Nested(getUsers(restrict_user))
	return format

def getGroups():
	format = {
		'id': fields.Integer,
		'name': fields.String
	}
	return format

def getCriteria():
	format = {
		'id': fields.Integer,
		'name': fields.String,
		'description': fields.String,
		'modified': fields.DateTime,
		'created': fields.DateTime,
		'users_id': fields.Integer,
		'default': fields.Boolean,
		'judged': fields.Boolean
	}
	return format

def getCriteriaAndCourses():
	format = {
		'id': fields.Integer,
		'criterion': fields.Nested(getCriteria()),
		'courses_id': fields.Integer,
		'active': fields.Boolean,
		'inQuestion': fields.Boolean
	}
	return format

def getCriteriaAndPostsForQuestions():
	format = {
		'id': fields.Integer,
		'criterion': fields.Nested(getCriteria()),
		'active': fields.Boolean
	}
	return format

def getPosts(restrict_users=True):
	return {
		'id': fields.Integer,
		'user': fields.Nested(getUsers(restrict_users)),
		'course': fields.Nested(getCourses()),
		'content': fields.String,
		'modified': fields.DateTime,
		'created': fields.DateTime,
		'files': fields.Nested(getFilesForPosts())
	}

def getPostsForQuestions(restrict_users=True, include_answers=True):
	post = getPosts(restrict_users)
	del post['course']
	ret = {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'title': fields.String,
		'answers_count': fields.Integer,
		'modified': fields.DateTime,
		'comments_count': fields.Integer,
		'available': fields.Boolean,
		'criteria': fields.Nested(getCriteriaAndPostsForQuestions()),
		'answer_period': fields.Boolean,
		'judging_period': fields.Boolean,
		'after_judging': fields.Boolean,
		'answer_start': fields.DateTime,
		'answer_end': fields.DateTime,
		'judge_start': fields.DateTime,
		'judge_end': fields.DateTime,
		'can_reply': fields.Boolean,
		'num_judgement_req': fields.Integer,
		'selfevaltype_id': fields.Integer,
		'judged': fields.Boolean,
		'evaluation_count': fields.Integer
	}
	if include_answers:
		answer = getPostsForAnswers(restrict_users)
		ret['answers'] = fields.List(fields.Nested(answer))
	return ret

def getPostsForAnswers(restrict_users=True, include_comments=True):
	post = getPosts(restrict_users)
	comments = getPostsForAnswersAndPostsForComments(restrict_users)
	score = getScores()
	del post['course']
	ret = {
		'id': fields.Integer,
		'post': fields.Nested(post),
		'scores': fields.Nested(score),
		'flagged': fields.Boolean,
		'questions_id': fields.Integer
	}
	# can see who flagged this post if user can view unrestricted data
	if not restrict_users:
		ret['flagger'] = fields.Nested(getUsers(restrict_users))
	if include_comments:
		ret['comments'] = fields.List(fields.Nested(comments))
		ret['comments_count'] = fields.Integer
		ret['private_comments_count'] = fields.Integer
		ret['public_comments_count'] = fields.Integer
	return ret

def getPostsForComments(retrict_users=True):
	post = getPosts(retrict_users)
	del post['course']
	return {
		'id': fields.Integer,
		'post': fields.Nested(post)
	}

def getPostsForQuestionsAndPostsForComments(restrict_users=True):
	comment = getPostsForComments(restrict_users)
	return {
		'id': fields.Integer,
		'postsforcomments': fields.Nested(comment),
		'content': fields.String
	}

def getPostsForAnswersAndPostsForComments(restrict_users=True):
	comment = getPostsForQuestionsAndPostsForComments(restrict_users)
	comment['selfeval'] = fields.Boolean
	comment['evaluation'] = fields.Boolean
	comment['type'] = fields.Integer
	return comment

def getFilesForPosts():
	return {
		'id': fields.Integer,
		'posts_id': fields.Integer,
		'name': fields.String,
		'alias': fields.String
	}

def getSelfEvalTypes():
	return {
		'id': fields.Integer,
		'name': fields.String
	}

def getAnswerPairings(include_answers=False):
	ret = {
		'id': fields.Integer,
		'questions_id': fields.Integer,
		'answers_id1': fields.Integer,
		'answers_id2': fields.Integer
	}
	if include_answers:
		ret['answer1'] = fields.Nested(getPostsForAnswers(include_comments=False))
		ret['answer2'] = fields.Nested(getPostsForAnswers(include_comments=False))
	return ret

def getJudgements():
	return {
		'id': fields.Integer,
		'answerpairing': fields.Nested(getAnswerPairings()),
		'users_id': fields.Integer,
		'answers_id_winner': fields.Integer,
		'question_criterion': fields.Nested(getCriteriaAndPostsForQuestions())
	}

def getPostsForJudgements(restrict_users=True):
	judgement = getJudgements()
	comment = getPostsForComments(restrict_users)
	return {
		'postsforcomments': fields.Nested(comment),
		'judgement': fields.Nested(judgement)
	}

def getImportUsersResults(restrict_users=True):
	user = getUsers(restrict_users)
	return {
		'user': fields.Nested(user),
		'message': fields.String
	}

def getEvalComments():
	answer = {'id': fields.Integer, 'feedback': fields.String}
	return {
		'user_id': fields.Integer,
		'name': fields.String,
		'avatar': fields.String,
		'criteriaandquestions_id': fields.Integer,
		'answerpairings_id': fields.Integer,
		'content': fields.String,
		'selfeval': fields.Boolean,
		'created': fields.DateTime,
		'answer1': fields.Nested(answer),
		'answer2': fields.Nested(answer),
		'winner': fields.Integer
	}

def getScores():
	return {
		'id': fields.Integer,
		'criteriaandquestions_id': fields.Integer,
		'answers_id': fields.Integer,
		'rounds': fields.Integer,
		'wins': fields.Integer,
		'score': fields.Float,
		'normalized_score': fields.Integer
	}
