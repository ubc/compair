from flask import Flask, redirect, session
from flask.ext.login import current_user

from .answer import on_answer_modified, on_answer_get, on_answer_list_get, on_answer_create, on_answer_flag
from .classlist import on_classlist_get, on_classlist_upload
from .comment import on_comment_modified, on_comment_get, on_comment_list_get, on_comment_create, on_comment_delete, \
	on_answer_comment_modified, on_answer_comment_get, on_answer_comment_list_get, on_answer_comment_create, \
	on_answer_comment_delete
from .course import on_course_modified, on_course_get, on_course_list_get, on_course_create
from .criteria import on_criteria_list_get, criteria_get, criteria_post, criteria_update
from .evalcomment import on_evalcomment_create
from .judgement import on_answer_pair_get, on_judgement_create
from .question import on_question_modified, on_question_get, on_question_list_get, on_question_create, \
	on_question_delete
from acj.users import on_user_modified, on_user_get, on_user_list_get, on_user_create, on_user_course_get, \
	on_user_password_update
from .authorization import define_authorization
from .core import login_manager, bouncer, db, cas
from .configuration import config
from .models import Users
from .login import authenticate
from .activity import log


def create_app(conf=config, settings_override={}):
	"""Return a :class:`Flask` application instance

	:param settings_override: override the default settings or settings in the configuration file
	"""
	app = Flask(__name__)
	app.config.update(conf)
	app.config.update(settings_override)

	app.logger.debug("Application Configuration: " + str(app.config))

	db.init_app(app)

	# Flask-Login initialization
	login_manager.init_app(app)
	# This is how Flask-Login loads the newly logged in user's information
	@login_manager.user_loader
	def load_user(user_id):
		app.logger.debug("User logging in, ID: " + user_id)
		return Users.query.get(int(user_id))

	app.config['CAS_SERVER'] = 'http://localhost:8088'
	app.config['CAS_AFTER_LOGIN'] = 'route_root'

	cas.init_app(app)

	# Flask-Bouncer initialization
	bouncer.init_app(app)
	# Assigns permissions to the current logged in user
	@bouncer.authorization_method
	def bouncer_define_authorization(user, they):
		define_authorization(user, they)
	# Loads the current logged in user. Note that although Flask-Bouncer advertises
	# compatibility with Flask-Login, it looks like it's compatible with an older
	# version than we're using, so we have to override their loader.
	@bouncer.user_loader
	def bouncer_user_loader():
		return current_user

	# Flask-Restless definitions
	# api_manager.init_app(
	# 	app,
	# 	flask_sqlalchemy_db=db,
	# 	preprocessors=dict(
	# 		GET_SINGLE=[auth_func],
	# 		GET_MANY=[auth_func],
	# 		POST=[auth_func],
	# 		DELETE=[auth_func],
	# 		PUT=[auth_func],
	# 		)
	# )

	# api_manager.create_api(
	# 	CoursesAndUsers
	# )

	# Initialize rest of the api modules
	from .course import courses_api
	app.register_blueprint(courses_api, url_prefix='/api/courses')
	from .classlist import classlist_api
	app.register_blueprint(classlist_api, url_prefix='/api/courses/<int:course_id>/users')
	from .login import login_api
	app.register_blueprint(login_api)
	from .users import users_api, user_types_api
	app.register_blueprint(users_api, url_prefix='/api/users')
	app.register_blueprint(user_types_api, url_prefix='/api/usertypes')
	from .question import questions_api
	app.register_blueprint(questions_api, url_prefix='/api/courses/<int:course_id>/questions')
	from .answer import answers_api, all_answers_api
	app.register_blueprint(answers_api,
		url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/answers')
	app.register_blueprint(all_answers_api,
		url_prefix='/api/courses/<int:course_id>/answers')
	from .attachment import attachment_api
	app.register_blueprint(attachment_api,
		url_prefix='/api/attachment')
	from .comment import commentsforquestions_api, commentsforanswers_api, usercommentsforanswers_api
	app.register_blueprint(commentsforquestions_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/comments')
	app.register_blueprint(commentsforanswers_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/answers/<int:answer_id>/comments')
	app.register_blueprint(usercommentsforanswers_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/answers/<int:answer_id>/users/comments')
	from .evalcomment import evalcomments_api
	app.register_blueprint(evalcomments_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/judgements/comments')
	from .criteria import coursescriteria_api, criteria_api
	app.register_blueprint(coursescriteria_api, url_prefix='/api/courses/<int:course_id>/criteria')
	app.register_blueprint(criteria_api, url_prefix='/api/criteria')
	from .judgement import judgements_api, all_judgements_api
	app.register_blueprint(judgements_api,
		url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/judgements')
	app.register_blueprint(all_judgements_api,
		url_prefix='/api/courses/<int:course_id>/judgements')


	@app.route('/')
	def route_root():
		username = cas.username

		if username is None:
			return redirect('/static/index.html#/')

		user = Users.query.filter_by(username=username).first()
		if not user:
			app.logger.debug("Login failed, invalid username for: " + username)
		else:
			authenticate(user)
			session['CAS_LOGIN'] = True

		return redirect('/static/index.html#/')

	return app


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
criteria_get.connect(log)
criteria_post.connect(log)
criteria_update.connect(log)

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

# evalcomment event
on_evalcomment_create.connect(log)
