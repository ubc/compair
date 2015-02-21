"""
This module manages to load the application configuration from various places. (Priority from high to low)

* Environment variables
* config.py
* Default Settings: acj/settings.py

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

from flask import Config
from sqlalchemy.engine.url import URL


config = Config('.')
config.from_object('acj.settings')
config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py'), silent=True)

if os.environ.get('OPENSHIFT_MYSQL_DB_HOST'):
	config['SQLALCHEMY_DATABASE_URI'] = URL({
		'drivername': 'mysql',
		'host': os.environ.get('OPENSHIFT_MYSQL_DB_HOST'),
		'port': os.environ.get('OPENSHIFT_MYSQL_DB_PORT'),
		'username': os.environ.get('OPENSHIFT_MYSQL_DB_USERNAME'),
		'password': os.environ.get('OPENSHIFT_MYSQL_DB_PASSWORD'),
		'database': os.environ.get('OPENSHIFT_GEAR_NAME'),
	})
elif os.environ.get('DATABASE_URI'):
	config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
elif "DATABASE" in config and 'DATABASE_URI' not in config:
	config['SQLALCHEMY_DATABASE_URI'] = URL(**config['DATABASE'])
elif "DATABASE_URI" in config:
	config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_URI']

# clear DATABASE value
if 'DATABASE' in config:
	del config['DATABASE']

env_overridables = ['CAS_SERVER', 'CAS_AFTER_LOGIN', 'REPORT_FOLDER',
					'CAS_LOGIN_ROUTE', 'CAS_LOGOUT_ROUTE',
					'CAS_LOGOUT_RETURN_URL', 'CAS_VERSION',
					'CAS_VALIDATE_ROUTE', 
					'SECRET_KEY', 'UPLOAD_FOLDER', 'ATTACHMENT_UPLOAD_FOLDER']

for env in env_overridables:
	if os.environ.get(env):
		config[env] = os.environ.get(env)

# print config
