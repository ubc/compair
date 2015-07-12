"""
	The app core, initialize necessary objects
"""
from blinker import Namespace
from flask.ext.bouncer import Bouncer
from flask.ext.cas import CAS

from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy


# initialize database
db = SQLAlchemy(session_options={
	'expire_on_commit': False
})

# initialize Flask-Bouncer
bouncer = Bouncer()

# initialize Flask-Login
login_manager = LoginManager()

# initialize CAS
cas = CAS()

# check if the user is authenticated and used by api preprocessors
# def auth_func(*args, **kw):
# 	if not current_user.is_authenticated():
# 		raise ProcessingException(description='Not authenticated!', code=401)

# create custom namespace for signals
event = Namespace()
