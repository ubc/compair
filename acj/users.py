from flask import Blueprint, current_app
from bouncer.constants import READ, MANAGE, EDIT, CREATE
from flask.ext.restful import Resource, marshal_with, marshal
from flask.ext.restful.reqparse import RequestParser

from flask_login import login_required, current_user
from acj import dataformat, db
from .authorization import is_user_access_restricted, require
from core import event
from .util import pagination, new_restful_api, get_model_changes

from .models import Users, UserTypesForSystem

users_api = Blueprint('users_api', __name__)
user_types_api = Blueprint('user_types_api', __name__)

new_user_parser = RequestParser()
new_user_parser.add_argument('username', type=str, required=True)
new_user_parser.add_argument('usertypesforsystem_id', type=int, required=True)
new_user_parser.add_argument('firstname', type=str, required=True)
new_user_parser.add_argument('lastname', type=str, required=True)
new_user_parser.add_argument('displayname', type=str, required=True)
new_user_parser.add_argument('email', type=str, required=True)
new_user_parser.add_argument('password', type=str, required=True)

existing_user_parser = RequestParser()
existing_user_parser.add_argument('id', type=int, required=True)
existing_user_parser.add_argument('username', type=str, required=True)
existing_user_parser.add_argument('usertypesforsystem_id', type=int, required=True)
existing_user_parser.add_argument('firstname', type=str, required=True)
existing_user_parser.add_argument('lastname', type=str, required=True)
existing_user_parser.add_argument('displayname', type=str, required=True)
existing_user_parser.add_argument('email', type=str, required=True)

update_password_parser = RequestParser()
update_password_parser.add_argument('oldpassword', type=str, required=True)
update_password_parser.add_argument('newpassword', type=str, required=True)

# events
on_user_modified = event.signal('USER_MODIFIED')
on_user_get = event.signal('USER_GET')
on_user_list_get = event.signal('USER_LIST_GET')
on_user_create = event.signal('USER_CREATE')
on_user_course_get = event.signal('USER_COURSE_GET')
on_user_password_update = event.signal('USER_PASSWORD_UPDATE')


# /id
class UserAPI(Resource):
	@login_required
	def get(self, id):
		user = Users.query.get_or_404(id)
		on_user_get.send(current_app._get_current_object(), event_name=on_user_get.name,
							  user=current_user, data={'id': id})
		return marshal(user, dataformat.getUsers(is_user_access_restricted(user)))
	@login_required
	def post(self, id):
		user = Users.query.get_or_404(id)
		require(EDIT, user)
		params = existing_user_parser.parse_args()
		# make sure the user id in the url and the id matches
		if params['id'] != id:
			return {"error":"User id does not match URL."}, 400
		user.username = params.get("username", user.username)
		user.usertypesforsystem_id = params.get("usertypesforsystem_id", user.usertypesforsystem_id)
		user.firstname = params.get("firstname", user.firstname)
		user.lastname = params.get("lastname", user.lastname)
		user.displayname = params.get("displayname", user.displayname)
		user.email = params.get("email", user.email)
		changes = get_model_changes(user)
		db.session.commit()
		on_user_modified.send(
			current_app._get_current_object(),
			event_name=on_user_modified.name,
			user=current_user,
			data={'id': id, 'changes': changes})
		return marshal(user, dataformat.getUsers())


# /
class UserListAPI(Resource):
	@login_required
	@pagination(Users)
	@marshal_with(dataformat.getUsers(False))
	def get(self, objects):
		require(MANAGE, Users)
		on_user_list_get.send(
			current_app._get_current_object(),
			event_name=on_user_list_get.name,
			user=current_user)
		return objects

	def post(self):
		user = Users()
		require(CREATE, user)
		params = new_user_parser.parse_args()
		user.username = params.get("username")
		username = Users.query.filter(Users.username==user.username).first()
		if username is not None:
			return {"error":"This username already exists. Please pick another."}, 409
		user.password = params.get("password")
		user.usertypesforsystem_id = params.get("usertypesforsystem_id")
		user.email = params.get("email")
		user.firstname = params.get("firstname")
		user.lastname = params.get("lastname")
		user.displayname = params.get("displayname")
		displayname = Users.query.filter(Users.displayname==user.displayname).first()
		if displayname is not None:
			return {"error":"This display name already exists. Please pick another."}, 409
		db.session.add(user)
		db.session.commit()
		on_user_create.send(
			current_app._get_current_object(),
			event_name=on_user_create.name,
			user=current_user,
			data=marshal(user, dataformat.getUsers(False)))
		return marshal(user, dataformat.getUsers())


# /id/courses
class UserCourseListAPI(Resource):
	@login_required
	def get(self, id):
		user = Users.query.get_or_404(id)
		# we want to list courses only, so only check the association table
		coursesandusers = []
		for courseanduser in user.coursesandusers:
			require(READ, courseanduser)
			coursesandusers.append(courseanduser)

		# sort alphabetically by course name
		coursesandusers.sort(key=lambda courseanduser: courseanduser.course.name)

		# TODO REMOVE COURSES WHERE USER IS DROPPED?
		# TODO REMOVE COURSES WHERE COURSE IS UNAVAILABLE?

		on_user_course_get.send(
			current_app._get_current_object(),
			event_name=on_user_course_get.name,
			user=current_user,
			data={'userid': id})

		return {'objects': marshal(coursesandusers, dataformat.getCoursesAndUsers(include_user=False))}


# /
class UserTypesAPI(Resource):
	@login_required
	def get(self):
		types = UserTypesForSystem.query.\
			order_by("id").all()
		return marshal(types, dataformat.getUserTypesForSystem())


# /password
class UserUpdatePasswordAPI(Resource):
	@login_required
	def post(self, id):
		user = Users.query.get_or_404(id)
		require(EDIT, user)
		params = update_password_parser.parse_args()
		oldpassword = params.get('oldpassword')
		if user.verify_password(oldpassword):
			user.password = params.get('newpassword')
			db.session.add(user)
			db.session.commit()
			on_user_password_update.send(
				current_app._get_current_object(),
				event_name=on_user_password_update.name,
				user=current_user)
			return marshal(user, dataformat.getUsers(False))
		else:
			return {"error": "The old password is incorrect."}, 401

api = new_restful_api(users_api)
api.add_resource(UserAPI, '/<int:id>')
api.add_resource(UserListAPI, '')
api.add_resource(UserCourseListAPI, '/<int:id>/courses')
api.add_resource(UserUpdatePasswordAPI, '/password/<int:id>')
apiT = new_restful_api(user_types_api)
apiT.add_resource(UserTypesAPI, '')

#def import_users(list, group=True):
#	schema = {
#			'type': 'object',
#			'properties': {
#				'username': {'type': 'string'},
#				'usertype': {'type': 'string',
#					'enum': ['Admin', 'Student', 'Teacher']},
#				'password': {'type': 'string'},
#				'email': {'type': 'string', 'format': 'email', 'required': False},
#				'firstname': {'type': 'string', 'required': False},
#				'lastname': {'type': 'string', 'required': False},
#				'display': {'type': 'string', 'required': False}
#				}
#			}
#	# query all used usernames and displays
#	query = Users.query.with_entities(Users.username).all()
#	usernames = [item for sublist in query for item in sublist]
#	query = Users.query.with_entities(Users.displayname).all()
#	displays = [item for sublist in query for item in sublist]
#	duplicate = []
#	error = []
#	success = []
#	for user in list:
#
#		try:
#			validictory.validate(user, schema)
#		except ValueError as err:
#			error.append({'user': user, 'msg': str(err), 'validation': True})
#			continue
#
#		# fill in empty values if they don't exist
#		if not 'firstname' in user:
#			user['firstname'] = ''
#		if not 'lastname' in user:
#			user['lastname'] = ''
#		if not 'display' in user:
#			user['display'] = ''
#
#		if user['username'] in duplicate:
#			error.append({'user': user, 'msg': 'Duplicate username in file'})
#			continue
#		if user['username'] in usernames:
#			if not group:
#				error.append({'user': user, 'msg': 'Username already exists'})
#			else:
#				u = Users.query.filter_by( username = user['username'] ).first()
#				if u.userrole.role == 'Student':
#					user = {'id': u.id, 'username': u.username, 'password': 'hidden', 'usertype': 'Student',
#							'email': u.email, 'firstname': u.firstname, 'lastname': u.lastname, 'display': u.display}
#					duplicate.append(user['username'])
#					success.append({'user': user})
#				else :
#					error.append({'user': user, 'msg': 'User is not a student'})
#			continue
#		if user['display'] in displays:
#			if not group:
#				error.append({'user': user, 'msg': 'Display name already exists'})
#				continue
#			integer = random.randrange(1000, 9999)
#			user['display'] = user['display'] + ' ' + str(integer)
#		if 'email' in user:
#			email = user['email']
#			if not re.match(r"[^@]+@[^@]+", email):
#				error.append({'user': user, 'msg': 'Incorrect email format'})
#				continue
#		else:
#			email = ''
#		usertype = UserTypesForSystem.query.filter_by(name = user['usertype']).first().id
#		newUser = Users(
#			username = user['username'],
#			usertypesforsystem = usertype,
#			email = email,
#			firstname = user['firstname'],
#			lastname = user['lastname'],
#			displayname = user['display']
#		)
#		newUser.set_password(user['password'])
#		db_session.add(newUser)
#		status = db_session.commit()
#		if not status:
#			error.append({'user': user, 'msg': 'Error'})
#		else:
#			# if successful append usernames + displays to prevent duplicates
#			duplicate.append(user['username'])
#			displays.append(user['display'])
#			user['id'] = newUser.id
#			success.append({'user': user})
#	return {'error': error, 'success': success}
#
#@teacher.require(http_exception=401)
#def csv_user_parser(filename):
#	reader = csv.reader(open(filename, "rU"))
#	list = []
#	error = []
#	for row in reader:
#		# filter removes trailing empty columns in cases where some rows have more than 4 columns
#		row = filter(None, row)
#		if len(row) != 4:
#			error.append({'user': {'username': 'N/A', 'display': 'N/A'}, 'msg': str(row) + ' is an invalid row'})
#			continue
#		user = {'username': row[0], 'password': password_generator(), 'usertype': 'Student',
#				'email': row[3], 'firstname': row[1], 'lastname': row[2], 'display': row[1] + ' ' + row[2]}
#		list.append(user)
#	return {'list': list, 'error': error}
#
#@teacher.require(http_exception=401)
#def password_generator(size=16, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
#	return ''.join(random.choice(chars) for x in range(size))
#
#@users_api.route('/userimport', methods=['POST'])
#@teacher.require(http_exception=401)
#def user_import():
#	file = request.files['file']
#	if not file or not allowed_file(file.filename):
#		return json.dumps( {"completed": True, "msg": "Please provide a valid file"} )
#	schema = {
#			'type': 'object',
#			'properties': {
#				'course': {'type': 'string'}
#				}
#			}
#	try:
#		validictory.validate(request.form, schema)
#	except ValueError, error:
#		return json.dumps( {"completed": True} )
#	courseId = request.form['course']
#	retval = []
#	ts = time.time()
#	timestamp = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
#	filename = timestamp + '-' + secure_filename(file.filename)
#	file.save(os.path.join(users_api.config['UPLOAD_FOLDER'], filename))
#	content = csv_user_parser(os.path.join(users_api.config['UPLOAD_FOLDER'], filename))
#	result = import_users(content['list'])
#	enrolled = []
#	success = []
#	if len(result['success']):
#		enrolled = enrol_users(result['success'], courseId)
#		success = enrolled['success']
#		enrolled = enrolled['error']
#	error = result['error'] + enrolled + content['error']
#	return json.dumps( {"success": success, "error": error, "completed": True} )
#
#@users_api.route('/user/<id>', methods=['POST'])
#@teacher.require(http_exception=401)
#def create_user(id):
#	result = import_users([request.json], False)
#	return json.dumps(result)
#
#@users_api.route('/user/<id>', methods=['PUT'])
#def edit_user(id):
#	user = ''
#	loggedUser = Users.query.filter_by(username = session['username']).first()
#	if id == '0':
#		user = loggedUser
#	elif id:
#		user = Users.query.filter_by(id = id).first()
#	param = request.json
#	schema = {
#			'type': 'object',
#			'properties': {
#				'email': {'type': 'string', 'format': 'email', 'required': False},
#				'display': {'type': 'string'},
#				'password': {
#					'type': 'object',
#					'properties': {
#						'old': {'type': 'string'},
#						'new': {'type': 'string'},
#						},
#					'required': False
#					},
#				}
#			}
#	try:
#		validictory.validate(param, schema)
#	except ValueError as error:
#		print (str(error))
#		return ''
#	display = param['display']
#	query = Users.query.filter(Users.id != user.id).filter_by(display = display).first()
#	if query:
#		db_session.rollback()
#		return json.dumps( {"flash": 'Display name already exists'} )
#	user.display = display
#	if 'email' in param:
#		email = param['email']
#		if not re.match(r"[^@]+@[^@]+", email):
#			db_session.rollback()
#			return json.dumps( {"flash": 'Incorrect email format'} )
#		user.email = email
#	else:
#		user.email = ''
#	if 'password' in param:
#		if not user.verify_password(param['password']['old']):
#			db_session.rollback()
#			return json.dumps( {"flash": 'Incorrect password'} )
#		user.set_password(param['password']['new'])
#	usertype = user.usertypeforysystem
#	db_session.commit()
#	return json.dumps( {"msg": "PASS", "usertype": usertype} )
#
#@users_api.route('/admin', methods=['POST'])
#def create_admin():
#	print "Here 1"
#	result = import_users([request.json], False)
#	print "Here 2"
#	file = open('tmp/installed.txt', 'w+')
#	print "Here 3"
#	return json.dumps(result)
#
#@users_api.route('/password/<uid>')
#@admin.require(http_exception=401)
#def reset_password(uid):
#	user = User.query.filter_by( id = uid ).first()
#	password = password_generator()
#	user.password = hasher.hash_password( password )
#	commit()
#	return json.dumps( {"resetpassword": password} )
#
