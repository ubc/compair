import os

"""
    Default settings, if no other settings is specified, values here are used.
"""

DATABASE = {
    'drivername': 'mysql+pymysql',
    'host': 'localhost',
    'port': '3306',
    'username': 'compair',
    'password': 'compaircompair',
    'database': 'compair',
}

# enable sessions by setting the secret key
SECRET_KEY = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"

# save some system resources, (will be false by default in Flask-SQLAlchemy in a future release)
# we currently use SQLAlchemy event system directly
SQLALCHEMY_TRACK_MODIFICATIONS = False

# recycle connections after ~5 minutes
SQLALCHEMY_POOL_RECYCLE=299

# persistent directories for uploads and download
PERSISTENT_BASE = os.getcwd() + '/persistent'
REPORT_FOLDER = PERSISTENT_BASE + '/report'
UPLOAD_FOLDER = PERSISTENT_BASE + '/tmp'
ATTACHMENT_UPLOAD_FOLDER = PERSISTENT_BASE + '/pdf'

# file upload options
ATTACHMENT_ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_ALLOWED_EXTENSIONS = {'csv'}

PASSLIB_CONTEXT = 'default'

# make the session valid for a day
PERMANENT_SESSION_LIFETIME = 3600 * 24

# set celery tasks
CELERY_RESULT_BACKEND = None
CELERY_BROKER_URL = None
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_IMPORTS = ('compair.tasks.user_password', 'compair.tasks.lti_outcomes', 'compair.tasks.xapi_statement')
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True
}

# xAPI & Learning Record Stores (LRS)
XAPI_ENABLED = False
XAPI_APP_BASE_URL = None

LRS_STATEMENT_ENDPOINT = 'local' #url for LRS xAPI statements
LRS_AUTH = None
LRS_USERNAME = None
LRS_PASSWORD = None

LRS_ACTOR_ACCOUNT_USE_CAS = False # set to True to use CAS account information if available
LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER = None # set to a param field value to use or None to use unique_identifier
LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE = None # set to the url for the CAS account homepage

# where to retrieve assets, possible values 'cloud', 'local'
ASSET_LOCATION = 'cloud'
# compair-asset s3 location
ASSET_CLOUD_URI_PREFIX = 'https://d1flf4q1u9z72v.cloudfront.net/dist/'

# Google Analytic Tracking ID, setting this will enable tracking
GA_TRACKING_ID = None

# Login & Authentication methods
# Login via ComPAIR username & Password
APP_LOGIN_ENABLED = True
# Login via CAS
# if true requires additional CAS settings
CAS_LOGIN_ENABLED = True
# Login via LTI consumer
# if true requires record with oauth_consumer_key and oauth_consumer_secret in lti_consumer table
LTI_LOGIN_ENABLED = True

CAS_SERVER = 'http://localhost:8088'
CAS_AFTER_LOGIN = 'login_api.auth_cas'
CAS_AFTER_LOGOUT = None

# enter additional attributes to store in third_party_user table
CAS_ATTRIBUTES_TO_STORE = []