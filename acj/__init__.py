from flask import Flask, redirect
from flask.ext.login import current_user
from .authorization import define_authorization
from .core import login_manager, bouncer, db, cas
from .configuration import config
from .models import Users
from .login import authenticate


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
	from .answer import answers_api
	app.register_blueprint(answers_api,
		url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/answers')
	from .attachment import attachment_api
	app.register_blueprint(attachment_api,
		url_prefix='/api/tmpAttachment')
	from .comment import commentsforquestions_api
	app.register_blueprint(commentsforquestions_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/comments')
	from .comment import commentsforanswers_api
	app.register_blueprint(commentsforanswers_api, url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/answers/<int:answer_id>/comments')
	from .criteria import criteria_api
	app.register_blueprint(criteria_api, url_prefix='/api/courses/<int:course_id>/criteria')
	from .judgement import judgements_api
	app.register_blueprint(judgements_api,
		url_prefix='/api/courses/<int:course_id>/questions/<int:question_id>/judgements')


	@app.route('/')
	def route_root():
		username = cas.username
		user = Users.query.filter_by(username=username).first()
		if not user:
			app.logger.debug("Login failed, invalid username for: " + username)
		else:
			authenticate(user)

		return redirect('/static/index.html#/')

	return app

