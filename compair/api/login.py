import os

from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect, Flask, render_template
from flask_login import current_user, login_required, login_user, logout_user

from compair.core import db, event, abort
from compair.authorization import get_logged_in_user_permissions
from compair.models import User, LTIUser, LTIResourceLink, LTIUserResourceLink, UserCourse, LTIContext, \
    ThirdPartyUser, ThirdPartyType
from compair.cas import get_cas_login_url, validate_cas_ticket, get_cas_logout_url

login_api = Blueprint("login_api", __name__, url_prefix='/api')

# events
on_login_with_method = event.signal('USER_LOGGED_IN_WITH_METHOD')
on_logout = event.signal('USER_LOGGED_OUT')

@login_api.route('/login', methods=['POST'])
def login():
    if not current_app.config.get('APP_LOGIN_ENABLED'):
        abort(403, title="Not Logged In",
            message="Please use a valid way to log in. You are not able to use the ComPAIR login based on the current settings.")

    # expecting login params to be in json format
    param = request.json
    if param is None:
        abort(400, title="Not Logged In", message="Invalid login data. Please try again.")

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

        if sess.get('LTI') and sess.get('oauth_create_user_link'):
            lti_user = LTIUser.query.get_or_404(sess['lti_user'])
            lti_user.compair_user_id = user.id
            sess.pop('oauth_create_user_link')

        if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
            lti_context = LTIContext.query.get_or_404(sess['lti_context'])
            lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
            lti_context.update_enrolment(user.id, lti_user_resource_link.course_role)

        db.session.commit()
        return jsonify({'user_id': user.uuid, 'permissions': permissions})

    # login unsuccessful
    abort(400, title="Not Logged In", message="Sorry, unrecognized username or password. Please try again.")

@login_api.route('/logout', methods=['DELETE'])
@login_required
def logout():
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

    sess.clear()
    return url


@login_api.route('/session', methods=['GET'])
@login_required
def session():
    return jsonify({'id': current_user.uuid, 'permissions': get_logged_in_user_permissions()})


@login_api.route('/session/permission', methods=['GET'])
@login_required
def get_permission():
    return jsonify(get_logged_in_user_permissions())

@login_api.route('/cas/login')
def cas_login():
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Not Logged In",
            message="Please use a valid way to log in. You are not able to use CWL login based on the current settings.")

    return redirect(get_cas_login_url())

@login_api.route('/cas/auth', methods=['GET'])
def cas_auth():
    """
    CAS Authentication Endpoint. Authenticate user through CAS. If user doesn't exists,
    set message in session so that frontend can get the message through /session call
    """
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Not Logged In",
            message="Please use a valid way to log in. You are not able to use CWL login based on the current settings.")

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

            # store additional CAS attributes if needed
            if not thirdpartyuser or not thirdpartyuser.user:
                if sess.get('LTI') and sess.get('oauth_create_user_link'):
                    sess['CAS_CREATE'] = True
                    sess['CAS_UNIQUE_IDENTIFIER'] = username
                    sess['CAS_PARAMS'] = validation_response.attributes
                    url = '/app/#/oauth/create'
                else:
                    current_app.logger.debug("Login failed, invalid username for: " + username)
                    error_message = "You don't have access to this application."
            else:
                authenticate(thirdpartyuser.user, login_method=thirdpartyuser.third_party_type.value)
                thirdpartyuser.params = validation_response.attributes

                if sess.get('LTI') and sess.get('oauth_create_user_link'):
                    lti_user = LTIUser.query.get_or_404(sess['lti_user'])
                    lti_user.compair_user_id = thirdpartyuser.user_id
                    sess.pop('oauth_create_user_link')

                if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
                    lti_context = LTIContext.query.get_or_404(sess['lti_context'])
                    lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
                    lti_context.update_enrolment(thirdpartyuser.user_id, lti_user_resource_link.course_role)

                db.session.commit()
                sess['CAS_LOGIN'] = True

    if error_message is not None:
        sess['CAS_AUTH_MSG'] = error_message

    return redirect(url)

@login_api.route('/cas/logout', methods=['GET'])
def cas_logout():
    if not current_app.config.get('CAS_LOGIN_ENABLED'):
        abort(403, title="Not Logged Out",
            message="Please use a valid way to log out. You are not able to use CWL logout based on the current settings.")

    return redirect(get_cas_logout_url())

def authenticate(user, login_method=None):
    # username valid, password valid, login successful
    # "remember me" functionality is available, do we want to implement?
    user.update_last_online()
    login_user(user) # flask-login store user info

    if user.username != None:
        current_app.logger.debug("Login successful for: " + user.username)
    else:
        current_app.logger.debug("Login successful for: user_id = " + str(user.id))

    on_login_with_method.send(
        current_app._get_current_object(),
        event=on_login_with_method.name,
        user=user,
        login_method=login_method
    )
    return get_logged_in_user_permissions()
