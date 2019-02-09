import os

"""
    Default settings, if no other settings is specified, values here are used.
"""

COMPAIR_VERSION = "1.2.1"

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
ATTACHMENT_PREVIEW_EXTENSIONS = {'jpg','jpeg','png'}

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
CELERY_ALWAYS_EAGER = True # By default, execute tasks locally
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True
}

# xAPI & Learning Record Stores (LRS)
XAPI_ENABLED = False
CALIPER_ENABLED = False
LRS_APP_BASE_URL = None

LRS_XAPI_STATEMENT_ENDPOINT = 'local' #url for LRS xAPI statements
LRS_XAPI_AUTH = None
LRS_XAPI_USERNAME = None
LRS_XAPI_PASSWORD = None

LRS_CALIPER_HOST = 'local' #url for LRS Caliper statements
LRS_CALIPER_API_KEY = None

# limit user generated content field text size limit
LRS_USER_INPUT_FIELD_SIZE_LIMIT = 524288 #512 * 1024 -> max 512KB
LRS_SIS_COURSE_ID_URI_TEMPLATE = '{base_url}/course/{sis_course_id}'
LRS_SIS_SECTION_ID_URI_TEMPLATE = '{base_url}/course/{sis_course_id}/section/{sis_section_id}'

LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER = False # set to True to use user's global_unique_identifier if available
LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE = None # set to the url for the global unique identifer homepage

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
CAS_LOGIN_ENABLED = False
# Login via SAML idp
# if true requires additional SAML settings
SAML_LOGIN_ENABLED = False
# Login via LTI consumer
# if true requires record with oauth_consumer_key and oauth_consumer_secret in lti_consumer table
LTI_LOGIN_ENABLED = True

LOGIN_ADDITIONAL_INSTRUCTIONS_HTML = """
<h3>For course access issues, please check:</h3>
<dl>
    <dt>Are you registered in the course that is using this application?</dt>
        <dd>For example, see if you have access to the course in Canvas. If you aren't registered, contact <a href="https://it.ubc.ca/got-question-about-it-products-and-support#helpdesk" target="_blank">UBC IT support</a>.</dd>
    <dt>Did you click the ComPAIR link from Canvas at least once?</dt>
        <dd>If your course has a Canvas site, click the ComPAIR link from there once. This action enrols you in the ComPAIR course.</dd>
    <dt>Are you using a modern browser?</dt>
        <dd>Supported browsers for this application include <a href="https://www.mozilla.org/en-US/firefox/new/" target="_blank">Firefox</a>, <a href="http://www.google.com/chrome/" target="_blank">Chrome</a>, <a href="https://www.apple.com/ca/safari/" target="_blank">Safari</a>, and <a href="http://windows.microsoft.com/en-ca/internet-explorer/download-ie" target="_blank">IE9+</a>.</dd>
    <dt>Did you answer 'yes' to all the troubleshooting questions above?</dt>
        <dd>Contact <a href="mailto:compair.support@ubc.ca" target="_self">ComPAIR technical support</a> for help.</dd>
</dl>
"""

CAS_LOGIN_HTML = """<img class="center-block" src="https://www.auth.cwl.ubc.ca/CWL_login_button.gif" width="76" height="25" alt="CWL Login" border="0">"""
CAS_SERVER = 'http://localhost:8088'
CAS_AUTH_PREFIX = '/cas'
CAS_USE_SAML = False

CAS_ATTRIBUTE_USER_ROLE = None
CAS_INSTRUCTOR_ROLE_VALUES = {}
CAS_ATTRIBUTE_FIRST_NAME = None
CAS_ATTRIBUTE_LAST_NAME = None
CAS_ATTRIBUTE_STUDENT_NUMBER = None
CAS_ATTRIBUTE_EMAIL = None

SAML_LOGIN_HTML = """<img class="center-block" src="https://www.auth.cwl.ubc.ca/CWL_login_button.gif" width="76" height="25" alt="CWL Login" border="0">"""
SAML_UNIQUE_IDENTIFIER = 'uid'
SAML_METADATA_URL = None
SAML_METADATA_ENTITY_ID = None
SAML_EXPOSE_METADATA_ENDPOINT = False

SAML_ATTRIBUTE_USER_ROLE = None
SAML_INSTRUCTOR_ROLE_VALUES = {}
SAML_ATTRIBUTE_FIRST_NAME = None
SAML_ATTRIBUTE_LAST_NAME = None
SAML_ATTRIBUTE_STUDENT_NUMBER = None
SAML_ATTRIBUTE_EMAIL = None

# kaltura integration defaults
KALTURA_ENABLED = False
KALTURA_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
KALTURA_AUDIO_EXTENSIONS = {'wav', 'mp3'}
KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER = False

# Mail
MAIL_NOTIFICATION_ENABLED = False

# Privacy data settings
EXPOSE_EMAIL_TO_INSTRUCTOR = False
EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR = False

# Control which profile information a student can edit
ALLOW_STUDENT_CHANGE_NAME = True
ALLOW_STUDENT_CHANGE_DISPLAY_NAME = True
ALLOW_STUDENT_CHANGE_STUDENT_NUMBER = True
ALLOW_STUDENT_CHANGE_EMAIL = True

# Allow impersonation
IMPERSONATION_ENABLED = True

# Feature to notify students on assignment answering / comparing period ending soon
NOTIFICATION_ASSIGNMENT_ENDING_ENABLED = False