from flask import Flask
from flask.ext.login import current_user
from authorization import define_authorization
from core import login_manager, auth_func, api_manager, bouncer
from configuration import config
from course import courses_api
from models import CoursesAndUsers, Users
from users import users_api


def create_app(conf=config, settings_override={}):
	"""Return a :class:`Flask` application instance

	:param settings_override: override the default settings or settings in the configuration file
	"""
	app = Flask(__name__)
	app.config.update(conf)
	app.config.update(settings_override)

	app.logger.debug("Application Configuration: " + str(app.config))

	from core import db
	db.init_app(app)

	bouncer.init_app(app)

	login_manager.init_app(app)

	api_manager.init_app(
		app,
		flask_sqlalchemy_db=db,
		preprocessors=dict(
			GET_SINGLE=[auth_func],
			GET_MANY=[auth_func],
			POST=[auth_func],
			DELETE=[auth_func],
			PUT=[auth_func],
			)
	)

	api_manager.create_api(
		CoursesAndUsers
	)

	# initialize rest of the api modules
	from login import login_api
	app.register_blueprint(login_api)
	app.register_blueprint(users_api, url_prefix='/api/users')
	app.register_blueprint(courses_api, url_prefix='/api/courses')

	@login_manager.user_loader
	def load_user(user_id):
		app.logger.debug("User logging in, ID: " + user_id)
		return Users.query.get(int(user_id))

	# Looks like exception=None is required. Without it, I got sqlalchemy exception
	# about transactions needing to be rolled back, failing login. Seems to have
	# something to do with the session connection expiring and not being renewed?
	# def shutdown_session(exception=None):
	# 	app.db_session.remove()
	#
	# app.teardown_appcontext(shutdown_session)

	return app


@bouncer.authorization_method
def bouncer_define_authorization(user, they):
	define_authorization(user, they)
@bouncer.user_loader
def bouncer_user_loader():
	return current_user

