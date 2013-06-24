from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import db, User, Judgement, Script, CJ_Model, Score, Course, Question
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

@app.route('/login', methods=['GET'])
def logincheck():
	if 'username' in session:
		return json.dumps( {"username": session['username']} )
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
	if not query:
		return ''
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
	query[2:]
	shuffle( query )
	fresh = get_fresh_pair( query )
	if not fresh:
		print 'judged them all'
		return '' 
	print ('freshl: ' + str(fresh[0]))
	print ('freshr: ' + str(fresh[1]))
	return json.dumps( {"sidl": fresh[0], "sidr": fresh[1]} )

def get_fresh_pair( scripts ):
	uid = User.query.filter_by(username = session['username']).first().id
	index = 0
	for scriptl in scripts:
		index = index + 1
		print ('index: ' + str(index))
		print (scripts[index:])
		for scriptr in scripts[index:]:
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


@app.route('/score')
def estimate_score():
	scripts = Script.query.order_by( Script.id ).all()
	for scriptl in scripts:
		sidl = scriptl.id
		print ('sidl: ' + str(sidl))
		sigma = 0
		lwins = scriptl.wins
		for scriptr in scripts:
			if scriptl != scriptr:
				rwins = scriptr.wins
				print ('loop sidr: ' + str(scriptr.id))
				prob = lwins / (lwins + rwins)
				print ('prob: ' + str(prob))
				sigma = sigma + prob
				print ('sigma: ' + str(sigma))
		print ('out of inner loop')
		query = Script.query.filter_by(id = sidl).first()
		query.score = sigma
	db.session.commit()
	return '101010100010110'
		
@app.route('/ranking')
def marked_scripts():
	scripts = Script.query.order_by( Script.score.desc() ).all() 
	lst = []
	for script in scripts:
		lst.append( {"title": script.title, "author": script.author, "time": str(script.time), "content": script.content, "score":script.score } )
	print ('what is happneing')
	print ( lst )
	return json.dumps( {"scripts": lst} )

@app.route('/course', methods=['POST'])
def create_course():
	param = request.json
	name = param['name']
	table = Course(name)
	db.session.add(table)
	db.session.commit()
	return ''

@app.route('/course', methods=['GET'])
def list_course():
	courses = Course.query.order_by( Course.name ).all()
	lst = []
	for course in courses:
		lst.append( {"id": course.id, "name": course.name} )
	return json.dumps( {"courses": lst} )

@app.route('/question/<id>')
def list_question(id):
	course = Course.query.filter_by(id = id).first()
	questions = Question.query.filter_by(cid = id).all()
	lst = []
	for question in questions:
		lst.append( {"id": question.id, "content": question.content} )
	return json.dumps( {"course": course.name, "questions": lst} )

@app.route('/question/<id>', methods=['POST'])
def ask_question(id):
	param = request.json
	content = param['content']
	table = Question(id, content)
	db.session.add(table)
	db.session.commit()
	course = Course.query.filter_by(id = id).first()
	return json.dumps( {"course": course.name} )



app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
