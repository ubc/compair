import json
import os
import ssl
import requests
import re

from flask import Flask, redirect, session as sess, jsonify, url_for, make_response
from flask_bouncer import ensure
from jinja2 import Markup
from flask_login import current_user
from sqlalchemy.orm import joinedload
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import Unauthorized
from lxml.html.clean import clean_html
from celery.schedules import crontab

from .authorization import define_authorization
from .core import login_manager, bouncer, db, celery, abort, mail, impersonation
from .configuration import config
from .models import User, File
from .activity import log
from .api import register_api_blueprints, log_events, \
    register_demo_api_blueprints, log_demo_events, \
    register_learning_record_api_blueprints, impersonation as impersonation_api
from compair.learning_records import capture_events
from compair.notifications import capture_notification_events

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

_impersonation_url_whitelist = {}

def get_asset_names(app):
    manifest_path = app.static_folder + '/build/rev-manifest.json'
    if not os.path.exists(manifest_path):
        raise RuntimeError('Could not find ' + manifest_path + '. Run gulp prod first.')

    with open(manifest_path, 'r') as f:
        assets = json.load(f)

    return {'ASSETS': assets}

def get_asset_prefix(app):
    prefix = ''
    if app.config['ASSET_LOCATION'] == 'cloud':
        prefix = app.config['ASSET_CLOUD_URI_PREFIX']
    elif app.config['ASSET_LOCATION'] == 'local':
        prefix = app.static_url_path + '/dist/'
    else:
        app.logger.error('Invalid ASSET_LOCATION value ' + app.config['ASSET_LOCATION'] + '.')

    return {'ASSET_PREFIX': prefix}


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

def _populate_impersonation_url_whitelist():
    _impersonation_url_whitelist['GET'] = [
        re.compile('.*'),   # allow GET to any URL
    ]
    _impersonation_url_whitelist['DELETE'] = [
        re.compile('^' + re.escape(impersonation_api.IMPERSONATION_API_BASE_URL)),  # allow ending impersonation
    ]
    _impersonation_url_whitelist['POST'] = [
        re.compile('^' + re.escape('/api/learning_records')),   # allow XAPI/Caliper
    ]

def is_allowed_during_impersonation(request):
    # TODO if there is a performance issue, could hard-code and allow all GET requests to pass without using regex,
    # assuming most requests will be GET
    allowed = _impersonation_url_whitelist.get(request.method, [])
    for url in allowed:
        if url.match(request.full_path):
            return True
    return False

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

        # try disabling insecure request warnings (some versions of requests have import errors)
        try:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except ImportError:
            # Skip if requests does not have InsecureRequestWarning
            pass

    app.logger.debug("Application Configuration: " + str(app.config))

    # setup celery scheduled tasks
    if app.config.get('DEMO_INSTALLATION', False):
        #each day at 3am
        app.config.setdefault('CELERY_BEAT_SCHEDULE', {})['reset-demo-data-daily'] = {
            'task': "compair.tasks.demo.reset_demo",
            'schedule': crontab(hour=3, minute=0)
        }
    if (app.config.get('XAPI_ENABLED') and app.config.get('LRS_XAPI_STATEMENT_ENDPOINT') != 'local') or \
            (app.config.get('CALIPER_ENABLED') and app.config.get('LRS_CALIPER_HOST') != 'local'):
        # every 6 hours
        app.config.setdefault('CELERY_BEAT_SCHEDULE', {})['retry-sending-failed-learning-records'] = {
            'task': "compair.tasks.emit_learning_record.resend_learning_records",
            'schedule': crontab(hour='*/6', minute=0)
        }


    db.init_app(app)

    celery.conf.update(app.config.get_namespace('CELERY_'))

    mail.init_app(app)

    create_persistent_dirs(app.config, app.logger)

    # add include_raw to jinja templates
    app.jinja_env.globals['include_raw'] = lambda filename : Markup(app.jinja_loader.get_source(app.jinja_env, filename)[0])
    app.jinja_env.globals['clean_html'] = lambda html_string : clean_html(html_string) if html_string else ''
    if not skip_assets and not app.debug and not app.config.get('TESTING', False):
        assets = get_asset_names(app)
        app.config.update(assets)
        prefix = get_asset_prefix(app)
        app.config.update(prefix)

    # set resp headers
    def _resp_header_defaults(resp):
        headers_lower = set(k.lower() for k in resp.headers.keys())
        # avoid xss by telling browser not to guess the content type
        if 'x-content-type-options' not in headers_lower:
            resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp
    app.after_request(_resp_header_defaults)

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
            if sess.get('THIRD_PARTY_AUTH_ERROR_MSG'):
                msg = sess.pop('THIRD_PARTY_AUTH_ERROR_MSG')
                msg_type = sess.pop('THIRD_PARTY_AUTH_ERROR_TYPE')
                response = jsonify({'message': msg, 'status': 403, 'type': msg_type})
                response.status_code = 403
                return response
            abort(401, title="User Logged Out", message="You must be logged in to see this page. Please log in to continue.")

        # Flask-Bouncer initialization
        bouncer.init_app(app)

        # Assigns permissions to the current logged in user
        @bouncer.authorization_method
        def bouncer_define_authorization(user, they):
            original_user = None
            if impersonation.is_impersonating():
                original_user = User.query.get(impersonation.get_impersonation_original_user_id())
            define_authorization(user, they, original_user)

        # Loads the current logged in user. Note that although Flask-Bouncer advertises
        # compatibility with Flask-Login, it looks like it's compatible with an older
        # version than we're using, so we have to override their loader.
        @bouncer.user_loader
        def bouncer_user_loader():
            return current_user

        # setup impersonation
        if app.config.get('IMPERSONATION_ENABLED', False):
            impersonation.init_app(app)

            @impersonation.user_loader
            def load_user(user_id):
                return User.query.get(int(user_id))

            @impersonation.authorize
            def authorize(act_as_user_id):
                try:
                    ensure(impersonation.IMPERSONATE, load_user(act_as_user_id))
                    return True
                except Unauthorized as e:
                    abort(403, title="Impersonation Failed", message="Sorry, your role in the system does not allow you see a student's view.")

                return False    # normally won't reach here

            @impersonation.process_request
            def process_request(request):
                """
                Callback invoked during impersonation to check incoming requests
                """
                if current_user and current_user.is_authenticated and not current_user.is_anonymous:
                    if not is_allowed_during_impersonation(request):
                        abort(403, title="Action Temporarily Disabled", \
                            message="Sorry, you can't perform that action in the student view. Only the real student can do this.", \
                            disabled_by_impersonation=True)

                # proceed with the request
                return None

        # register regex route converter
        app.url_map.converters['regex'] = RegexConverter

        app = register_api_blueprints(app)

        if app.config.get('MAIL_NOTIFICATION_ENABLED', False):
            capture_notification_events()

        if app.config.get('DEMO_INSTALLATION', False):
            log_demo_events(log)
            app = register_demo_api_blueprints(app)

        if app.config.get('XAPI_ENABLED', False) or app.config.get('CALIPER_ENABLED', False) :
            capture_events()
            app = register_learning_record_api_blueprints(app)

    return app

log_events(log)
_populate_impersonation_url_whitelist()
