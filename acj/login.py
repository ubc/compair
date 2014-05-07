import json
import logging

from flask import Blueprint, request
from flask.ext.login import login_required, login_user, logout_user

from acj.database import db_session
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
	user = Users.query.filter_by(username = username).first()
	if not user:
		logger.debug("Login failed, invalid username for: " + username)
	elif not user.verify_password(password):
		logger.debug("Login failed, invalid password for: " + username )
	else:
		# username valid, password valid, login successful
		# "remember me" functionality is available, do we want to implement?
		login_user(user)
		logger.debug("Login successful for: " + user.username);
		return json.dumps( {"userid": user.id} )

	# login unsuccessful
	return json.dumps( {"error": 'Sorry, unrecognized username or password.'} ), 400

@login_api.route('/login/logout', methods=['DELETE'])
@login_required
def logout():
	logout_user()
	return ""
