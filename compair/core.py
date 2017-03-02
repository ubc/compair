"""
    The app core, initialize necessary objects
"""
from blinker import Namespace
from flask import session as sess
from flask_bouncer import Bouncer
from celery import Celery

from flask_login import LoginManager, user_logged_in
from flask_sqlalchemy import SQLAlchemy

from .configuration import config

# initialize database
db = SQLAlchemy(session_options={
    'expire_on_commit': False
})

# initialize Flask-Bouncer
bouncer = Bouncer()

# initialize Flask-Login
login_manager = LoginManager()

# initialize celery
celery = Celery(
    broker=config.get("CELERY_RESULT_BACKEND"),
    backend=config.get("CELERY_BROKER_URL")
)

# create custom namespace for signals
event = Namespace()

# subscribe user_logged_in signal to generate auth token
@user_logged_in.connect
def generate_session_token(sender, user, **extra):
    sess['session_token'] = user.generate_session_token()

