from flask import Flask
import flask.ext.restless
from flask.ext.login import LoginManager

import logging

from acj.database import init_db, db_session
from acj.models import Courses, Users
from acj.login import login_api

logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path="/static", static_folder="acj/static/")
# enable sessions by setting the secret key
app.secret_key = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"
# initialize database with sqlalchemy
init_db()
# initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# initialize Flask-Restless
manager = flask.ext.restless.APIManager(app, session=db_session)
manager.create_api(Courses, collection_name="courses")
manager.create_api(Users, exclude_columns=['password'], include_methods=['avatar'], collection_name="users")
# initialize rest of the api modules
app.register_blueprint(login_api)

@login_manager.user_loader
def load_user(user_id):
	logger.debug("User logging in, ID: " + user_id)
	return Users.query.get(int(user_id))

@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()

# start the webserver
app.run("0.0.0.0", 8080, debug=True)
