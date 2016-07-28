from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint, jsonify, request, current_app, url_for, redirect, session as sess
from flask.ext.login import login_required, current_user, logout_user
from flask.ext.restful import Resource, marshal, abort
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import and_, or_

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from login import authenticate
from acj.models import User, Course, LTIConsumer, LTIContext, LTIResourceLink, \
    LTIUser, LTIUserResourceLink
from .util import new_restful_api, get_model_changes, pagination_parser

from lti.contrib.flask import FlaskToolProvider
from lti import ToolProvider
from oauthlib.oauth1 import RequestValidator

lti_api = Blueprint("lti_api", __name__, url_prefix='/api')
api = new_restful_api(lti_api)

# events
on_lti_course_link = event.signal('LTI_CONTEXT_COURSE_LINKED')

# /lti/auth
class LTIAuthAPI(Resource):
    def post(self):
        """
        Kickstarts the LTI integration flow.
        """
        tool_provider = FlaskToolProvider.from_flask_request(request=request)
        validator = MyRequestValidator()
        ok = tool_provider.is_valid_request(validator)

        # todo: if LMS user already linked to a ComPAIR account, establish an appropriate session
        # otherwise, direct the user to the login screen. In either case, set session variables.
        if ok:
            # log current user out if needed
            logout_user()
            sess.clear()

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

            # if user linked
            if lti_user.is_linked_to_user():
                authenticate(lti_user.acj_user)
            else:
                # need to create user link
                sess['oauth_create_user_link'] = True

            # after setting session, check if accounts linkage exists. If not, redirect.
            return redirect("/static/index.html#/lti")
        else:
            return {"error": 'Error: LTI launch request is invalid.'}, 400

api.add_resource(LTIAuthAPI, '/lti/auth')

# /lti/status
class LTIStatusAPI(Resource):
    def get(self):
        """
        Returns information related to the current user:
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

        course['course_role'] = None
        lti_user_resource_link = LTIUserResourceLink.query.get(sess['lti_user_resource_link'])
        if lti_user_resource_link:
            if lti_user_resource_link.course_role:
                course['course_role'] = lti_user_resource_link.course_role.value

        user = {}
        user['exists'] = False
        lti_user = LTIUser.query.get(sess['lti_user'])
        if lti_user:
            if lti_user.acj_user_id:
                user['exists'] = True

        body['course'] = course
        body['assignment'] = assignment
        body['user'] = user

        return { "status" : body }

api.add_resource(LTIStatusAPI, '/lti/status')

# /lti/course/:course_id/link
class LTICourseLinkAPI(Resource):
    @login_required
    def post(self, course_id):
        """
        link current session's lti context with a course
        """
        course = Course.get_active_or_404(course_id)
        require(EDIT, course)

        if not sess.get('LTI'):
            return 404

        lti_context = LTIContext.query.get_or_404(sess['lti_context'])
        if not lti_context:
            return 404

        lti_context.acj_course_id = course.id

        db.session.commit()

        on_lti_course_link.send(
            self,
            event_name=on_lti_course_link.name,
            user=current_user,
            data={ "course_id": course.id, "lti_context_id": lti_context.id })

        return marshal(course, dataformat.get_course())

api.add_resource(LTICourseLinkAPI, '/lti/course/<int:course_id>/link')



class MyRequestValidator(RequestValidator):
    enforce_ssl = False

    def validate_timestamp_and_nonce(self, timestamp, nonce, request, request_token=None, access_token=None):
        return True

    def validate_client_key(self, client_key, request):
        lti_consumer = LTIConsumer.query \
            .filter_by(
                active=True,
                oauth_consumer_key=client_key
            ) \
            .one_or_none()

        return lti_consumer != None

    def get_client_secret(self, client_key, request):
        lti_consumer = LTIConsumer.query \
            .filter_by(
                active=True,
                oauth_consumer_key=client_key
            ) \
            .one_or_none()

        if lti_consumer:
            return lti_consumer.oauth_consumer_secret
        else:
            return None
