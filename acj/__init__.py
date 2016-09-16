from flask import Flask, redirect, session as sess, abort, jsonify
from flask_login import current_user
from sqlalchemy.orm import joinedload

from .authorization import define_authorization
from .core import login_manager, bouncer, db, cas
from .configuration import config
from .models import User
from .activity import log
from .api import register_api_blueprints, log_events

def create_app(conf=config, settings_override=None):
    """Return a :class:`Flask` application instance

    :param settings_override: override the default settings or settings in the configuration file
    """
    if settings_override is None:
        settings_override = {}
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
        return User.query. \
            options(joinedload("user_courses")). \
            get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if sess.get('CAS_AUTH_MSG'):
            msg = sess.pop('CAS_AUTH_MSG')
            response = jsonify({'message': msg, 'status': 403, 'type': 'CAS'})
            response.status_code = 403
            return response
        return abort(401)

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

    app = register_api_blueprints(app)

    return app

log_events(log)