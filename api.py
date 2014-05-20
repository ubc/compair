from bouncer.constants import ALL, MANAGE, EDIT, READ
from flask import Flask
import flask.ext.restless
from flask.ext.login import LoginManager, current_user
from flask.ext.bouncer import Bouncer

import logging

from acj.authorization import define_authorization
from acj.database import init_db, db_session
from acj.models import Courses, CoursesAndUsers, Users

from acj.login import login_api
from acj.users import users_api

# logging configuration for the entire app
logging.basicConfig(level=logging.DEBUG)
# logging object for this module
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path="/static", static_folder="acj/static/")
# enable sessions by setting the secret key
app.secret_key = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"
# initialize database with sqlalchemy
init_db()
# initialize Flask-Bouncer
bouncer = Bouncer(app)
@bouncer.authorization_method
def bouncer_define_authorization(user, they):
	define_authorization(user, they)
@bouncer.user_loader
def bouncer_user_loader():
	return current_user
# initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# initialize Flask-Restless
manager = flask.ext.restless.APIManager(app, session=db_session)
manager.create_api(
	Courses,
	collection_name="courses" # default API route created is the table name,
								# which results in caps in url /api/Courses.
								# this overrides that so we get the standard
								# lower case /api/courses
)

manager.create_api(
	CoursesAndUsers
)

# initialize rest of the api modules
app.register_blueprint(login_api)
app.register_blueprint(users_api, url_prefix='/api/users')


@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

# Looks like exception=None is required. Without it, I got sqlalchemy exception
# about transactions needing to be rolled back, failing login. Seems to have
# something to do with the session connection expiring and not being renewed?
@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()

# start the web server
app.run("0.0.0.0", 8080, debug=True)
