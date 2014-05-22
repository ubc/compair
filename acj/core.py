"""
	The app core, initialize necessary objects
"""
from flask.ext.bouncer import Bouncer

from flask.ext.login import LoginManager, current_user
from flask.ext.restless import ProcessingException, APIManager
from flask.ext.sqlalchemy import SQLAlchemy


# initialize database
db = SQLAlchemy()

# initialize Flask-Bouncer
bouncer = Bouncer()

# initialize Flask-Login
login_manager = LoginManager()

# initialize Flask-Restless
api_manager = APIManager()


# check if the user is authenticated and used by api preprocessors
def auth_func(*args, **kw):
	if not current_user.is_authenticated():
		raise ProcessingException(description='Not authenticated!', code=401)
