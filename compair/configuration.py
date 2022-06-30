"""
This module manages to load the application configuration from various places. (Priority from high to low)

* Environment variables
* config.py
* Default Settings: compair/settings.py

The configuration will be merged in above order and config variable is available for the final result.

The database settings can be defined as a string in DATABASE_URI or as a dictionary in DATABASE in different
configuration locations. (Priority from high to low)

* Environment variables
* DATABASE_URI
* DATABASE

Currently the supported environment variables:

* OpenShift
* DATABASE_URI
"""

import os
import json
import re
import pytz
import time

from distutils.util import strtobool
from flask import Config
from sqlalchemy.engine.url import URL

config = Config('.')
config.from_object('compair.settings')
config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py'), silent=True)

db_conn_options = ''
if os.environ.get('DB_CONN_OPTIONS'):
    options_dict = json.loads(os.environ.get('DB_CONN_OPTIONS'))
    for key in options_dict:
        db_conn_options = db_conn_options + ('?' if db_conn_options == '' else '&') + \
            key + '=' + options_dict.get(key)

if os.environ.get('OPENSHIFT_MYSQL_DB_HOST'):
    config['SQLALCHEMY_DATABASE_URI'] = URL(
        'mysql+pymysql',
        host=os.getenv('OPENSHIFT_MYSQL_DB_HOST', 'localhost'),
        port=os.getenv('OPENSHIFT_MYSQL_DB_PORT', '3306'),
        username=os.getenv('OPENSHIFT_MYSQL_DB_USERNAME', 'compair'),
        password=os.getenv('OPENSHIFT_MYSQL_DB_PASSWORD', 'compair'),
        database=os.getenv('OPENSHIFT_GEAR_NAME', 'compair'),
    )
elif os.environ.get('DB_HOST') or os.environ.get('DB_PORT') or os.environ.get('DB_USERNAME') \
        or os.environ.get('DB_PASSWORD') or os.environ.get('DB_NAME'):
    config['SQLALCHEMY_DATABASE_URI'] = str(URL(
        os.getenv('DB_DRIVER', 'mysql+pymysql'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '3306'),
        username=os.getenv('DB_USERNAME', 'compair'),
        password=os.getenv('DB_PASSWORD', 'compair'),
        database=os.getenv('DB_NAME', 'compair'),
    )) + db_conn_options
elif os.environ.get('DATABASE_URI'):
    config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
elif "DATABASE" in config and 'DATABASE_URI' not in config:
    config['SQLALCHEMY_DATABASE_URI'] = URL(**config['DATABASE'])
elif "DATABASE_URI" in config:
    config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_URI']

# clear DATABASE value
if 'DATABASE' in config:
    del config['DATABASE']

env_overridables = [
    'LOGIN_ADDITIONAL_INSTRUCTIONS_HTML',
    'CAS_SERVER', 'CAS_AUTH_PREFIX', 'CAS_LOGIN_HTML',
    'CAS_ATTRIBUTE_USER_ROLE', 'CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD',
    'CAS_ATTRIBUTE_FIRST_NAME', 'CAS_ATTRIBUTE_LAST_NAME',
    'CAS_ATTRIBUTE_STUDENT_NUMBER', 'CAS_ATTRIBUTE_EMAIL',
    'SAML_UNIQUE_IDENTIFIER', 'SAML_SETTINGS_FILE', 'SAML_LOGIN_HTML',
    'SAML_METADATA_URL', 'SAML_METADATA_ENTITY_ID',
    'SAML_ATTRIBUTE_USER_ROLE', 'SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD',
    'SAML_ATTRIBUTE_FIRST_NAME', 'SAML_ATTRIBUTE_LAST_NAME',
    'SAML_ATTRIBUTE_STUDENT_NUMBER', 'SAML_ATTRIBUTE_EMAIL',
    'SECRET_KEY', 'REPORT_FOLDER', 'UPLOAD_FOLDER',
    'ATTACHMENT_UPLOAD_FOLDER', 'ASSET_LOCATION', 'ASSET_CLOUD_URI_PREFIX',
    'CELERY_RESULT_BACKEND', 'CELERY_BROKER_URL', 'CELERY_TIMEZONE',
    'LRS_APP_BASE_URL',
    'LRS_XAPI_STATEMENT_ENDPOINT', 'LRS_XAPI_AUTH', 'LRS_XAPI_USERNAME', 'LRS_XAPI_PASSWORD',
    'LRS_CALIPER_HOST', 'LRS_CALIPER_API_KEY',
    'LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE',
    'KALTURA_SERVICE_URL', 'KALTURA_PARTNER_ID', 'KALTURA_USER_ID',
    'KALTURA_SECRET', 'KALTURA_PLAYER_ID',
    'MAIL_SERVER', 'MAIL_DEBUG', 'MAIL_USERNAME', 'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER', 'MAIL_SUPPRESS_SEND',
    'GA_TRACKING_ID', 'APP_TIMEZONE'
]

env_bool_overridables = [
    'APP_LOGIN_ENABLED', 'CAS_LOGIN_ENABLED', 'SAML_LOGIN_ENABLED', 'LTI_LOGIN_ENABLED',
    'CAS_USE_SAML', 'DEMO_INSTALLATION', 'SAML_EXPOSE_METADATA_ENDPOINT',
    'CELERY_TASK_ALWAYS_EAGER',
    'XAPI_ENABLED', 'CALIPER_ENABLED', 'LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER',
    'KALTURA_ENABLED', 'KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER',
    'EXPOSE_EMAIL_TO_INSTRUCTOR', 'EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR',
    'ALLOW_STUDENT_CHANGE_NAME', 'ALLOW_STUDENT_CHANGE_DISPLAY_NAME',
    'ALLOW_STUDENT_CHANGE_STUDENT_NUMBER', 'ALLOW_STUDENT_CHANGE_EMAIL',
    'MAIL_NOTIFICATION_ENABLED', 'MAIL_USE_TLS', 'MAIL_USE_SSL', 'MAIL_ASCII_ATTACHMENTS',
    'ENFORCE_SSL', 'IMPERSONATION_ENABLED'
]

env_int_overridables = [
    'ATTACHMENT_UPLOAD_LIMIT', 'LRS_USER_INPUT_FIELD_SIZE_LIMIT',
    'MAIL_PORT', 'MAIL_MAX_EMAILS', 'CELERY_WORKER_MAX_TASKS_PER_CHILD',
    'CELERY_WORKER_MAX_MEMORY_PER_CHILD'
]

env_set_overridables = [
    'ATTACHMENT_ALLOWED_EXTENSIONS', 'ATTACHMENT_PREVIEW_EXTENSIONS',
    'KALTURA_VIDEO_EXTENSIONS', 'KALTURA_AUDIO_EXTENSIONS',
    'SAML_INSTRUCTOR_ROLE_VALUES', 'CAS_INSTRUCTOR_ROLE_VALUES'
]

env_json_overridables = [
    'SAML_SETTINGS', 'SQLALCHEMY_ENGINE_OPTIONS'
]

for env in env_overridables:
    if os.environ.get(env) != None:
        config[env] = os.environ.get(env)

for env in env_bool_overridables:
    if os.environ.get(env) != None:
        config[env] = bool(strtobool(os.environ.get(env)))

for env in env_int_overridables:
    if os.environ.get(env) != None:
        config[env] = int(os.environ.get(env))

for env in env_set_overridables:
    if os.environ.get(env) != None:
        config[env] = set(re.split('\s+', os.environ.get(env).strip()))

for env in env_json_overridables:
    if os.environ.get(env) != None:
        config[env] = json.loads(os.environ.get(env))

# KALTURA_ATTACHMENT_EXTENSIONS is the combination of both KALTURA_VIDEO_EXTENSIONS and KALTURA_AUDIO_EXTENSIONS
config['KALTURA_ATTACHMENT_EXTENSIONS'] = config['KALTURA_VIDEO_EXTENSIONS'] | config['KALTURA_AUDIO_EXTENSIONS']
# force cas & saml login to be disabled when demo installation
if config['DEMO_INSTALLATION'] == True:
    config['APP_LOGIN_ENABLED'] = True
    config['CAS_LOGIN_ENABLED'] = False
    config['SAML_LOGIN_ENABLED'] = False

# configuring APP_TIMEZONE
if not(config['APP_TIMEZONE'] in pytz.all_timezones):
    config['APP_TIMEZONE'] = time.strftime('%Z')
