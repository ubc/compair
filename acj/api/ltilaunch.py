import os
from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect, Flask, render_template
from flask_login import current_user, login_required, login_user, logout_user
from mock import Mock
from acj import cas
from acj.authorization import get_logged_in_user_permissions
from acj.models import User
from pylti.flask import lti, LTI_SESSION_KEY
import logging
from lti.contrib.flask import FlaskToolProvider
from lti import ToolConfig
from .MyRequestValidator import MyRequestValidator

isLTI = False
lti_api = Blueprint("lti_api", __name__, url_prefix='/api')
VERSION = '0.0.1'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='myapp.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

@lti_api.route('/lti/auth', methods=['POST'])
#@lti(request='initial', error=error)
def lti_auth():
    """Kickstarts the LTI integration flow.
    """
    sess['LTI'] = True
    tool_provider = FlaskToolProvider.from_flask_request(request=request)
    validator = MyRequestValidator()
    ok = tool_provider.is_valid_request(validator)

    # todo: if LMS user already linked to a ComPAIR account, establish an appropriate session
    # otherwise, direct the user to the login screen
    if ok:
        return redirect("http://localhost:8080/static/index.html#/", code=302)
    else:
        return "Error: LTI launch request is invalid."

@lti_api.route('/lti/islti', methods=['GET'])
def is_lti():
    """Used by the frontend to check if the current
    session originated from an LTI launch request.
    """
    if sess.get('LTI'):
        if sess['LTI']:
            return jsonify({'status': True})
    else:
        return jsonify({'status': False})

