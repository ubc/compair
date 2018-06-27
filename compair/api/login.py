import os
import datetime
import pytz
from hashlib import md5

from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect, Flask
from flask_login import current_user, login_required, login_user, logout_user
from flask_restful import marshal, Resource

from compair.core import db, event, abort, impersonation
from compair.authorization import get_logged_in_user_permissions
from compair.models import User, LTIUser, LTIResourceLink, LTIUserResourceLink, UserCourse, LTIContext, \
    ThirdPartyUser, ThirdPartyType
from compair.cas import get_cas_login_url, validate_cas_ticket, get_cas_logout_url
from compair.saml import get_saml_login_url, get_saml_auth_response, get_saml_logout_url, _get_auth
from . import dataformat
from .util import new_restful_api

login_api = Blueprint("login_api", __name__, url_prefix='/api')

# events
on_login_with_method = event.signal('USER_LOGGED_IN_WITH_METHOD')
on_logout = event.signal('USER_LOGGED_OUT')

@login_api.route('/login', methods=['POST'])
def login():
    if not current_app.config.get('APP_LOGIN_ENABLED'):
        abort(403, title="Log In Failed",
            message="Please try an alternate way of logging in. The ComPAIR login has been disabled by your system administrator.")

    # expecting login params to be in json format
    param = request.json
    if param is None:
        abort(400, title="Log In Failed", message="The username and password data did not send as expected. Please try again.")

    username = param['username']
    password = param['password']
    # grab the user from the username
    user = User.query.filter_by(username=username).first()
    if not user:
        current_app.logger.debug("Login failed, invalid username for: " + username)
    elif not user.verify_password(password):
        current_app.logger.debug("Login failed, invalid password for: " + username)
    else:
        permissions = authenticate(user, login_method='ComPAIR Account')

        if sess.get('LTI') and sess.get('lti_create_user_link'):
            lti_user = LTIUser.query.get_or_404(sess['lti_user'])
            lti_user.compair_user = user
            lti_user.upgrade_system_role()
            lti_user.update_user_profile()
            sess.pop('lti_create_user_link')

        if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
            lti_context = LTIContext.query.get_or_404(sess['lti_context'])
            lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
            lti_context.update_enrolment(user.id, lti_user_resource_link.course_role)

        db.session.commit()
        return jsonify({'user_id': user.uuid, 'permissions': permissions})

    # login unsuccessful
    abort(400, title="Log In Failed", message="Sorry, the username or password was not recognized. Please double-check both fields and try again.")

class Logout(Resource):
    @login_required
    def delete(self):
        sess['end_at'] = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        on_logout.send(
            current_app._get_current_object(),
            event=on_logout.name,
            user=current_user
        )
        current_user.update_last_online()
        logout_user()  # flask-login delete user info
        url = ""

        if sess.get('LTI'):
            lti_resource_link = LTIResourceLink.query.get(sess['lti_resource_link'])
            if lti_resource_link:
                return_url = lti_resource_link.launch_presentation_return_url
                if return_url != None and return_url.strip() != "":
                    url = jsonify({'redirect': return_url})

        elif sess.get('CAS_LOGIN'):
            url = jsonify({'redirect': url_for('login_api.cas_logout')})
        elif sess.get('SAML_LOGIN'):
            url = jsonify({'redirect': url_for('login_api.saml_logout')})

        sess.clear()
        return url

restful_logout_api = new_restful_api(login_api)
restful_logout_api.add_resource(Logout, '/logout')

@login_api.route('/session', methods=['GET'])
@login_required
def session():
    impersonation_details = _checkImpersonation()
    if impersonation_details.get('impersonating', False):
        return jsonify({'id': current_user.uuid, 'permissions': get_logged_in_user_permissions(), 'impersonation': impersonation_details})
    else:
        return jsonify({'id': current_user.uuid, 'permissions': get_logged_in_user_permissions()})


@login_api.route('/session/permission', methods=['GET'])
@login_required
def get_permission():
    return jsonify(get_logged_in_user_permissions())

@login_api.route('/cas/login')
def cas_login():
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Log In Failed",
            message="Please try an alternate way of logging in. The CWL login has been disabled by your system administrator.")

    return redirect(get_cas_login_url())

@login_api.route('/cas/auth', methods=['GET'])
def cas_auth():
    """
    CAS Authentication Endpoint. Authenticate user through CAS.
    If error, set message in session so that frontend can get the message through /session call
    """
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Log In Failed",
            message="Please try an alternate way of logging in. The CWL login has been disabled by your system administrator.")

    url = "/app/#/lti" if sess.get('LTI') else "/"
    error_message = None
    ticket = request.args.get("ticket")

    # check if token isn't present
    if not ticket:
        error_message = "No token in request"
    else:
        validation_response = validate_cas_ticket(ticket)

        if not validation_response.success:
            current_app.logger.debug(
                "CAS Server did NOT validate ticket:%s and included this response:%s" % (ticket, validation_response.response)
            )
            error_message = "Login Failed. CAS ticket was invalid."
        elif not validation_response.user:
            current_app.logger.debug("CAS Server responded with valid ticket but no user")
            error_message = "Login Failed. Expecting CAS username to be set."
        else:
            current_app.logger.debug(
                "CAS Server responded with user:%s and attributes:%s" % (validation_response.user, validation_response.attributes)
            )
            username = validation_response.user

            thirdpartyuser = ThirdPartyUser.query. \
                filter_by(
                    unique_identifier=username,
                    third_party_type=ThirdPartyType.cas
                ) \
                .one_or_none()

            if not thirdpartyuser:
                thirdpartyuser = ThirdPartyUser(
                    unique_identifier=username,
                    third_party_type=ThirdPartyType.cas,
                    params=validation_response.attributes
                )
                thirdpartyuser.generate_or_link_user_account()
                db.session.add(thirdpartyuser)
                db.session.commit()
            elif not thirdpartyuser.user:
                thirdpartyuser.generate_or_link_user_account()
                db.session.commit()

            authenticate(thirdpartyuser.user, login_method=thirdpartyuser.third_party_type.value)
            thirdpartyuser.params = validation_response.attributes

            if sess.get('LTI') and sess.get('lti_create_user_link'):
                lti_user = LTIUser.query.get_or_404(sess['lti_user'])
                lti_user.compair_user_id = thirdpartyuser.user_id
                lti_user.upgrade_system_role()
                lti_user.update_user_profile()
                sess.pop('lti_create_user_link')
            else:
                thirdpartyuser.upgrade_system_role()
                thirdpartyuser.update_user_profile()

            if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
                lti_context = LTIContext.query.get_or_404(sess['lti_context'])
                lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
                lti_context.update_enrolment(thirdpartyuser.user_id, lti_user_resource_link.course_role)

            db.session.commit()
            sess['CAS_LOGIN'] = True

    if error_message is not None:
        sess['THIRD_PARTY_AUTH_ERROR_TYPE'] = 'CAS'
        sess['THIRD_PARTY_AUTH_ERROR_MSG'] = error_message

    return redirect(url)

@login_api.route('/cas/logout', methods=['GET'])
def cas_logout():
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Log Out Failed",
            message="Please try an alternate way of logging out. The CWL logout has been disabled by your system administrator.")

    return redirect(get_cas_logout_url())


@login_api.route('/saml/login', methods=['GET'])
def saml_login():
    if not current_app.config.get('SAML_LOGIN_ENABLED'):
        abort(403, title="Not Logged In",
            message="Please use a valid way to log in. You are not able to use CWL login based on the current settings.")

    return redirect(get_saml_login_url(request))

@login_api.route('/saml/auth', methods=['POST'])
def saml_auth():
    """
    SAML Authentication Endpoint. Authenticate user through SAML.
    If error, set message in session so that frontend can get the message through /session call
    """
    if not current_app.config.get('SAML_LOGIN_ENABLED'):
        abort(403, title="Not Logged In",
            message="Please use a valid way to log in. You are not able to use CWL login based on the current settings.")

    url = "/app/#/lti" if sess.get('LTI') else "/"
    error_message = None
    auth = get_saml_auth_response(request)
    errors = auth.get_errors()

    if len(errors) > 0:
        current_app.logger.debug(
            "SAML IdP returned errors: %s" % (errors)
        )
        error_message = "Login Failed."
    elif not auth.is_authenticated():
        current_app.logger.debug(
            "SAML IdP not logged in"
        )
        error_message = "Login Failed."
    else:
        attributes = auth.get_attributes()
        unique_identifier = attributes.get(current_app.config.get('SAML_UNIQUE_IDENTIFIER'))
        current_app.logger.debug(
            "SAML IdP responded with attributes:%s" % (attributes)
        )

        if not unique_identifier or (isinstance(unique_identifier, list) and len(unique_identifier) == 0):
            current_app.logger.error(
                "SAML idP did not return the unique_identifier " + current_app.config.get('SAML_UNIQUE_IDENTIFIER') + " within its attributes"
            )
            error_message = "Login Failed. Expecting " + current_app.config.get('SAML_UNIQUE_IDENTIFIER') + " to be set."
        else:
            # set unique_identifier to first item in list if unique_identifier is an array
            if isinstance(unique_identifier, list):
                unique_identifier = unique_identifier[0]

            thirdpartyuser = ThirdPartyUser.query. \
                filter_by(
                    unique_identifier=unique_identifier,
                    third_party_type=ThirdPartyType.saml
                ) \
                .one_or_none()

            sess['SAML_NAME_ID'] = auth.get_nameid()
            sess['SAML_SESSION_INDEX'] = auth.get_session_index()

            if not thirdpartyuser:
                thirdpartyuser = ThirdPartyUser(
                    unique_identifier=unique_identifier,
                    third_party_type=ThirdPartyType.saml,
                    params=attributes
                )
                thirdpartyuser.generate_or_link_user_account()
                db.session.add(thirdpartyuser)
                db.session.commit()
            elif not thirdpartyuser.user:
                thirdpartyuser.generate_or_link_user_account()
                db.session.commit()

            authenticate(thirdpartyuser.user, login_method=thirdpartyuser.third_party_type.value)
            thirdpartyuser.params = attributes

            if sess.get('LTI') and sess.get('lti_create_user_link'):
                lti_user = LTIUser.query.get_or_404(sess['lti_user'])
                lti_user.compair_user_id = thirdpartyuser.user_id
                lti_user.upgrade_system_role()
                lti_user.update_user_profile()
                sess.pop('lti_create_user_link')
            else:
                thirdpartyuser.upgrade_system_role()
                thirdpartyuser.update_user_profile()

            if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
                lti_context = LTIContext.query.get_or_404(sess['lti_context'])
                lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
                lti_context.update_enrolment(thirdpartyuser.user_id, lti_user_resource_link.course_role)

            db.session.commit()
            sess['SAML_LOGIN'] = True

    if error_message is not None:
        sess['THIRD_PARTY_AUTH_ERROR_TYPE'] = 'SAML'
        sess['THIRD_PARTY_AUTH_ERROR_MSG'] = error_message

    return redirect(url)

@login_api.route('/saml/metadata', methods=['GET'])
def metadata():
    if not current_app.config.get('SAML_LOGIN_ENABLED') or not current_app.config.get('SAML_EXPOSE_METADATA_ENDPOINT'):
        abort(404)

    auth = _get_auth(request)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) > 0:
        abort(500, title="Metadata Error",
            message=', \n'.join(errors))

    return metadata, 200, {'Content-Type': 'text/xml; charset=utf-8'}

@login_api.route('/saml/logout', methods=['GET'])
def saml_logout():
    if not current_app.config.get('SAML_LOGIN_ENABLED'):
        abort(403, title="Not Logged Out",
            message="Please use a valid way to log out. You are not able to use CWL logout based on the current settings.")

    return redirect(get_saml_logout_url(request))


@login_api.route('/saml/single_logout', methods=['GET'])
def saml_single_logout():
    # TODO: TEST THIS
    if not current_app.config.get('SAML_LOGIN_ENABLED'):
        abort(403, title="Not Logged Out",
            message="Please use a valid way to log out. You are not able to use CWL logout based on the current settings.")

    auth = _get_auth(request)
    url = auth.process_slo(delete_session_cb=_saml_single_signout_callback)
    errors = auth.get_errors()
    if len(errors) > 0:
        current_app.logger.debug("Error when processing Single Loggout: %s" % (', '.join(errors)))
    else:
        current_app.logger.debug("SAML Single Loggout Successfull")

    return redirect(url) if url != None else redirect('/')

def _saml_single_signout_callback():
    if current_user:
        current_user.update_last_online()
    logout_user()
    sess.clear()

def authenticate(user, login_method=None, skip_event_tracking=False):
    # username valid, password valid, login successful
    # "remember me" functionality is available, do we want to implement?
    user.update_last_online()
    login_user(user) # flask-login store user info

    if user.username != None:
        current_app.logger.debug("Login successful for: " + user.username)
    else:
        current_app.logger.debug("Login successful for: user_id = " + str(user.id))

    sess['session_id'] = md5(sess['session_token'].encode('UTF-8')).hexdigest()
    sess['start_at'] = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    sess['login_method'] = login_method

    if not skip_event_tracking:
        on_login_with_method.send(
            current_app._get_current_object(),
            event=on_login_with_method.name,
            user=user
        )
    return get_logged_in_user_permissions()

def _checkImpersonation():
    if not current_app.config.get('IMPERSONATION_ENABLED', False) or not impersonation.is_impersonating():
        return {'impersonating' : False}

    original_user = impersonation.get_impersonation_original_user()
    impersonate_as_user = current_user
    if original_user is None or impersonate_as_user is None:
        # something went wrong...
        abort(503, title="Cannot check impersonation status", \
            message="Sorry, cannot find information on impersonation status")

    # user is impersonating. treat as restrict_user when calling dataformat
    return { \
        'impersonating' : True,
        'original_user' : marshal(original_user, dataformat.get_user(True))
    }