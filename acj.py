from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import db_session, User, Judgement, Script, CJ_Model, Score, Course, Question, Enrollment
from sqlalchemy import desc, func, select
from random import shuffle
from math import log10, exp
import exceptions
import MySQLdb
import re
import phpass
import json


app = Flask(__name__)

hasher = phpass.PasswordHash()

def commit():
	try:
		db_session.commit()
	finally:
		db_session.rollback()

@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()

@app.route('/')
def index():
	return redirect(url_for('static', filename="index.html"))

@app.route('/script/<id>', methods=['GET'])
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
def post_answer(id):
	param = request.json
	qid = id
	author = session['username']
	content = param['content']
	table = Script(qid, author, content)
	db_session.add(table)
	db_session.commit()
	script = Script.query.order_by( Script.time.desc() ).first()
	retval = json.dumps({"id": script.id, "author": script.author, "time": str(script.time), "content": script.content, "score":script.score})
	db_session.rollback()
	return retval

@app.route('/answer/<id>', methods=['PUT'])
def edit_answer(id):
	param = request.json
	script = Script.query.filter_by(id = id).first()
	script.content = param['content']
	commit()
	return json.dumps({"msg": "PASS"})

@app.route('/answer/<id>', methods=['DELETE'])
def delete_answer(id):
	script = Script.query.filter_by(id = id).first()
	db_session.delete(script)
	commit()
	return json.dumps({"msg": "PASS"})

@app.route('/login', methods=['GET'])
def logincheck():
	if 'username' in session:
		user = User.query.filter_by(username = session['username']).first()
		retval = json.dumps( {"username": session['username'], "usertype": user.usertype} )
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
		db_session.rollback()
		return ''
	db.dession.rollback()
	return json.dumps( {"msg": 'Incorrect username or password'} )

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))

@app.route('/user', methods=['POST'])
def create_user():
	param = request.json
	username = param['username']
	query = User.query.filter_by(username = username).first()
	if query:
		db_session.rollback()
		return json.dumps( {"msg": 'Username already exists'} )
	password = param['password']
	password = hasher.hash_password( password )
	usertype = param['usertype']
	table = User(username, password, usertype)
	db_session.add(table)
	commit()
	session['username'] = username
	return ''

@app.route('/pickscript/<id>', methods=['GET'])
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
	retval = json.dumps( {"course": course.name, "question": question.content, "sidl": fresh[0], "sidr": fresh[1]} )
	db_session.rollback()
	return retval

def get_fresh_pair( scripts ):
	uid = User.query.filter_by(username = session['username']).first().id
	index = 0
	for scriptl in scripts:
		index = index + 1
		print ('index: ' + str(index))
		print (scripts[index:])
		if session['username'] != scriptl.author:
			for scriptr in scripts[index:]:
				if session['username'] != scriptr.author:
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
def random_question():
	script = Script.query.order_by( Script.count ).first()
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
def marked_scripts(id):
	estimate_score(id)
	scripts = Script.query.filter_by(qid = id).order_by( Script.score.desc() ).all() 
	lst = []
	for script in scripts:
		lst.append( {"id": script.id, "title": script.title, "author": script.author, "time": str(script.time), "content": script.content, "score":script.score } )
	print ('what is happneing')
	print ( lst )
	question = Question.query.filter_by(id = id).first()
	course = Course.query.filter_by(id = question.cid).first()
	user = User.query.filter_by(username = session['username']).first()
	retval = json.dumps( {"username": session['username'], "usertype": user.usertype, "course": course.name, "question": question.content, "scripts": lst} )
	db_session.rollback()
	return retval

@app.route('/ranking')
def total_ranking():
	scripts = Script.query.order_by( Script.score.desc() ).all()
	lst = []
	for script in scripts:
		question = Question.query.filter_by(id = script.qid).first()
		course = Course.query.filter_by(id = question.cid).first()
		lst.append( {"course": course.name, "question": question.content, "author":script.author, "time": str(script.time), "content": script.content, "score": script.score } )
	db_session.rollback()
	return json.dumps( {"scripts": lst} )

@app.route('/course', methods=['POST'])
def create_course():
	user = User.query.filter_by( username = session['username']).first()
	param = request.json
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
def list_question(id):
	course = Course.query.filter_by(id = id).first()
	questions = Question.query.filter_by(cid = id).order_by( Question.time.desc() ).all()
	lst = []
	for question in questions:
		lst.append( {"id": question.id, "author": question.author, "time": str(question.time), "title": question.title, "content": question.content} )
	db_session.rollback()
	return json.dumps( {"course": course.name, "questions": lst} )

@app.route('/question/<id>', methods=['POST'])
def create_question(id):
	param = request.json
	content = param['content']
	newQuestion = Question(id, session['username'], content)
	db_session.add(newQuestion)
	db_session.commit()
	course = Course.query.filter_by(id = id).first()
	retval = json.dumps({"id": newQuestion.id, "author": newQuestion.author, "time": str(newQuestion.time), "content": newQuestion.content})
	db_session.rollback()
	return retval

@app.route('/question/<id>', methods=['DELETE'])
def delete_question(id):
	question = Question.query.filter_by(id = id).first()
	user = User.query.filter_by(username = session['username']).first()
	if session['username'] != question.author and user.usertype != 'Teacher':
		retval = json.dumps( {"msg": question.author} )
		db_session.rollback()
		return retval
	db_session.delete(question)
	commit()
	return ''

@app.route('/enrollment/<cid>')
def students_enrolled(cid):
	users = User.query.filter((User.usertype == 'Teacher') | (User.usertype == 'Student')).order_by( User.username ).all()
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
			studentlst.append( {"uid": user.id, "username": user.username, "enrolled": enrolled} )
		else:
			teacherlst.append( {"uid": user.id, "username": user.username, "enrolled": enrolled} )
	print ('student list: ' + str(studentlst))
	print ('teacher list: ' + str(teacherlst))
	course = Course.query.filter_by(id = cid).first()
	retval = json.dumps( { "course": course.name, "students": studentlst, "teachers": teacherlst } )
	db_session.rollback()
	return retval

@app.route('/enrollment/<cid>', methods=['POST'])
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
def drop_student(eid):
	query = Enrollment.query.filter_by( id = eid ).first()
	db_session.delete(query)
	commit()
	return json.dumps( {"msg": "PASS"} )
	




app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
