from acj import app
from general import admin, teacher, commit, hasher
from sqlalchemy_acj import db_session, User, UserRole
from flask import session, request
from werkzeug import secure_filename
import json
import validictory
import random
import re
import datetime
import os
import csv
import string

def import_users(list, group=True):
	schema = {
			'type': 'object',
			'properties': {
				'username': {'type': 'string'},
				'usertype': {'type': 'string', 
					'enum': ['Admin', 'Student', 'Teacher']},
				'password': {'type': 'string'},
				'email': {'type': 'string', 'format': 'email', 'required': False},
				'firstname': {'type': 'string', 'required': False},
				'lastname': {'type': 'string', 'required': False},
				'display': {'type': 'string', 'required': False}
				}
			}
	# query all used usernames and displays
	query = User.query.with_entities(User.username).all()
	usernames = [item for sublist in query for item in sublist]
	query = User.query.with_entities(User.display).all()
	displays = [item for sublist in query for item in sublist]
	duplicate = []
	error = []
	success = []
	for user in list:

		try:
			validictory.validate(user, schema)
		except ValueError, err:
			error.append({'user': user, 'msg': str(err), 'validation': True})
			continue

		# fill in empty values if they don't exist
		if not 'firstname' in user:
			user['firstname'] = ''
		if not 'lastname' in user:
			user['lastname'] = ''
		if not 'display' in user:
			user['display'] = ''

		if user['username'] in duplicate:
			error.append({'user': user, 'msg': 'Duplicate username in file'})
			continue
		if user['username'] in usernames:
			if not group:
				error.append({'user': user, 'msg': 'Username already exists'})
			else:
				u = User.query.filter_by( username = user['username'] ).first()
				if u.userrole.role == 'Student':
					user = {'id': u.id, 'username': u.username, 'password': 'hidden', 'usertype': 'Student',
							'email': u.email, 'firstname': u.firstname, 'lastname': u.lastname, 'display': u.display}
					duplicate.append(user['username'])
					success.append({'user': user})
				else : 
					error.append({'user': user, 'msg': 'User is not a student'})
			continue
		if user['display'] in displays:
			if not group:
				error.append({'user': user, 'msg': 'Display name already exists'})
				continue
			integer = random.randrange(1000, 9999)
			user['display'] = user['display'] + ' ' + str(integer)
		if 'email' in user:
			email = user['email']
			if not re.match(r"[^@]+@[^@]+", email):
				error.append({'user': user, 'msg': 'Incorrect email format'})
				continue
		else:
			email = ''
		usertype = UserRole.query.filter_by(role = user['usertype']).first().id
		table = User(user['username'], hasher.hash_password(user['password']), usertype, email, user['firstname'], user['lastname'], user['display'])
		db_session.add(table)
		status = commit()
		if not status:
			error.append({'user': user, 'msg': 'Error'})
		else:
			# if successful append usernames + displays to prevent duplicates
			duplicate.append(user['username'])
			displays.append(user['display'])
			user['id'] = table.id
			success.append({'user': user})
	return {'error': error, 'success': success}

@teacher.require(http_exception=401)
def csv_user_parser(filename):
	reader = csv.reader(open(filename, "rU"))
	list = []
	error = []
	for row in reader:
		# filter removes trailing empty columns in cases where some rows have more than 4 columns
		row = filter(None, row)
		if len(row) != 4:
			error.append({'user': {'username': 'N/A', 'display': 'N/A'}, 'msg': str(row) + ' is an invalid row'})
			continue
		user = {'username': row[0], 'password': password_generator(), 'usertype': 'Student',
				'email': row[3], 'firstname': row[1], 'lastname': row[2], 'display': row[1] + ' ' + row[2]}
		list.append(user)
	return {'list': list, 'error': error}

@teacher.require(http_exception=401)
def password_generator(size=16, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

@app.route('/userimport', methods=['POST'])
@teacher.require(http_exception=401)
def user_import():
	file = request.files['file']
	if not file or not allowed_file(file.filename):
		return json.dumps( {"completed": True, "msg": "Please provide a valid file"} )
	schema = {
			'type': 'object',
			'properties': {
				'course': {'type': 'string'}
				}
			}
	try:
		validictory.validate(request.form, schema)
	except ValueError, error:
		return json.dumps( {"completed": True} )
	courseId = request.form['course']
	retval = []
	ts = time.time()
	timestamp = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
	filename = timestamp + '-' + secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	content = csv_user_parser(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	result = import_users(content['list'])
	enrolled = []
	success = []
	if len(result['success']):
		enrolled = enrol_users(result['success'], courseId)
		success = enrolled['success']
		enrolled = enrolled['error']
	error = result['error'] + enrolled + content['error']
	return json.dumps( {"success": success, "error": error, "completed": True} )

@app.route('/user/<id>', methods=['POST'])
@teacher.require(http_exception=401)
def create_user(id):
	result = import_users([request.json], False)
	return json.dumps(result)

@app.route('/user/<id>', methods=['PUT'])
def edit_user(id):
	user = ''
	loggedUser = User.query.filter_by(username = session['username']).first()
	if id == '0':
		user = loggedUser 
	elif id:
		user = User.query.filter_by(id = id).first()
	param = request.json
	schema = {
			'type': 'object',
			'properties': {
				'email': {'type': 'string', 'format': 'email', 'required': False},
				'display': {'type': 'string'},
				'password': {
					'type': 'object', 
					'properties': {
						'old': {'type': 'string'},
						'new': {'type': 'string'},
						},
					'required': False
					},                        
				}
			}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return ''
	display = param['display']
	query = User.query.filter(User.id != user.id).filter_by(display = display).first()
	if query:
		db_session.rollback()
		return json.dumps( {"flash": 'Display name already exists'} )
	user.display = display
	if 'email' in param:
		email = param['email']
		if not re.match(r"[^@]+@[^@]+", email):
			db_session.rollback()
			return json.dumps( {"flash": 'Incorrect email format'} )
		user.email = email
	else:
		user.email = ''
	if 'password' in param:
		if not hasher.check_password( param['password']['old'], user.password ):
			db_session.rollback()
			return json.dumps( {"flash": 'Incorrect password'} )
		newpassword = param['password']['new']
		newpassword = hasher.hash_password( newpassword )
		user.password = newpassword
	usertype = user.userrole.role
	commit()
	return json.dumps( {"msg": "PASS", "usertype": usertype} )

@app.route('/admin', methods=['POST'])
def create_admin():
	print "Here 1"
	result = import_users([request.json], False)
	print "Here 2"
	file = open('tmp/installed.txt', 'w+')
	print "Here 3"
	return json.dumps(result)

@app.route('/allUsers')
@admin.require(http_exception=401)
def all_users():
	query = User.query.order_by(User.lastname)
	users = []
	for user in query:
		users.append( {"uid": user.id, "username": user.username, "fullname": user.fullname, "display": user.display, "type": user.userrole.role} )
	db_session.rollback()
	return json.dumps( {'users': users})

@app.route('/password/<uid>')
@admin.require(http_exception=401)
def reset_password(uid):
	user = User.query.filter_by( id = uid ).first()
	password = password_generator()
	user.password = hasher.hash_password( password )
	commit()
	return json.dumps( {"resetpassword": password} )

@app.route('/user/<id>')
def user_profile(id):
	user = ''
	retval = ''
	loggedUser = User.query.filter_by(username = session['username']).first()
	if id == '0':
		user = loggedUser
	elif id and loggedUser.userrole.role != 'Student':
		user = User.query.filter_by(id = id).first()
	if user:
		retval = json.dumps({"username":user.username, "fullname":user.fullname, "display":user.display, "email":user.email, "usertype":user.userrole.role, "loggedType": loggedUser.usertype, "loggedName": loggedUser.username})
	db_session.rollback()
	return retval
