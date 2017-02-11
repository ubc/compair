import json
import os
import ssl
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from flask import Flask, redirect, session as sess, jsonify, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload
from werkzeug.routing import BaseConverter
from flask_restplus import abort

from .authorization import define_authorization
from .core import login_manager, bouncer, db, celery
from .configuration import config
from .models import User, File
from .activity import log
from .api import register_api_blueprints, log_events
from compair.xapi import capture_xapi_events

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def get_asset_names(app):
    manifest_path = app.static_folder + '/build/rev-manifest.json'
    if not os.path.exists(manifest_path):
        raise RuntimeError('Could not find ' + manifest_path + '. Run gulp prod first.')

    with open(manifest_path, 'r') as f:
        assets = json.load(f)

    return {'ASSETS': assets}


def create_persistent_dirs(conf, logger):
    """
    creating persistent directories
    :param conf: Flask config object
    :param logger: Logging instance
    :return: None
    """
    for dir_name in ['REPORT_FOLDER', 'UPLOAD_FOLDER', 'ATTACHMENT_UPLOAD_FOLDER']:
        directory = conf[dir_name]
        logger.debug('checking directory {}'.format(directory))
        if not directory:
            logger.warning('{} is not defined.'.format(directory))
            continue
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                logger.warning('Failed to create directory {}.'.format(directory))
        elif not os.path.isdir(directory):
            logger.warning('{} is not a directory.'.format(directory))


def create_app(conf=config, settings_override=None, skip_endpoints=False, skip_assets=False):
    """Return a :class:`Flask` application instance

    :param conf: Flask config object
    :param settings_override: override the default settings or settings in the configuration file
    """
    if settings_override is None:
        settings_override = {}
    app = Flask(__name__, static_url_path='/app')
    app.config.update(conf)
    app.config.update(settings_override)

    if not app.config.get('ENFORCE_SSL', True):
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    app.logger.debug("Application Configuration: " + str(app.config))

    db.init_app(app)

    celery.conf.update(app.config)

    create_persistent_dirs(app.config, app.logger)

    if not skip_assets and not app.debug and not app.config.get('TESTING', False):
        assets = get_asset_names(app)
        app.config.update(assets)

    if not skip_endpoints:
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
            abort(401, title="Not Logged In", message="Authentication is required to access this area. Please log in to continue.")

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

        # register regex route converter
        app.url_map.converters['regex'] = RegexConverter

        app = register_api_blueprints(app)

    return app

log_events(log)
capture_xapi_events()