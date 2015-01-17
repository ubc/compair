from flask import Blueprint, jsonify, request, session as sess, current_app, url_for, redirect
from flask_login import current_user, login_required, login_user, logout_user
from flask_cas.routing import logout as cas_logout

from .authorization import get_logged_in_user_permissions
from .models import Users


login_api = Blueprint("login_api", __name__, url_prefix='/api')


@login_api.route('/login', methods=['POST'])
def login():
	# expecting login params to be in json format
	param = request.json
	if param == None:
		return jsonify({"error": 'Invalid login data format. Expecting json.'}), 400
	username = param['username']
	password = param['password']
	# grab the user from the username
	user = Users.query.filter_by(username=username).first()
	if not user:
		current_app.logger.debug("Login failed, invalid username for: " + username)
	elif not user.verify_password(password):
		current_app.logger.debug("Login failed, invalid password for: " + username)
	else:
		permissions = authenticate(user)
		return jsonify({"userid": user.id, "permissions": permissions})

	# login unsuccessful
	return jsonify({"error": 'Sorry, unrecognized username or password.'}), 400


@login_api.route('/logout', methods=['DELETE'])
@login_required
def logout():
	current_user.update_lastonline()
	logout_user()  # flask-login delete user info
	if 'CAS_LOGIN' in sess:
		sess.pop('CAS_LOGIN')
		return jsonify({'redirect': url_for('cas.logout')})
	else:
		return ""

@login_api.route('/session', methods=['GET'])
@login_required
def session():
	return jsonify({"id": current_user.id, "permissions": get_logged_in_user_permissions()})

@login_api.route('/session/permission', methods=['GET'])
@login_required
def get_permission():
	return jsonify(get_logged_in_user_permissions())


def authenticate(user):
	# username valid, password valid, login successful
	# "remember me" functionality is available, do we want to implement?
	user.update_lastonline()
	login_user(user)  # flask-login store user info
	current_app.logger.debug("Login successful for: " + user.username)
	return get_logged_in_user_permissions()
