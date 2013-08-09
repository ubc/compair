from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import init_db, db_session, User, Judgement, Script, Course, Question, Enrollment, CommentA, CommentQ, Entry
from flask_principal import ActionNeed, AnonymousIdentity, Identity, identity_changed, identity_loaded, Permission, Principal, RoleNeed
from sqlalchemy import desc, func, select
from random import shuffle
from math import log10, exp
import exceptions
import MySQLdb
import re
import phpass
import json
import datetime
import validictory
import os
import time
import csv
import string
import random
from werkzeug import secure_filename


app = Flask(__name__)
init_db()
hasher = phpass.PasswordHash()
principals = Principal(app)

UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = set(['csv', 'txt'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Needs
is_admin = RoleNeed('Admin')
is_teacher = RoleNeed('Teacher')
is_student = RoleNeed('Student')

# Permissions
admin = Permission(is_admin)
admin.description = "Admin's permissions"
teacher = Permission(is_teacher)
teacher.description = "Teacher's permissions"
student = Permission(is_student)
student.description = "Student's permissions"

apps_needs = [is_admin, is_teacher, is_student]
apps_permissions = [admin, teacher, student]

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
			return obj.strftime("%F %r")
        return json.JSONEncoder.default(self, obj) 

def commit():
	try:
		db_session.commit()
	except:
		db_session.rollback()
		return False
	return True

@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()

@app.route('/')
def index():
	return redirect(url_for('static', filename="index.html"))

@app.route('/isinstalled')
def is_installed():
	if os.access('tmp/installed.txt', os.W_OK):
		return json.dumps({'installed': True})
	return json.dumps({'installed': False})

@app.route('/install', methods=['GET'])
def install():
	requirements = []
	writable = True if os.access('tmp', os.W_OK) else False
	requirements.append( { 'text': 'tmp folder is writable', 'boolean': writable } )
	return json.dumps( {'requirements': requirements} )

@app.route('/script/<id>', methods=['GET'])
@student.require(http_exception=401)
def get_script(id):
	print(id)
	query = Script.query.filter_by(id = id).first()
	if not query:
		db_session.rollback()
		return json.dumps({"msg": "No matching script"})
	ret_val = json.dumps( {"content": query.content} )
	db_session.rollback()
	return ret_val

@app.route('/script/<id>', methods=['POST'])
@student.require(http_exception=401)
def mark_script(id):
	query = Script.query.filter_by(id = id).first()
	if not query:
		db_session.rollback()
		return json.dumps({"msg": "No matching script"})
	query.wins = query.wins + 1
	query.count = query.count + 1
	param = request.json
	sidl = param['sidl']
	sidr = param['sidr']
	sid = 0
	if sidl == int(id):
		print ('sidl == id')
		sid = sidr
	elif sidr == int(id):
		print ('sidr == id')
		sid = sidl
	query = Script.query.filter_by(id = sid).first()
	query.count = query.count + 1
	estimate_score(query.qid)
	query = User.query.filter_by(username = session['username']).first()
	uid = query.id
	if sidl > sidr:
		temp = sidr
		sidr = sidl
		sidl = temp
	table = Judgement(uid, sidl, sidr, id)
	db_session.add(table)
	commit()
	return json.dumps({"msg": "Script & Judgement updated"})

@app.route('/answer/<id>', methods=['POST'])
@student.require(http_exception=401)
def post_answer(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	qid = id
	user = User.query.filter_by(username = session['username']).first()
	uid = user.id
	author = user.display
	content = param['content']
	table = Script(qid, uid, content)
	db_session.add(table)
	db_session.commit()
	script = Script.query.order_by( Script.time.desc() ).first()
	retval = json.dumps({"id": script.id, "author": author, "time": str(script.time), "content": script.content, "score":script.score, "avatar": user.avatar})
	db_session.rollback()
	return retval

@app.route('/answer/<id>', methods=['PUT'])
@student.require(http_exception=401)
def edit_answer(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	script = Script.query.filter_by(id = id).first()
	script.content = param['content']
	commit()
	return json.dumps({"msg": "PASS"})

@app.route('/answer/<id>', methods=['DELETE'])
@student.require(http_exception=401)
def delete_answer(id):
	script = Script.query.filter_by(id = id).first()
	db_session.delete(script)
	commit()
	return json.dumps({"msg": "PASS"})

@app.route('/login', methods=['GET'])
def logincheck():
	if 'username' in session:
		user = User.query.filter_by(username = session['username']).first()
		retval = json.dumps( {"display": user.display, "usertype": user.usertype} )
		db_session.rollback()
		return retval
	return ''

@app.route('/login', methods=['POST'])
def login():
	param = request.json
	username = param['username']
	password = param['password']
	query = User.query.filter_by(username = username).first()
	if not query:
		db_session.rollback()
		return json.dumps( {"msg": 'Incorrect username or password'} )
	hx = query.password
	if hasher.check_password( password, hx ):
		session['username'] = username
		display = User.query.filter_by(username = username).first().display
		db_session.rollback()
		identity = Identity('only_' + query.usertype)
		identity_changed.send(app, identity=identity)
		return json.dumps( {"display": display} )
	db_session.rollback()
	return json.dumps( {"msg": 'Incorrect username or password'} )

@app.route('/logout')
def logout():
	session.pop('username', None)
	for key in ['identity.name', 'identity.auth_type']:
		session.pop(key, None)
	identity_changed.send(app, identity=AnonymousIdentity())
	return json.dumps( {"status": 'logged out'} )

@app.route('/user')
def user_profile():
	user = User.query.filter_by(username = session['username']).first()
	retval = json.dumps({"username":user.username, "fullname":user.fullname, "display":user.display, "email":user.email, "usertype":user.usertype, "password":user.password})
	db_session.rollback()
	return retval

@app.route('/allUsers')
@admin.require(http_exception=401)
def all_users():
	query = User.query.order_by(User.lastname)
	users = []
	for user in query:
		users.append( {"fullname": user.fullname, "display": user.display, "type": user.usertype} )
	db_session.rollback()
	return json.dumps( {'users': users})

@app.route('/user', methods=['POST'])
def create_user():
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'username': {'type': 'string'},
			'usertype': {'type': 'string', 'enum': ['Admin', 'Student', 'Teacher']},
			'password': {'type': 'string'},
			'email': {'type': 'string', 'format': 'email', 'required': False},
			'firstname': {'type': 'string'},
			'lastname': {'type': 'string'},
			'display': {'type': 'string'},
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	username = param['username']
	query = User.query.filter_by(username = username).first()
	if query:
		db_session.rollback()
		return json.dumps( {"flash": 'Username already exists'} )
	display = param['display']
	query = User.query.filter_by(display = display).first()
	if query:
		db_session.rollback()
		return json.dumps( {"flash": 'Display name already exists'} )
	password = param['password']
	password = hasher.hash_password( password )
	usertype = param['usertype']
	if 'email' in param:
		email = param['email']
		if not re.match(r"[^@]+@[^@]+", email):
			db_session.rollback()
			return json.dumps( {"flash": 'Incorrect email format'} )
	else:
		email = ''
	firstname = param['firstname']
	lastname = param['lastname']
	table = User(username, password, usertype, email, firstname, lastname, display)
	db_session.add(table)
	commit()
	if not os.access('tmp/installed.txt', os.W_OK):
		file = open('tmp/installed.txt', 'w+')
	return ''

@app.route('/user', methods=['PUT'])
def edit_user():
	user = User.query.filter_by(username = session['username']).first()
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'password': {'type': 'string'},
			'newpassword': {'type': 'string', 'required': False},
			'email': {'type': 'string', 'format': 'email', 'required': False},
			'display': {'type': 'string'},
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"flash": str(error)} )
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
	if 'newpassword' in param:
		if not hasher.check_password( param['password'], user.password ):
			db_session.rollback()
			return json.dumps( {"flash": 'Incorrect password'} )
		newpassword = param['newpassword']
		newpassword = hasher.hash_password( newpassword )
		user.password = newpassword
	commit()
	return json.dumps( {"msg": "PASS"} )

@app.route('/pickscript/<id>', methods=['GET'])
@student.require(http_exception=401)
def pick_script(id):
	query = Script.query.filter_by(qid = id).order_by( Script.count.desc() ).first()
	question = Question.query.filter_by(id = id).first()
	course = Course.query.filter_by(id = question.cid).first()
	if not query:
		retval = json.dumps( {"course": course.name, "question": question.content} )
		db_session.rollback()
		return retval
	max = query.count
	query = Script.query.filter_by(qid = id).order_by( Script.count ).first()
	min = query.count
	print ('max: ' + str(max))
	print ('min: ' + str(min))
	if max == min:
		max = max + 1 
	query = Script.query.filter_by(qid = id).order_by( Script.count ).limit(10).all()
	index = 0
	for script in query:
		if script.count >= max:
			query[:index]
			break
		index = index + 1
	shuffle( query )
	# why is this here?
	# query[2:]
	fresh = get_fresh_pair( query )
	if not fresh:
		print 'judged them all'
		retval = json.dumps( {"question": question.content} ) 
		db_session.rollback()
		return retval
	print ('freshl: ' + str(fresh[0]))
	print ('freshr: ' + str(fresh[1]))
	retval = json.dumps( {"cid": course.id, "course": course.name, "question": question.content, "sidl": fresh[0], "sidr": fresh[1]} )
	db_session.rollback()
	return retval

@student.require(http_exception=401)
def get_fresh_pair( scripts ):
	uid = User.query.filter_by(username = session['username']).first().id
	index = 0
	for scriptl in scripts:
		index = index + 1
		print ('index: ' + str(index))
		print (scripts[index:])
		if uid != scriptl.uid:
			for scriptr in scripts[index:]:
				if uid != scriptr.uid:
					sidl = scriptl.id
					sidr = scriptr.id
					print ('uid: ' + str(uid))
					print ('sid: ' + str(sidl))
					print ('sid: ' + str(sidr))
					if sidl > sidr:
						temp = sidr
						sidr = sidl
						sidl = temp
					query = Judgement.query.filter_by(uid = uid).filter_by(sidl = sidl).filter_by(sidr = sidr).first()
					if not query:
						db_session.rollback()
						return [sidl, sidr]
	db_session.rollback()
	return ''

@app.route('/randquestion')
@student.require(http_exception=401)
def random_question():
	script = Script.query.order_by( Script.count ).first()
	if not script:
		return ''
	scripts = Script.query.filter_by( count = script.count ).all()
	print ('initial scripts: ' + str(scripts))
	user = User.query.filter_by( username = session['username'] ).first()
	shuffle( scripts )
	lowest0 = ''
	qid = ''
	lowest1 = ''
	for script in scripts:
		question = Question.query.filter_by( id = script.qid ).first()
		enrolled = Enrollment.query.filter_by( cid = question.cid ).filter_by( uid = user.id ).first()
		if not enrolled:
			continue
		print ('in loop, script: ' + str(script))
		print ('in loop, lowest0: ' + str(lowest0))
		print ('in loop, lowest1: ' + str(lowest1))
		query = Script.query.filter_by(qid = script.qid).order_by( Script.count ).limit(10).all()
		if get_fresh_pair(query):
			sum = query[0].count + query[1].count
			if lowest0 == '':
				lowest0 = sum
				qid = script.qid
				print ('in if, lowest0: ' + str(lowest0))
			else:
				lowest1 = sum
				print ('in if, lowest1: ' + str(lowest1))
				if lowest0 > lowest1:
					qid = script.qid
				print ('retval: ' + str(qid))
				retval = json.dumps( {"question": qid} )
				db_session.rollback()
				return retval
	print ('RETURN: SOMETHING IS NOT RIGHT')
	db_session.rollback()
	return ''

@app.route('/cjmodel')
def produce_cj_model():
	scripts = Script.query.order_by( Script.id ).all()
	index = 0
	for scriptl in scripts:
		lwins = scriptl.wins
		for scriptr in scripts:
			if scriptl != scriptr:
				rwins = scriptr.wins
				odds = (lwins/scriptl.count) / (rwins/scriptr.count) 
				diff = log10( odds )
				table =  CJ_Model(scriptl.id, scriptr.id, diff)
				db_session.add(table)
	commit()
	return '1001110100101010001011010101010'


def estimate_score(id):
	scripts = Script.query.filter_by(qid = id).order_by( Script.id ).all()
	for scriptl in scripts:
		sidl = scriptl.id
		print ('sidl: ' + str(sidl))
		sigma = 0
		lwins = scriptl.wins
		for scriptr in scripts:
			if scriptl != scriptr:
				rwins = scriptr.wins
				print ('loop sidr: ' + str(scriptr.id))
				if lwins + rwins == 0:
					prob = 0
				else:
					prob = lwins / (lwins + rwins)
				print ('prob: ' + str(prob))
				sigma = sigma + prob
				print ('sigma: ' + str(sigma))
		print ('out of inner loop')
		query = Script.query.filter_by(id = sidl).first()
		query.score = sigma
	db_session.commit()
	return '101010100010110'
		
@app.route('/ranking/<id>')
@student.require(http_exception=401)
def marked_scripts(id):
	scripts = Script.query.filter_by(qid = id).order_by( Script.score.desc() ).all() 
	slst = []
	for script in scripts:
		author = User.query.filter_by(id = script.uid).first()
		slst.append( {"id": script.id, "title": script.title, "author": author.display, "time": str(script.time), "content": script.content, "score": script.score, "comments": [], "avatar": author.avatar} )
	print ('what is happneing')
	print ( slst )
	question = Question.query.filter_by(id = id).first()
	course = Course.query.filter_by(id = question.cid).first()
	user = User.query.filter_by(username = session['username']).first()
	retval = json.dumps( {"display": user.display, "usertype": user.usertype, "cid": course.id, "course": course.name, "question": question.content, "scripts": slst} )
	db_session.rollback()
	return retval

@app.route('/ranking')
@student.require(http_exception=401)
def total_ranking():
	scripts = Script.query.order_by( Script.score.desc() ).all()
	lst = []
	for script in scripts:
		question = Question.query.filter_by(id = script.qid).first()
		course = Course.query.filter_by(id = question.cid).first()
		author = User.query.filter_by(id = script.uid).first().display
		lst.append( {"course": course.name, "question": question.content, "author": author, "time": str(script.time), "content": script.content, "score": script.score } )
	db_session.rollback()
	return json.dumps( {"scripts": lst} )

def get_comments(type, id):
	comments = []
	lst = []
	if (type == 'answer'):
		comments = CommentA.query.filter_by(sid = id).order_by( CommentA.time ).all()
	elif (type == 'question'):
		comments = CommentQ.query.filter_by(qid = id).order_by( CommentQ.time ).all()
	for comment in comments:
		author = User.query.filter_by(id = comment.uid).first()
		lst.append( {"id": comment.id, "author": author.display, "time": str(comment.time), "content": comment.content, "avatar": author.avatar} )
	retval = json.dumps( {"comments": lst} )
	db_session.rollback()
	return retval

def make_comment(type, id, content):
	table = ''
	uid = User.query.filter_by(username = session['username']).first().id
	if (type == 'answer'):
		table = CommentA(id, uid, content)
	elif (type == 'question'):
		print ('at least in question')
		table = CommentQ(id, uid, content)
	db_session.add(table)
	db_session.commit()
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.order_by( CommentA.time.desc() ).first()
	elif (type == 'question'):
		print ('at least in question')
		comment = CommentQ.query.order_by( CommentQ.time.desc() ).first()
	author = User.query.filter_by(id = comment.uid).first()
	retval = json.dumps({"comment": {"id": comment.id, "author": author.display, "time": str(comment.time), "content": comment.content, "avatar": author.avatar}})
	db_session.rollback()
	return retval

def edit_comment(type, id, content):
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.filter_by(id = id).first()
	elif (type == 'question'):
		comment = CommentQ.query.filter_by(id = id).first()
	comment.content = content
	db_session.commit()
	db_session.rollback()
	return json.dumps({"msg": "PASS"})

def delete_comment(type, id):
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.filter_by(id = id).first()
	elif (type == 'question'):
		comment = CommentQ.query.filter_by(id = id).first()
	db_session.delete(comment)
	commit()
	return json.dumps({"msg": "PASS"})


@app.route('/answer/<id>/comment')
def get_commentsA(id):
	return get_comments('answer', id)


@app.route('/answer/<id>/comment', methods=['POST'])
def comment_answer(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return make_comment('answer', id, param['content'])


@app.route('/answer/<id>/comment', methods=['PUT'])
def edit_commentA(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return edit_comment('answer', id, param['content'])


@app.route('/answer/<id>/comment', methods=['DELETE'])
def delete_commentA(id):
	return delete_comment('answer', id)


@app.route('/question/<id>/comment')
def get_commentsQ(id):
	return get_comments('question', id)


@app.route('/question/<id>/comment', methods=['POST'])
def comment_question(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return make_comment('question', id, param['content'])


@app.route('/question/<id>/comment', methods=['PUT'])
def edit_commentQ(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return edit_comment('question', id, param['content'])


@app.route('/question/<id>/comment', methods=['DELETE'])
def delete_commentQ(id):
	return delete_comment('question', id)


@app.route('/course/<id>', methods=['DELETE'])
def delete_coursae(id):
	course = Course.query.filter_by( id = id).first()
	db_session.delete(course)
	commit()
	return ''

@app.route('/course', methods=['POST'])
@teacher.require(http_exception=401)
def create_course():
	user = User.query.filter_by( username = session['username']).first()
	param = request.json
	course = Course.query.filter_by( name = param['name']).first()
	if course:
		db_session.rollback()
		return json.dumps( {"flash": 'Course name already exists.'} )
	name = param['name']
	newCourse = Course(name)
	db_session.add(newCourse)
	db_session.commit()
	course = Course.query.filter_by( name = name ).first()
	table = Enrollment(user.id, course.id)
	db_session.add(table)
	retval = json.dumps({"id": newCourse.id, "name": newCourse.name})
	commit()
	return retval

@app.route('/course', methods=['GET'])
@student.require(http_exception=401)
def list_course():
	user = User.query.filter_by( username = session['username'] ).first()
	courses = Course.query.order_by( Course.name ).all()
	lst = []
	for course in courses:
		if user.usertype != 'Admin':
			query = Enrollment.query.filter_by(cid = course.id).filter_by(uid = user.id).first()
			if not query:
				continue
		lst.append( {"id": course.id, "name": course.name} )
	db_session.rollback()
	return json.dumps( {"courses": lst} )

@app.route('/question/<id>')
@student.require(http_exception=401)
def list_question(id):
	course = Course.query.filter_by(id = id).first()
	questions = Question.query.filter_by(cid = id).order_by( Question.time.desc() ).all()
	lst = []
	for question in questions:
		author = User.query.filter_by(id = question.uid).first()
		lst.append( {"id": question.id, "author": author.display, "time": str(question.time), "title": question.title, "content": question.content, "avatar": author.avatar} )
	db_session.rollback()
	return json.dumps( {"course": course.name, "questions": lst} )

@app.route('/question/<id>', methods=['POST'])
@student.require(http_exception=401)
def create_question(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'title': {'type': 'string'},
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	content = param['content']
	title = param['title']
	user = User.query.filter_by(username = session['username']).first()
	newQuestion = Question(id, user.id, title, content)
	db_session.add(newQuestion)
	db_session.commit()
	course = Course.query.filter_by(id = id).first()
	retval = json.dumps({"id": newQuestion.id, "author": user.display, "time": str(newQuestion.time), "title": newQuestion.title, "content": newQuestion.content, "avatar": user.avatar})
	db_session.rollback()
	return retval

@app.route('/question/<id>', methods=['DELETE'])
@student.require(http_exception=401)
def delete_question(id):
	question = Question.query.filter_by(id = id).first()
	user = User.query.filter_by(username = session['username']).first()
	if user.id != question.uid and user.usertype != 'Teacher' and user.usertype != 'Admin':
		retval = json.dumps( {"msg": user.display} )
		db_session.rollback()
		return retval
	db_session.delete(question)
	commit()
	return ''

@app.route('/enrollment/<cid>')
@teacher.require(http_exception=401)
def students_enrolled(cid):
	users = User.query.filter((User.usertype == 'Teacher') | (User.usertype == 'Student')).order_by( User.fullname ).all()
	studentlst = []
	teacherlst = []
	for user in users:
		print ('in loop, student: ' + str(user))
		enrolled = ''
		query = Enrollment.query.filter_by(uid = user.id).filter_by(cid = cid).first()
		print (query)
		if (query):
			print ('enrolled')
			enrolled = query.id
		if user.usertype == 'Student':
			studentlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled} )
		else:
			teacherlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled} )
	print ('student list: ' + str(studentlst))
	print ('teacher list: ' + str(teacherlst))
	course = Course.query.filter_by(id = cid).first()
	retval = json.dumps( { "course": course.name, "students": studentlst, "teachers": teacherlst } )
	db_session.rollback()
	return retval

@app.route('/enrollment/<cid>', methods=['POST'])
@teacher.require(http_exception=401)
def enroll_student(cid):
	param = request.json
	uid = param['uid']
	table = Enrollment(uid, cid)
	db_session.add(table)
	db_session.commit()
	query = Enrollment.query.filter_by(uid = uid).filter_by(cid = cid).first()
	retval = json.dumps( {"eid": query.id} )
	db_session.rollback()
	return retval

@app.route('/enrollment/<eid>', methods=['DELETE'])
@teacher.require(http_exception=401)
def drop_student(eid):
	query = Enrollment.query.filter_by( id = eid ).first()
	db_session.delete(query)
	commit()
	return json.dumps( {"msg": "PASS"} )

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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

@teacher.require(http_exception=401)
def import_users(list):
	schema = {
		'type': 'object',
		'properties': {
			'username': {'type': 'string'},
			'usertype': {'type': 'string', 'enum': ['Admin', 'Student', 'Teacher']},
			'password': {'type': 'string'},
			'email': {'type': 'string', 'format': 'email', 'required': False},
			'firstname': {'type': 'string'},
			'lastname': {'type': 'string'},
			'display': {'type': 'string'},
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
			error.append({'user': user, 'msg': str(err)})
		if user['username'] in duplicate:
			error.append({'user': user, 'msg': 'Duplicate username in file'})
			continue
		if user['username'] in usernames:
			u = User.query.filter_by( username = user['username'] ).first()
			if u.usertype == 'Student':
				user = {'id': u.id, 'username': u.username, 'password': 'hidden', 'usertype': 'Student',
					'email': u.email, 'firstname': u.firstname, 'lastname': u.lastname, 'display': u.display}
				duplicate.append(user['username'])
				success.append({'user': user})
			else : 
				error.append({'user': user, 'msg': 'User is not a student'})
			continue
		if user['display'] in displays:
			integer = random.randrange(1000, 9999)
			user['display'] = user['display'] + ' ' + str(integer)
		if 'email' in user:
			email = user['email']
			if not re.match(r"[^@]+@[^@]+", email):
				error.append({'user': user, 'msg': 'Incorrect email format'})
				continue
		else:
			email = ''
		table = User(user['username'], hasher.hash_password(user['password']), user['usertype'], email, user['firstname'], user['lastname'], user['display'])
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
def enrol_users(users, courseId):
	error = []
	success = []
	enrolled = Enrollment.query.filter_by(cid = courseId).with_entities(Enrollment.uid).all()
	enrolled =  [item for sublist in enrolled for item in sublist]
	for u in users:
		if u['user']['id'] in enrolled:
			success.append(u)
			continue
		table = Enrollment(u['user']['id'], courseId)
		db_session.add(table)
		status = commit()
		if status:
			success.append(u)
		else:
			u['msg'] = 'The user is created, but cannot be enrolled'
			error.append(u)
	return {'error': error, 'success': success}
	
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
	needs = []
	
	if identity.id in ('only_Student', 'only_Teacher', 'only_Admin'):
		needs.append(is_student)
	
	if identity.id in ('only_Teacher', 'only_Admin'):
		needs.append(is_teacher)
	
	if identity.id == 'only_Admin':
		needs.append(is_admin)
	
	for n in needs:
		identity.provides.add(n)

app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
