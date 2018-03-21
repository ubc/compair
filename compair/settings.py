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
ATTACHMENT_UPLOAD_FOLDER = PERSISTENT_BASE + '/attachment'
ATTACHMENT_UPLOAD_LIMIT = 262144000 #1024 * 1024 * 250 -> max 250MB

# file upload options
ATTACHMENT_ALLOWED_EXTENSIONS = {'pdf','mp3','mp4','webm','jpg','jpeg','png'}
UPLOAD_ALLOWED_EXTENSIONS = {'csv'}

PASSLIB_CONTEXT = 'default'

ERROR_404_HELP = False

# make the session valid for a day
PERMANENT_SESSION_LIFETIME = 3600 * 24

# set celery tasks
CELERY_RESULT_BACKEND = None
CELERY_BROKER_URL = None
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_IMPORTS = ['compair.tasks']
CELERY_TIMEZONE = 'America/Vancouver'
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
# limit user generated content field text size limit
LRS_USER_INPUT_FIELD_SIZE_LIMIT = 1048576 #1024 * 1024 -> max 1MB

LRS_ACTOR_ACCOUNT_USE_CAS = False # set to True to use CAS account information if available
LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER = None # set to a param field value to use or None to use unique_identifier
LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE = None # set to the url for the CAS account homepage

# where to retrieve assets, possible values 'cloud', 'local'
ASSET_LOCATION = 'cloud'
# compair-asset s3 location
ASSET_CLOUD_URI_PREFIX = 'https://d1flf4q1u9z72v.cloudfront.net/dist/'

# Google Analytic Tracking ID, setting this will enable tracking
GA_TRACKING_ID = None

# Used by ComPAIR demo instances
# Demo instances allow user to create accounts of any role on the login screen and
# schedule automatic database resets daily
# Do not enable in any non-demo environment
DEMO_INSTALLATION = False

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
CAS_AUTH_PREFIX = '/cas'
CAS_USE_SAML = False

# kaltura integration defaults
KALTURA_ENABLED = False
KALTURA_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
KALTURA_AUDIO_EXTENSIONS = {'wav', 'mp3'}

# Mail
MAIL_NOTIFICATION_ENABLED = False

# Privacy data settings
EXPOSE_EMAIL_TO_INSTRUCTOR = False
EXPOSE_CAS_USERNAME_TO_INSTRUCTOR = False

# Control which profile information a student can edit
ALLOW_STUDENT_CHANGE_NAME = True
ALLOW_STUDENT_CHANGE_DISPLAY_NAME = True
ALLOW_STUDENT_CHANGE_STUDENT_NUMBER = True
ALLOW_STUDENT_CHANGE_EMAIL = True