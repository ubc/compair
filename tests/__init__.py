"""
	Test package, also includes default settings for test environment
"""

test_app_settings = {
	'DEBUG': False,
	'TESTING': True,
	'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
	'SQLALCHEMY_ECHO': False,
	'CSRF_ENABLED': False
}
