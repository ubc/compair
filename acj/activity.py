import json
from flask import session
from flask.ext.login import user_logged_in, user_logged_out
from acj.answer import on_answer_create, on_answer_list_get, on_answer_get, on_answer_modified, on_answer_flag
from acj.classlist import on_classlist_upload, on_classlist_get
from acj.comment import on_comment_modified, on_comment_get, on_comment_list_get, on_comment_create, \
	on_answer_comment_create, on_answer_comment_list_get, on_answer_comment_get, on_answer_comment_modified, \
	on_answer_comment_delete, on_comment_delete
from acj.criteria import on_criteria_list_get
from acj.judgement import on_judgement_create, on_answer_pair_get
from course import on_course_create, on_course_list_get, on_course_get, on_course_modified
from models import Activities

from acj import db
from question import on_question_create, on_question_list_get, on_question_get, on_question_modified, on_question_delete
from users import on_user_modified, on_user_create, on_user_list_get, on_user_get, on_user_password_update, \
	on_user_course_get


def log(sender, event_name='UNKNOWN', **extra):
	params = dict({'event': event_name})
	if 'user' in extra:
		params['users_id'] = extra['user'].id
	elif 'user_id' in extra:
		params['users_id'] = extra['user_id']
	if 'course' in extra:
		params['courses_id'] = extra['course'].id
	elif 'course_id' in extra:
		params['courses_id'] = extra['course_id']
	if 'data' in extra:
		if isinstance(extra['data'], basestring):
			params['data'] = extra['data']
		else:
			params['data'] = json.dumps(extra['data'])
	if 'status' in extra:
		params['status'] = extra['status']
	if 'message' in extra:
		params['message'] = extra['message']
	if '_id' in session:
		params['session_id'] = session['_id']

	activity = Activities(**params)
	db.session.add(activity)
	db.session.commit()


@user_logged_in.connect
def logged_in_wrapper(sender, user, **extra):
	log(sender, 'USER_LOGGED_IN', user=user, **extra)


@user_logged_out.connect
def logged_out_wrapper(sender, user, **extra):
	log(sender, 'USER_LOGGED_OUT', user=user, **extra)

# user events
on_user_modified.connect(log)
on_user_get.connect(log)
on_user_list_get.connect(log)
on_user_create.connect(log)
on_user_course_get.connect(log)
on_user_password_update.connect(log)

# course events
on_course_modified.connect(log)
on_course_get.connect(log)
on_course_list_get.connect(log)
on_course_create.connect(log)

# question events
on_question_modified.connect(log)
on_question_get.connect(log)
on_question_list_get.connect(log)
on_question_create.connect(log)
on_question_delete.connect(log)

# comment events
on_comment_modified.connect(log)
on_comment_get.connect(log)
on_comment_list_get.connect(log)
on_comment_create.connect(log)
on_comment_delete.connect(log)

# answer comment events
on_answer_comment_modified.connect(log)
on_answer_comment_get.connect(log)
on_answer_comment_list_get.connect(log)
on_answer_comment_create.connect(log)
on_answer_comment_delete.connect(log)

# criteria events
on_criteria_list_get.connect(log)

# answer events
on_answer_modified.connect(log)
on_answer_get.connect(log)
on_answer_list_get.connect(log)
on_answer_create.connect(log)
on_answer_flag.connect(log)

# judgement events
on_answer_pair_get.connect(log)
on_judgement_create.connect(log)

# classlist events
on_classlist_get.connect(log)
on_classlist_upload.connect(log)
