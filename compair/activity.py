import json
import datetime
from enum import Enum
from hashlib import md5
from six import text_type

from flask import session as sess
from flask_login import user_logged_in, user_logged_out
from flask_sqlalchemy import Model
from flask_login import UserMixin

from .models import ActivityLog, User
from .core import db


def log(sender, event_name='UNKNOWN', **extra):
    params = dict({'event': event_name})

    if 'user' in extra and hasattr(extra['user'], 'id'):
        params['user_id'] = extra['user'].id
    elif 'user_id' in extra:
        params['user_id'] = extra['user_id']

    if 'course' in extra and hasattr(extra['course'], 'id'):
        params['course_id'] = extra['course'].id
    elif 'course_id' in extra:
        params['course_id'] = extra['course_id']

    if 'data' in extra:
        if isinstance(extra['data'], str):
            params['data'] = extra['data']
        else:
            params['data'] = json.dumps(extra['data'], cls=JSONDateTimeEncoder)
    if 'status' in extra:
        params['status'] = extra['status']
    if 'message' in extra:
        params['message'] = extra['message']
    if 'session_token' in sess:
        params['session_id'] = md5(sess['session_token'].encode('UTF-8')).hexdigest()

    activity = ActivityLog(**params)
    db.session.add(activity)
    db.session.commit()


@user_logged_in.connect
def logged_in_wrapper(sender, user, **extra):
    log(sender, 'USER_LOGGED_IN', user=user, **extra)


@user_logged_out.connect
def logged_out_wrapper(sender, user, **extra):
    log(sender, 'USER_LOGGED_OUT', user=user, **extra)


class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return text_type(obj.value)
        else:
            return json.JSONEncoder.default(self, obj)
