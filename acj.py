from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import db, User, Judgement, Script, CJ_Model, Score, Course, Question, Enrollment
from sqlalchemy import desc, func, select
from random import shuffle
from math import log10, exp
import exceptions
import MySQLdb
import re
import phpass
import json


app = Flask(__name__)

db.create_all()

hasher = phpass.PasswordHash()

@app.route('/')
def index():
	return redirect(url_for('static', filename="index.html"))

@app.route('/script/<id>', methods=['GET'])
def get_script(id):
	print(id)
	query = Script.query.filter_by(id = id).first()
	if not query:
		return json.dumps({"msg": "No matching script"})
	ret_val = json.dumps( {"content": query.content} )
	return ret_val

@app.route('/script/<id>', methods=['POST'])
def mark_script(id):
	query = Script.query.filter_by(id = id).first()
	if not query:
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
	db.session.add(table)
	db.session.commit()
	return json.dumps({"msg": "Script & Judgement updated"})

@app.route('/answer/<id>', methods=['POST'])
def post_answer(id):
	param = request.json
	qid = id
	author = session['username']
	content = param['content']
	table = Script(qid, author, content)
	db.session.add(table)
	db.session.commit()
	script = Script.query.order_by( Script.time.desc() ).first()
	return json.dumps({"id": script.id, "author": script.author, "time": str(script.time), "content": script.content, "score":script.score})

@app.route('/answer/<id>', methods=['PUT'])
def edit_answer(id):
	param = request.json
	script = Script.query.filter_by(id = id).first()
	script.content = param['content']
	db.session.commit()
	return json.dumps({"msg": "PASS"})

@app.route('/answer/<id>', methods=['DELETE'])
def delete_answer(id):
	script = Script.query.filter_by(id = id).first()
	db.session.delete(script)
	db.session.commit()
	return json.dumps({"msg": "PASS"})

@app.route('/login', methods=['GET'])
def logincheck():
	if 'username' in session:
		user = User.query.filter_by(username = session['username']).first()
		return json.dumps( {"username": session['username'], "usertype": user.usertype} )
	return ''

@app.route('/login', methods=['POST'])
def login():
	param = request.json
	username = param['username']
	password = param['password']
	query = User.query.filter_by(username = username).first()
	if not query:
		return json.dumps( {"msg": 'Incorrect username or password'} )
	hx = query.password
	if hasher.check_password( password, hx ):
		session['username'] = username
		return ''
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
		return json.dumps( {"msg": 'Username already exists'} )
	password = param['password']
	password = hasher.hash_password( password )
	usertype = param['usertype']
	table = User(username, password, usertype)
	db.session.add(table)
	db.session.commit()
	session['username'] = username
	return ''

@app.route('/pickscript/<id>', methods=['GET'])
def pick_script(id):
	query = Script.query.filter_by(qid = id).order_by( Script.count.desc() ).first()
	question = Question.query.filter_by(id = id).first()
	course = Course.query.filter_by(id = question.cid).first()
	if not query:
		return json.dumps( {"course": course.name, "question": question.content} )
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
		return json.dumps( {"question": question.content} ) 
	print ('freshl: ' + str(fresh[0]))
	print ('freshr: ' + str(fresh[1]))
	return json.dumps( {"course": course.name, "question": question.content, "sidl": fresh[0], "sidr": fresh[1]} )

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
						return [sidl, sidr]
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
				return json.dumps( {"question": qid} )
	print ('RETURN: SOMETHING IS NOT RIGHT')
	return ''

@app.route('/temp')
def temp():
	return Script.query(columns[qid, wins]).filter_by(count = 0).all()

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
				db.session.add(table)
	db.session.commit()
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
	db.session.commit()
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
	user = User.query.filter_by(username = session['username']).first()
	return json.dumps( {"username": session['username'], "usertype": user.usertype, "question": question.content, "scripts": lst} )

@app.route('/ranking')
def total_ranking():
	scripts = Script.query.order_by( Script.score.desc() ).all()
	lst = []
	for script in scripts:
		question = Question.query.filter_by(id = script.qid).first()
		course = Course.query.filter_by(id = question.cid).first()
		lst.append( {"course": course.name, "question": question.content, "author":script.author, "time": str(script.time), "content": script.content, "score": script.score } )
	return json.dumps( {"scripts": lst} )

@app.route('/course', methods=['POST'])
def create_course():
	user = User.query.filter_by( username = session['username']).first()
	param = request.json
	name = param['name']
	newCourse = Course(name)
	db.session.add(newCourse)
	db.session.commit()
	course = Course.query.filter_by( name = name ).first()
	table = Enrollment(user.id, course.id)
	db.session.add(table)
	db.session.commit()
	return json.dumps({"id": newCourse.id, "name": newCourse.name})

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
	return json.dumps( {"courses": lst} )

@app.route('/question/<id>')
def list_question(id):
	course = Course.query.filter_by(id = id).first()
	questions = Question.query.filter_by(cid = id).order_by( Question.time.desc() ).all()
	lst = []
	for question in questions:
		lst.append( {"id": question.id, "author": question.author, "time": str(question.time), "content": question.content} )
	return json.dumps( {"course": course.name, "questions": lst} )

@app.route('/question/<id>', methods=['POST'])
def create_question(id):
	param = request.json
	content = param['content']
	newQuestion = Question(id, session['username'], content)
	db.session.add(newQuestion)
	db.session.commit()
	course = Course.query.filter_by(id = id).first()
	
	return json.dumps({"id": newQuestion.id, "author": newQuestion.author, "time": str(newQuestion.time), "content": newQuestion.content});

@app.route('/question/<id>', methods=['DELETE'])
def delete_question(id):
	question = Question.query.filter_by(id = id).first()
	user = User.query.filter_by(username = session['username']).first()
	if session['username'] != question.author and user.usertype != 'Teacher':
		return json.dumps( {"msg": question.author} )
	db.session.delete(question)
	db.session.commit()
	return ''

@app.route('/enrollment/<id>')
def students_enrolled(id):
	users = User.query.filter((User.usertype == 'Teacher') | (User.usertype == 'Student')).order_by( User.username ).all()
	studentlst = []
	teacherlst = []
	for user in users:
		print ('in loop, student: ' + str(user))
		enrolled = ''
		query = Enrollment.query.filter_by(uid = user.id).filter_by(cid = id).first()
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
	course = Course.query.filter_by(id = id).first()
	return json.dumps( { "course": course.name, "students": studentlst, "teachers": teacherlst } )

@app.route('/enrollment/<id>', methods=['POST'])
def enroll_student(id):
	param = request.json
	sid = param['sid']
	table = Enrollment(sid, id)
	db.session.add(table)
	db.session.commit()
	return ''

@app.route('/enrollment/<id>', methods=['DELETE'])
def drop_student(id):
	query = Enrollment.query.filter_by( id = id ).first()
	db.session.delete(query)
	db.session.commit()
	return ''
	




app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
