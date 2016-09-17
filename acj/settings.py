import os

"""
    Default settings, if no other settings is specified, values here are used.
"""

DATABASE = {
    'drivername': 'mysql+pymysql',
    'host': 'localhost',
    'port': '3306',
    'username': 'acj',
    'password': 'acjacj',
    'database': 'acj',
}

# enable sessions by setting the secret key
SECRET_KEY = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"

CAS_SERVER = 'http://localhost:8088'
CAS_AFTER_LOGIN = 'login_api.auth_cas'

REPORT_FOLDER = os.getcwd() + '/acj/static/report'

# save some system resources, (will be false by default in Flask-SQLAlchemy in a future release)
# we currently use SQLAlchemy event sytem directly
SQLALCHEMY_TRACK_MODIFICATIONS = False

# for uploads
UPLOAD_FOLDER = os.getcwd() + '/tmpUpload'
ATTACHMENT_UPLOAD_FOLDER = os.getcwd() + '/acj/static/pdf'
ATTACHMENT_ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_ALLOWED_EXTENSIONS = {'csv'}

PASSLIB_CONTEXT = 'default'

# make the session valid for a day
PERMANENT_SESSION_LIFETIME = 3600 * 24

# where to retrieve assets, possible values 'cloud', 'local'
ASSET_LOCATION = 'cloud'
# compair-asset s3 location
ASSET_CLOUD_URI_PREFIX = 'https://d1flf4q1u9z72v.cloudfront.net/dist/'

# Google Analytic Tracking ID, setting this will enable tracking
GA_TRACKING_ID = None
