"""
    The app core, initialize necessary objects
"""
from blinker import Namespace
from flask import session
from flask.ext.bouncer import Bouncer
from flask.ext.cas import CAS

from flask.ext.login import LoginManager, user_logged_in
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

# create custom namespace for signals
event = Namespace()


# subscribe user_logged_in signal to generate auth token
@user_logged_in.connect
def generate_session_token(sender, user, **extra):
    session['session_token'] = user.generate_session_token()

