import os

"""
    Default settings, if no other settings is specified, values here are used.
"""

DATABASE = {
    'drivername': 'mysql+pymysql',
    'host': 'localhost',
    'port': '3306',
    'username': 'acj',
    'password': 'acj',
    'database': 'acj',
}

# enable sessions by setting the secret key
SECRET_KEY = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"

CAS_SERVER = 'http://localhost:8088'
CAS_AFTER_LOGIN = 'login_api.auth_cas'

REPORT_FOLDER = os.getcwd() + '/acj/static/report'

# for uploads
UPLOAD_FOLDER = os.getcwd() + '/tmpUpload'
ATTACHMENT_UPLOAD_FOLDER = os.getcwd() + '/acj/static/pdf'
ATTACHMENT_ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_ALLOWED_EXTENSIONS = {'csv'}

PASSLIB_CONTEXT = 'default'
