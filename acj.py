from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import db, User, Judgement, Script
from sqlalchemy import desc, func, select
from random import shuffle
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

@app.route('/script/<id>', methods=['', 'POST'])
def mark_script(id):
	query = Script.query.filter_by(id = id).first()
	if not query:
		return json.dumps({"msg": "No matching script"})
	query.score = query.score + 1
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

@app.route('/judgement/<id>')
def check_judge(id):
	query = User.query.filter_by(username = session['username']).first()
	query = Judgement.query.filter_by(uid = query.id).first()
	if not query:
		return json.dumps( {"msg": 'No matching judgement'} )
	ret_val = json.dumps( {"sidl": query.sidl, "sidr": query.sidr} )
	return ret_val

@app.route('/user', methods=['POST'])
def create_user():
	param = request.json
	username = param['username']
	query = User.query.filter_by(username = username).first()
	if query:
		return json.dumps( {"msg": 'Username already exists'} )
	password = param['password']
	password = hasher.hash_password( password )
	table = User(username, password)
	db.session.add(table)
	db.session.commit()
	session['username'] = username
	return ''

@app.route('/pickscript', methods=['GET'])
def pick_script():
	query = Script.query.order_by( Script.count.desc() ).first()
	max = query.count
	query = Script.query.order_by( Script.count ).first()
	min = query.count
	print ('max: ' + str(max))
	print ('min: ' + str(min))
	if max == min:
		max = max + 1 
	query = Script.query.filter(Script.count < max).order_by( Script.count ).limit(10).all()
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

app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
