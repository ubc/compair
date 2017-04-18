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
    'XAPI_ENABLED': True,
    'XAPI_APP_BASE_URL': 'https://localhost:8888/',
    'LRS_STATEMENT_ENDPOINT': 'local',
    'DEMO_INSTALLATION': False
}