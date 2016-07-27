import os
import json
from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect, Flask, render_template, Response
from flask_login import current_user, login_required, login_user, logout_user
from mock import Mock
from acj import cas
from acj.authorization import get_logged_in_user_permissions
from acj.models import User, LTIConsumer, LTIContext, LTIResourceLink, LTIUser, LTIUserResourceLink
from pylti.flask import lti, LTI_SESSION_KEY
import logging
from lti.contrib.flask import FlaskToolProvider
from lti import ToolConfig
from .MyRequestValidator import MyRequestValidator

from acj.core import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

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
    tool_provider = FlaskToolProvider.from_flask_request(request=request)
    validator = MyRequestValidator()
    ok = tool_provider.is_valid_request(validator)

    # todo: if LMS user already linked to a ComPAIR account, establish an appropriate session
    # otherwise, direct the user to the login screen. In either case, set session variables.
    if ok:
        sess['LTI'] = True
        lti_consumer = LTIConsumer.get_by_tool_provider(tool_provider)
        sess['lti_consumer'] = lti_consumer.id
        lti_user = LTIUser.get_by_tool_provider(lti_consumer, tool_provider)
        sess['lti_user'] = lti_user.id
        lti_context = LTIContext.get_by_tool_provider(lti_consumer, tool_provider)
        sess['lti_context'] = lti_context.id
        lti_resource_link = LTIResourceLink.get_by_tool_provider(lti_consumer, tool_provider)
        sess['lti_resource_link'] = lti_resource_link.id
        lti_user_resource_link = LTIUserResourceLink.get_by_tool_provider(lti_resource_link, lti_user, tool_provider)
        sess['lti_user_resource_link'] = lti_user_resource_link.id
        # after setting session, check if accounts linkage exists. If not, redirect.
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

@lti_api.route('/lti/status', methods=['GET'])
def status():
    """Returns information related to the current user:
    any linked course, assignment, etc. Helps inform 
    the app as to what to do next, for a given state. e.g.:

"status": {
    "valid": Bool, #is LTI session
    "redirect": String, # if the user should be redirected to one of "root", "course", or "assignment" after account setup/etc
    "course": {
        "id": Int, #LTI context's acj course id or null/None
        "exists": Bool, #If the course exists yet or not
        "course_role": String #the CourseRole string value for the current_user and the context
    },
    "assignment": {
        "id": Int, #LTI link custom assignment id or null/None
        "exists": Bool #If the assignment exists or not
    },
    "user": {
        "exists": Bool, #If the user exists or not
        "course_role": String #the SystemRole string value for the current_user
    }
}
    """
    isLTISession = False
    if sess.get('LTI'):
        isLTISession = True
    
    body = {}
    body['valid'] = isLTISession

    assignment = {}
    assignment['id'] = None
    assignment['exists'] = False
    lti_resource_link = LTIResourceLink.query.get(sess['lti_resource_link'])
    if lti_resource_link:
        assignment['id'] = lti_resource_link.acj_assignment_id
        if assignment['id']:
            assignment['exists'] = True

    course = {}
    lti_context = LTIContext.query.get(sess['lti_context'])
    course['id'] = None
    course['exists'] = False
    if lti_context:
        course['id'] = lti_context.acj_course_id
        if course['id']:
            course['exists'] = True

    user = {}
    user['exists'] = False
    lti_user = LTIUser.query.get(sess['lti_user'])
    if lti_user:
        if lti_user.user_oauth_id:
            user['exists'] = True

    user['course_role'] = None
    lti_user_resource_link = LTIUserResourceLink.query.get(sess['lti_user_resource_link'])
    if lti_user_resource_link:
        if lti_user_resource_link.course_role:
            user['course_role'] = lti_user_resource_link.course_role.value

    body['course'] = course
    body['assignment'] = assignment
    body['user'] = user
    js = { "status" : body }
    return Response(json.dumps(js), mimetype='application/json')
