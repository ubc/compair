"""
    The app core, initialize necessary objects
"""
from blinker import Namespace
from werkzeug.exceptions import HTTPException
from six import text_type
from flask import session as sess, abort as flask_abort
from flask_bouncer import Bouncer
from celery import Celery
from flask_mail import Mail
import string
import random

from flask_login import LoginManager, user_logged_in
from flask_sqlalchemy import SQLAlchemy

from .configuration import config
from .impersonation import Impersonation

# initialize database
db = SQLAlchemy(session_options={
    'expire_on_commit': False
})

# initialize Flask-Bouncer
bouncer = Bouncer()

# initialize Flask-Login
login_manager = LoginManager()

# initialize impersonation
impersonation = Impersonation()

# initialize celery
celery = Celery(
    backend=config.get("CELERY_RESULT_BACKEND"),
    broker=config.get("CELERY_BROKER_URL"),
    result_expires=(30 * 60), # 30 minutes
)

# initialize Flask-Mail
mail = Mail()

# create custom namespace for signals
event = Namespace()

# subscribe user_logged_in signal to generate auth token
@user_logged_in.connect
def generate_session_token(sender, user, **extra):
    sess['session_token'] = user.generate_session_token()

def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def allowed_file(filename, allowed):
    return '.' in filename and \
        filename.lower().rsplit('.', 1)[1] in allowed

def display_name_generator(role="student"):
    return "".join([role, '_', random_generator(8, string.digits)])

def abort(code=500, message=None, **kwargs):
    try:
        flask_abort(code)
    except HTTPException as e:
        if message:
            kwargs['message'] = text_type(message)
        if kwargs:
            e.data = kwargs
        raise