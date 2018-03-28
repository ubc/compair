"""
    Test package, also includes default settings for test environment
"""

test_app_settings = {
    'DEBUG': False,
    'TESTING': True,
    #'PRESERVE_CONTEXT_ON_EXCEPTION': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_ECHO': False,
    'CSRF_ENABLED': False,
    'PASSLIB_CONTEXT': 'plaintext',
    'ENFORCE_SSL': False,
    'CELERY_ALWAYS_EAGER': True,
    'XAPI_ENABLED': False,
    'XAPI_APP_BASE_URL': 'https://localhost:8888/',
    'LRS_STATEMENT_ENDPOINT': 'local',
    'DEMO_INSTALLATION': False,
    'EXPOSE_EMAIL_TO_INSTRUCTOR': False,
    'EXPOSE_CAS_USERNAME_TO_INSTRUCTOR': False,
    'ALLOW_STUDENT_CHANGE_NAME': False,
    'ALLOW_STUDENT_CHANGE_DISPLAY_NAME': False,
    'ALLOW_STUDENT_CHANGE_STUDENT_NUMBER': False,
    'ALLOW_STUDENT_CHANGE_EMAIL': False,
    'MAIL_NOTIFICATION_ENABLED': True,
    'MAIL_DEFAULT_SENDER': 'compair@example.com'
}