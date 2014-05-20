import logging

from flask import Blueprint, jsonify, request
from flask.ext.login import current_user, login_required, login_user, logout_user

from acj.models import Users

logger = logging.getLogger(__name__)

login_api = Blueprint("login_api", __name__)


@login_api.route('/login/login', methods=['POST'])
def login():
	# expecting login params to be in json format
	param = request.json
	username = param['username']
	password = param['password']
	# grab the user from the username
	user = Users.query.filter_by(username=username).first()
	if not user:
		logger.debug("Login failed, invalid username for: " + username)
	elif not user.verify_password(password):
		logger.debug("Login failed, invalid password for: " + username)
	else:
		# username valid, password valid, login successful
		# "remember me" functionality is available, do we want to implement?
		user.update_lastonline()
		login_user(user) # flask-login store user info
		logger.debug("Login successful for: " + user.username)
		return jsonify({"userid": user.id})

	# login unsuccessful
	return jsonify({"error": 'Sorry, unrecognized username or password.'}), 400


@login_api.route('/login/logout', methods=['DELETE'])
@login_required
def logout():
	current_user.update_lastonline()
	logout_user() # flask-login delete user info
	return ""
