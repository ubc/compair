"""
    Test package, also includes default settings for test environment
"""

test_app_settings = {
    'DEBUG': False,
    # disable this for now, since Flask-Login will ignore the login_required
    # decorator if this is true. Not sure if this is required for testing,
    # so leaving it here for now in case other stuff breaks in the future.
    # 'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_ECHO': False,
    'CSRF_ENABLED': False
}
