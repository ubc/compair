from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint, jsonify, request, current_app, url_for, redirect, session as sess
from flask_login import login_required, current_user, logout_user
from flask_restful import Resource, marshal, abort
from flask_restful.reqparse import RequestParser
from sqlalchemy import and_, or_

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from .login import authenticate
from acj.models import User, Course, LTIConsumer, LTIContext, LTIMembership, \
    LTIResourceLink, LTIUser, LTIUserResourceLink, LTINonce
from acj.models.lti import MembershipNoValidContextsException, \
    MembershipNoResultsException, MembershipInvalidRequestException
from .util import new_restful_api, get_model_changes, pagination_parser

from acj.api.classlist import display_name_generator
from lti.contrib.flask import FlaskToolProvider
from oauthlib.oauth1 import RequestValidator

lti_api = Blueprint("lti_api", __name__, url_prefix='/api')
api = new_restful_api(lti_api)

# events
on_lti_course_link = event.signal('LTI_CONTEXT_COURSE_LINKED')
on_lti_course_membership_update = event.signal('LTI_CONTEXT_COURSE_MEMBERSHIP_UPDATE')
on_lti_course_membership_status_get = event.signal('LTI_CONTEXT_COURSE_MEMBERSHIP_STATUS_GET')

# /lti/auth
class LTIAuthAPI(Resource):
    def post(self):
        """
        Kickstarts the LTI integration flow.
        """
        tool_provider = FlaskToolProvider.from_flask_request(request=request)
        validator = ACJRequestValidator()
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

            lti_resource_link = LTIResourceLink.get_by_tool_provider(lti_consumer, tool_provider, lti_context)
            sess['lti_resource_link'] = lti_resource_link.id

            lti_user_resource_link = LTIUserResourceLink.get_by_tool_provider(lti_resource_link, lti_user, tool_provider)
            sess['lti_user_resource_link'] = lti_user_resource_link.id

            setup_required = False
            angular_route = None

            # if user linked
            if lti_user.is_linked_to_user():
                authenticate(lti_user.acj_user)

                # create/update enrollment if context exists
                if lti_context and lti_context.is_linked_to_course():
                    lti_context.update_enrolment(lti_user.acj_user_id, lti_user_resource_link.course_role)
            else:
                # need to create user link
                sess['oauth_create_user_link'] = True
                setup_required = True

            if not lti_context:
                # no context, redriect to home page
                angular_route = "/"
            elif lti_context.is_linked_to_course():
                # redirect to course page or assignment page if available
                angular_route = "/course/"+lti_context.acj_course_uuid
                if lti_resource_link.is_linked_to_assignment():
                    angular_route += "/assignment/"+lti_resource_link.acj_assignment_uuid
            else:
                # instructors can select course, students will recieve a warning message
                setup_required = True

            if setup_required:
                # if account/course setup required, redirect to lti controller
                angular_route = "/lti"
            elif angular_route == None:
                # set angular route to home page by default
                angular_route = "/"

            # clear cookies in case they exist from previous user
            response = current_app.make_response(redirect("/app/#"+angular_route))
            response.set_cookie('current.permissions', value='', path='/static')
            response.set_cookie('current.lti.status', value='', path='/static')
            response.set_cookie('current.user', value='', path='/static')

            return response
        else:
            display_message = "Invalid Request"

            if ok and tool_provider.user_id == None:
                display_message = "ComPAIR requires the LTI tool consumer to provide a user_id."

            tool_provider.lti_errormsg = display_message
            return_url = tool_provider.build_return_url()
            if return_url:
                return redirect(return_url)
            else:
                return display_message, 400

api.add_resource(LTIAuthAPI, '/lti/auth')

# /lti/status
class LTIStatusAPI(Resource):
    def get(self):
        """
        Returns information related to the current user:
        any linked course, assignment, etc. Helps inform
        the app as to what to do next, for a given state.
        """

        if not sess.get('LTI'):
            return { "status" : { 'valid': False } }

        lti_resource_link = LTIResourceLink.query.get(sess.get('lti_resource_link'))
        lti_context = LTIContext.query.get(sess.get('lti_context')) if sess.get('lti_context') else None
        lti_user_resource_link = LTIUserResourceLink.query.get(sess.get('lti_user_resource_link'))
        lti_user = LTIUser.query.get(sess.get('lti_user'))
        status = {
            'valid' : True,
            'assignment': {
                'id': lti_resource_link.acj_assignment_uuid if lti_resource_link.acj_assignment_id != None else None,
                'exists': lti_resource_link.acj_assignment_id != None
            },
            'course': {
                'name': lti_context.context_title if lti_context and lti_context.acj_course_id else None,
                'id': lti_context.acj_course_uuid if lti_context and lti_context.acj_course_id else None,
                'exists': lti_context and lti_context.acj_course_id != None,
                'course_role': lti_user_resource_link.course_role.value if lti_user_resource_link else None
            },
            'user': {
                'exists': lti_user.acj_user_id != None,
                'firstname': lti_user.lis_person_name_given,
                'lastname': lti_user.lis_person_name_family,
                'displayname': display_name_generator(lti_user.system_role.value),
                'email': lti_user.lis_person_contact_email_primary,
                'system_role': lti_user.system_role.value
            }
        }

        return { "status" : status }

api.add_resource(LTIStatusAPI, '/lti/status')

# /lti/course/:course_uuid/link
class LTICourseLinkAPI(Resource):
    @login_required
    def post(self, course_uuid):
        """
        link current session's lti context with a course
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course)

        if not sess.get('LTI'):
            return {'error': "Your LTI session has expired." }, 404

        if not sess.get('lti_context'):
            return {'error': "Your LTI session has no context." }, 404

        lti_context = LTIContext.query.get_or_404(sess.get('lti_context'))
        lti_context.acj_course_id = course.id
        db.session.commit()

        membership_warning = False

        # automatically fetch membership if enabled for context
        if lti_context.ext_ims_lis_memberships_url and lti_context.ext_ims_lis_memberships_id:
            try:
                LTIMembership.update_membership_for_course(course)
            except:
                membership_warning = True

        on_lti_course_link.send(
            self,
            event_name=on_lti_course_link.name,
            user=current_user,
            data={ 'course_id': course.id, 'lti_context_id': lti_context.id })

        if membership_warning:
            return { 'warning': 'LTI membership import failed' }
        else:
            return { 'success': True }

api.add_resource(LTICourseLinkAPI, '/lti/course/<course_uuid>/link')

# /lti/course/:course_uuid/membership
class LTICourseMembershipAPI(Resource):
    @login_required
    def post(self, course_uuid):
        """
        refresh the course membership if able
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course)

        if not course.lti_linked:
            return {'error': "Course not linked to lti context" }, 400

        try:
            LTIMembership.update_membership_for_course(course)
        except MembershipNoValidContextsException as err:
            return {'error': "LTI membership service is not supported for this course" }, 400
        except MembershipNoResultsException as err:
            return {'error': "LTI membership service did not return any users" }, 400
        except MembershipInvalidRequestException as err:
            return {'error': "LTI membership request was invalid. Please relaunch the ComPAIR course from the LTI consumer and try again" }, 400

        on_lti_course_membership_update.send(
            self,
            event_name=on_lti_course_membership_update.name,
            user=current_user,
            data={ 'course_id': course.id })

        return { 'imported': True }

api.add_resource(LTICourseMembershipAPI, '/lti/course/<course_uuid>/membership')


# /lti/course/:course_uuid/membership/status
class LTICourseMembershipStatusAPI(Resource):
    @login_required
    def get(self, course_uuid):
        """
        refresh the course membership if able
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course)

        if not course.lti_linked:
            return {'error': "Course not linked to lti context" }, 400

        valid_membership_contexts = [
            lti_context for lti_context in course.lti_contexts \
            if lti_context.ext_ims_lis_memberships_url and lti_context.ext_ims_lis_memberships_id
        ]

        pending = 0
        enabled = len(valid_membership_contexts) > 0
        if enabled:
            lti_context_ids = [lti_context.id for lti_context in valid_membership_contexts]

            pending = LTIMembership.query \
                .join(LTIUser) \
                .filter(and_(
                    LTIUser.acj_user_id == None,
                    LTIMembership.lti_context_id.in_(lti_context_ids)
                )) \
                .count()

        status = {
            'enabled': enabled,
            'pending': pending
        }

        on_lti_course_membership_status_get.send(
            self,
            event_name=on_lti_course_membership_status_get.name,
            user=current_user,
            data={ 'course_id': course.id })

        return { 'status': status }

api.add_resource(LTICourseMembershipStatusAPI, '/lti/course/<course_uuid>/membership/status')


class ACJRequestValidator(RequestValidator):
    @property
    def enforce_ssl(self):
        return current_app.config.get('LTI_ENFORCE_SSL', True)

    @property
    def client_key_length(self):
        return 10, 255

    @property
    def request_token_length(self):
        return 10, 50

    @property
    def access_token_length(self):
        return 10, 255

    @property
    def timestamp_lifetime(self):
        return 600

    @property
    def nonce_length(self):
        return 10, 50

    @property
    def verifier_length(self):
        return 20, 30

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None, access_token=None):
        return LTINonce.is_valid_nonce(client_key, nonce, timestamp)

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
        return lti_consumer.oauth_consumer_secret if lti_consumer else None
