from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint, jsonify, request, current_app, url_for, redirect, session as sess
from flask.ext.login import login_required, current_user, logout_user
from flask.ext.restful import Resource, marshal, abort
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import and_, or_
import string

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from login import authenticate
from acj.models import User, Course, CourseRole, SystemRole, \
    LTIConsumer, LTIContext, LTIResourceLink, LTIUser, LTIUserResourceLink
from .util import new_restful_api, get_model_changes, pagination_parser

from lti.contrib.flask import FlaskToolProvider
from lti import ToolProvider
from oauthlib.oauth1 import RequestValidator
from .file import random_generator

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

        if ok and tool_provider.user_id != None:
            # log current user out if needed
            logout_user()
            sess.clear()

            sess['LTI'] = True

            lti_consumer = LTIConsumer.get_by_tool_provider(tool_provider)
            sess['lti_consumer'] = lti_consumer.id

            lti_user = LTIUser.get_by_tool_provider(lti_consumer, tool_provider)
            sess['lti_user'] = lti_user.id

            lti_context = LTIContext.get_by_tool_provider(lti_consumer, tool_provider)
            if lti_context:
                sess['lti_context'] = lti_context.id

            lti_resource_link = LTIResourceLink.get_by_tool_provider(lti_consumer, tool_provider)
            sess['lti_resource_link'] = lti_resource_link.id

            lti_user_resource_link = LTIUserResourceLink.get_by_tool_provider(lti_resource_link, lti_user, tool_provider)
            sess['lti_user_resource_link'] = lti_user_resource_link.id

            setup_required = False
            angular_route = None

            # if user linked
            if lti_user.is_linked_to_user():
                authenticate(lti_user.acj_user)
            else:
                # need to create user link
                sess['oauth_create_user_link'] = True
                setup_required = True

            if not lti_context:
                # no context, redriect to home page
                angular_route = "/"
            elif lti_context.is_linked_to_course():
                # redirect to course page or assignment page if available
                angular_route = "/course/"+str(lti_context.acj_course_id)
                if lti_resource_link.is_linked_to_assignment():
                    angular_route += "/assignment/"+str(lti_resource_link.acj_assignment_id)
            elif lti_user_resource_link.course_role == CourseRole.instructor:
                setup_required = True
            else:
                # dislay message to user somehow
                angular_route = "/"

            if setup_required:
                # if account/course setup required, redirect to lti controller
                angular_route = "/lti"
            elif angular_route == None:
                # set angular route to home page by default
                angular_route = "/"

            return redirect("/static/index.html#"+angular_route)
        else:
            display_message = "Invalid Request"

            if ok and tool_provider.user_id == None:
                display_message = "ComPAIR requires the LTI tool consumer to provide a user_id."

            tool_provider.lti_errormsg = display_message
            return_url = tool_provider.build_return_url()
            if return_url:
                redirect(return_url)
            else:
                return display_message, 400

api.add_resource(LTIAuthAPI, '/lti/auth')

def display_name_generator(role="student"):
    return "".join([role, '_', random_generator(7, string.digits)])

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
            "name" : course name
            },
            "assignment": {
                "id": Int, #LTI link custom assignment id or null/None
                "exists": Bool #If the assignment exists or not
            },
            "user": {
                "exists": Bool, #If the user exists or not
                "first name": user's first name
                "last name": user's last name
                "display name": user display name; autogenerated
                "email": user's email
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
        course['name'] = None
        if lti_context:
            course['id'] = lti_context.acj_course_id
            if course['id']:
                course['exists'] = True
            course['name'] = lti_context.context_title

        course['course_role'] = None
        lti_user_resource_link = LTIUserResourceLink.query.get(sess['lti_user_resource_link'])
        if lti_user_resource_link:
            if lti_user_resource_link.course_role:
                course['course_role'] = lti_user_resource_link.course_role.value

        user = {}
        user['exists'] = False
        user['firstname'] = None
        user['lastname'] = None
        user['email'] = None
        user['displayname'] = None

        lti_user = LTIUser.query.get(sess['lti_user'])
        if lti_user:
            if lti_user.acj_user_id:
                user['exists'] = True
                user['firstname'] = lti_user.lis_person_name_given
                user['lastname'] = lti_user.lis_person_name_family
                user['email'] = lti_user.lis_person_contact_email_primary
                user['displayname'] = display_name_generator(lti_user.system_role.value)
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
            return {'error': "Your LTI session has expired." }, 404

        if not sess.get('lti_context'):
            return {'error': "Your LTI session has no context." }, 404

        lti_context = LTIContext.query.get_or_404(sess.get('lti_context'))
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
    @property
    def enforce_ssl(self):
        return current_app.config.get('LTI_ENFORCE_SSL', True)

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
