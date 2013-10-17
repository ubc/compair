from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session, jsonify, Response
from sqlalchemy_acj import init_db, reset_db, db_session, User, Judgement, Script, Course, Question, Enrollment, CommentA, CommentQ, CommentJ, Entry, Tags
from flask_principal import AnonymousIdentity, Identity, identity_changed, identity_loaded, Permission, Principal, RoleNeed #ActionNeed,
from sqlalchemy import desc, func#, select
from random import shuffle
from math import log10#, exp
from pw_hash import PasswordHash
#import exceptions
#import MySQLdb
import re
import json
import datetime
import validictory
import os
import time
import random
import time
from threading import Timer
from werkzeug import secure_filename
from flask.ext import sqlalchemy
import Image
import sys
from acj import app

'''
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
'''
#app = Flask(__name__)
init_db()
hasher = PasswordHash()
principals = Principal(app)

UPLOAD_FOLDER = 'tmp'
UPLOAD_IMAGE_FOLDER = 'acj/static/user_images'
ALLOWED_EXTENSIONS = set(['csv', 'txt'])
ALLOWED_IMAGE_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'gif', 'bmp'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_IMAGE_FOLDER'] = UPLOAD_IMAGE_FOLDER

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

#user activity
events = {}

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
			return obj.strftime("%F %r")
        return json.JSONEncoder.default(self, obj) 

def shutdown_server():
    if len(sys.argv) > 1 and str(sys.argv[1]) == '--t':
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
    
def commit():
    try:
        db_session.commit()
    except Exception, e:
        db_session.rollback()
        return False
    return True

@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()

@app.before_request
def registerOnline():
    global events
    if 'username' in session:
        if session['username'] in events:
            ev = events[session['username']]
            ev.cancel()
        ev = Timer(60.0, submitOnline, [session['username'], datetime.datetime.now()])
        events[str(session['username'])] = ev
        ev.start()

def submitOnline(name, time):
    user = User.query.filter_by(username = name).first()
    user.lastOnline = time
    commit()
        
@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

@app.route('/')
def index():
    return redirect(url_for('static', filename="index.html"))

@app.route('/isinstalled')
def is_installed():
	if os.access('tmp/installed.txt', os.F_OK):
		return json.dumps({'installed': True})
	return json.dumps({'installed': False})

@app.route('/install', methods=['GET'])
def install():
	requirements = []
	writable = True if os.access('tmp', os.W_OK) else False
	requirements.append( { 'text': 'tmp folder is writable', 'boolean': writable } )
	return json.dumps( {'requirements': requirements} )


@app.route('/login', methods=['GET'])
def logincheck():
    if 'username' in session:
        user = User.query.filter_by(username = session['username']).first()
        retval = json.dumps( {"id": user.id, "display": user.display, "usertype": user.usertype} )
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
        usertype = query.usertype
        display = User.query.filter_by(username = username).first().display
        db_session.rollback()
        identity = Identity('only_' + query.usertype)
        identity_changed.send(app, identity=identity)
        
        return json.dumps( {"display": display, "usertype": usertype} )
    db_session.rollback()
    return json.dumps( {"msg": 'Incorrect username or password'} )

@app.route('/logout')
def logout():
    if 'username' in session:
        if session['username'] in events:
            ev = events[session['username']]
            ev.cancel()
        submitOnline(session['username'], datetime.datetime.now())
        
	session.pop('username', None)
	for key in ['identity.name', 'identity.auth_type']:
		session.pop(key, None)
	identity_changed.send(app, identity=AnonymousIdentity())
	return json.dumps( {"status": 'logged out'} )

@app.route('/roles')
@teacher.require(http_exception=401)
def roles():
	query = User.query.filter_by(username = session['username']).first()
	roles = ['Student','Teacher']
	if query.usertype == 'Admin':
		roles.append('Admin')
	return json.dumps({'roles': roles})

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

'''
@app.route('/ranking')
@student.require(http_exception=401)
def total_ranking():
	scripts = Script.query.order_by( Script.score.desc() ).all()
	lst = []
	for script in scripts:
		question = Question.query.filter_by(id = script.qid).first()
		course = Course.query.filter_by(id = question.cid).first()
		author = User.query.filter_by(id = script.uid).first().display
		lst.append( {"course": course.name, "question": question.content, "author": author, "time": str(script.time), "content": script.content, "score": "{:10.2f}".format(script.score) } )
	db_session.rollback()
	return json.dumps( {"scripts": lst} )
'''
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_IMAGE_EXTENSIONS

@app.route('/notifications', methods=['GET'])
@student.require(http_exception=401)
def get_notifications():
    user = User.query.filter_by(username = session['username']).first()
    if user.lastOnline is not None:
        scripts = Script.query.join(Question, Script.qid == Question.id).filter(Question.uid == user.id).filter(Script.time > user.lastOnline).all()
        questions = []
        dummy = []
        for answer in scripts:
            if answer.qid not in dummy:
               questions.append({"qid": answer.qid, "title": answer.question.title})
               dummy.append(answer.qid)
        return json.dumps({"count": len(questions), "questions": questions})
    else:
        return json.dumps({"count": 0, "questions": {}})

@app.route('/uploadimage', methods=['POST'])
@student.require(http_exception=401)
def upload_image():
    file = request.files['file']
    if not file or not allowed_image_file(file.filename):
        return json.dumps( {"completed": True, "msg": "Please provide a valid image file"} )
    #throw exception if its not an image file
    try:
        img = Image.open(file)
    except IOError:
        return json.dumps( {"completed": True, "msg": "Invalid image file"} )    
    #scale the image if necessary
    if img.size[0] > 400 or img.size[1] > 400:
        neww = 0
        newh = 0
        rw = img.size[0] / 400
        rh = img.size[1] / 400
        
        if rw > rh:
            newh = int(round(img.size[1] / rw))
            neww = 400
        else:
            neww = int(round(img.size[0] / rh))
            newh = 400
        img = img.resize((neww,newh), Image.ANTIALIAS)
                        
    retval = []
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S")
    filename = timestamp + '-' + secure_filename(file.filename)
    if not os.path.exists(app.config['UPLOAD_IMAGE_FOLDER']):
        os.makedirs(app.config['UPLOAD_IMAGE_FOLDER'])
    img.save(os.path.join(app.config['UPLOAD_IMAGE_FOLDER'], filename))
    file.close()
    return json.dumps( {"file": filename, "completed": True} )

@app.route('/resetdb')
def resetdb():
    reset_db()
    return ''

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

#if __name__=='__main__':
	#app.run(debug=True)
	#app.run('0.0.0.0',8080)
