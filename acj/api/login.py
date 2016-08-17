import os
from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect, Flask, render_template
from flask_login import current_user, login_required, login_user, logout_user
from acj import cas
from acj.core import db, event
from acj.authorization import get_logged_in_user_permissions
from acj.models import User, LTIUser, LTIResourceLink, LTIUserResourceLink, UserCourse, LTIContext, ThirdPartyUser, \
    ThirdPartyType

login_api = Blueprint("login_api", __name__, url_prefix='/api')

on_user_create = event.signal('USER_CREATE')

@login_api.route('/login', methods=['POST'])
def login():
    # expecting login params to be in json format
    param = request.json
    if param is None:
        return jsonify({"error": 'Invalid login data format. Expecting json.'}), 400
    username = param['username']
    password = param['password']
    # grab the user from the username
    user = User.query.filter_by(username=username).first()
    if not user:
        current_app.logger.debug("Login failed, invalid username for: " + username)
    elif not user.verify_password(password):
        current_app.logger.debug("Login failed, invalid password for: " + username)
    else:
        permissions = authenticate(user)

        if sess.get('LTI') and sess.get('oauth_create_user_link'):
            lti_user = LTIUser.query.get_or_404(sess['lti_user'])
            lti_user.acj_user_id = user.id
        if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
            lti_context = LTIContext.query.get_or_404(sess['lti_context'])
            lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
            if lti_context.is_linked_to_course():
                user_course = UserCourse.query \
                    .filter_by(
                        user_id=user.id,
                        course_id=lti_context.acj_course_id
                    ) \
                    .one_or_none()
                if user_course is None:
                    # create new enrollment
                    new_user_course = UserCourse(user_id=user.id, course_id=lti_context.acj_course_id, course_role=lti_user_resource_link.course_role)
                    db.session.add(new_user_course)
                else:
                    user_course.course_role=lti_user_resource_link.course_role
        db.session.commit()

        return jsonify({"userid": user.id, "permissions": permissions})

    # login unsuccessful
    return jsonify({"error": 'Sorry, unrecognized username or password.'}), 400

@login_api.route('/logout', methods=['DELETE'])
@login_required
def logout():
    current_user.update_last_online()
    logout_user()  # flask-login delete user info

    if sess.get('LTI'):
        lti_resource_link = LTIResourceLink.query.get(sess['lti_resource_link'])
        if lti_resource_link:
            return_url = lti_resource_link.launch_presentation_return_url
            if return_url != None and return_url.strip() != "":
                return jsonify({'redirect': return_url})

    if sess.get('CAS_LOGIN'):
        return jsonify({'redirect': url_for('cas.logout')})

    sess.clear()

    return ""


@login_api.route('/session', methods=['GET'])
@login_required
def session():
    return jsonify({"id": current_user.id, "permissions": get_logged_in_user_permissions()})


@login_api.route('/session/permission', methods=['GET'])
@login_required
def get_permission():
    return jsonify(get_logged_in_user_permissions())


@login_api.route('/auth/cas', methods=['GET'])
def auth_cas():
    """
    CAS Authentication Endpoint. Authenticate user through CAS. If user doesn't exists,
    set message in session so that frontend can get the message through /session call
    """
    username = cas.username
    url = "/static/index.html#/lti" if sess.get('LTI') else "/"

    if username is not None:
        thirdpartyuser = ThirdPartyUser.query. \
            filter_by(
            unique_identifier=username,
            type=ThirdPartyType.cwl
        ).first()
        msg = None
        if not thirdpartyuser or not thirdpartyuser.user:
            if sess.get('oauth_create_user_link') and sess.get('LTI'):
                sess['CAS_CREATE'] = True
                sess['CAS_UNIQUE_IDENTIFIER'] = cas.username
                return redirect(
                    '/static/index.html#/oauth/create')
            else:
                current_app.logger.debug("Login failed, invalid username for: " + username)
                msg = 'You don\'t have access to this application.'
        else:
            authenticate(thirdpartyuser.user)
            if sess.get('LTI') and sess.get('oauth_create_user_link'):
                lti_user = LTIUser.query.get_or_404(sess['lti_user'])
                lti_user.acj_user_id = thirdpartyuser.user_id
                sess.pop('oauth_create_user_link')
            if sess.get('LTI') and sess.get('lti_context') and sess.get('lti_user_resource_link'):
                lti_context = LTIContext.query.get_or_404(sess['lti_context'])
                lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
                if lti_context.is_linked_to_course():
                    user_course = UserCourse.query \
                        .filter_by(
                        user_id=thirdpartyuser.user_id,
                        course_id=lti_context.acj_course_id
                    ) \
                        .one_or_none()
                    if user_course is None:
                        # create new enrollment
                        new_user_course = UserCourse(user_id=thirdpartyuser.user_id, course_id=lti_context.acj_course_id,
                                                     course_role=lti_user_resource_link.course_role)
                        db.session.add(new_user_course)
                    else:
                        user_course.course_role = lti_user_resource_link.course_role
            db.session.commit()
            sess['CAS_LOGIN'] = True
    else:
        msg = 'Login Failed. Expecting CAS username to be set.'

    if msg is not None:
        sess['CAS_AUTH_MSG'] = msg
    return redirect(url)


def authenticate(user):
    # username valid, password valid, login successful
    # "remember me" functionality is available, do we want to implement?
    user.update_last_online()
    login_user(user) # flask-login store user info
    current_app.logger.debug("Login successful for: " + user.username)
    return get_logged_in_user_permissions()
