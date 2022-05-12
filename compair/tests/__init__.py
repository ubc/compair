# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
    Test package, also includes default settings for test environment
"""
import json
import os

saml_settings = None
with open(os.getcwd() +'/deploy/development/dev_saml_settings.json', 'r') as json_data_file:
    saml_settings = json.load(json_data_file)

test_app_settings = {
    'DEBUG': False,
    'TESTING': True,
    #'PRESERVE_CONTEXT_ON_EXCEPTION': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_ECHO': False,
    'CSRF_ENABLED': False,
    'PASSLIB_CONTEXT': 'plaintext',
    'ENFORCE_SSL': False,
    'CELERY_TASK_ALWAYS_EAGER': True,
    'XAPI_ENABLED': False,
    'CALIPER_ENABLED': False,
    'DEMO_INSTALLATION': False,
    'EXPOSE_EMAIL_TO_INSTRUCTOR': False,
    'EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR': False,
    'SAML_UNIQUE_IDENTIFIER': 'urn:oid:0.9.2342.19200300.100.1.1',
    'SAML_SETTINGS': saml_settings,
    'SAML_EXPOSE_METADATA_ENDPOINT': True,
    'ALLOW_STUDENT_CHANGE_NAME': False,
    'ALLOW_STUDENT_CHANGE_DISPLAY_NAME': False,
    'ALLOW_STUDENT_CHANGE_STUDENT_NUMBER': False,
    'ALLOW_STUDENT_CHANGE_EMAIL': False,
    'MAIL_NOTIFICATION_ENABLED': True,
    'MAIL_DEFAULT_SENDER': 'compair@example.com'
}