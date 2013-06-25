from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy 
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://testuser:testpw@localhost/acj'
db = SQLAlchemy(app)

class User(db.Model):
	__tablename__ = 'User'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True)
	password = db.Column(db.String(120), unique=False)
	usertype = db.Column(db.Enum('Teacher', 'Student'))
	#judgements = db.Column(postgresql.ARRAY(db.Integer), unique=False)
	judgement = db.relationship('Judgement', passive_deletes=True)

	def __init__(self, username, password, usertype):
		self.username = username
		self.password = password
		self.usertype = usertype

	def __repr__(self):
		return '<User %r>' % self.username

class Course(db.Model):
	__tablename__ = 'Course'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True)
	question = db.relationship('Question', passive_deletes=True)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Course %r>' % self.name

class Question(db.Model):
	__tablename__ = 'Question'
	id = db.Column(db.Integer, primary_key=True)
	cid = db.Column(db.Integer, db.ForeignKey('Course.id', ondelete='CASCADE'))
	time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	content = db.Column(db.Text)
	script = db.relationship('Script', passive_deletes=True)

	def __init__(self, cid, content):
		self.cid = cid
		self.content = content

	def __repr__(self):
		return '<Question %r>' % self.id

class Script(db.Model):
	__tablename__ = 'Script'
	id = db.Column(db.Integer, primary_key=True)
	qid = db.Column(db.Integer, db.ForeignKey('Question.id', ondelete='CASCADE'))
	title = db.Column(db.String(80), default='answer')
	author = db.Column(db.String(80), unique=False)
	time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	content = db.Column(db.Text, unique=False)
	wins = db.Column(db.Integer, default=0)
	count = db.Column(db.Integer, default=0)
	score = db.Column(db.Float, default=0)

	def __init__(self, qid, author, content):
		self.qid = qid
		self.author = author
		self.content = content

	def __repr__(self):
		return '<Script %r>' % self.id

class Judgement(db.Model):
	__tablename__ = 'Judgement'
	id = db.Column(db.Integer, primary_key=True)
	uid = db.Column(db.Integer, db.ForeignKey('User.id', ondelete='CASCADE'))
	sidl= db.Column(db.Integer, db.ForeignKey('Script.id', ondelete='CASCADE'))
	sidr = db.Column(db.Integer, db.ForeignKey('Script.id', ondelete='CASCADE'))
	winner = db.Column(db.Integer, unique=False)

	script1 = db.relationship('Script', foreign_keys=[sidl], passive_deletes=True)
	script2 = db.relationship('Script', foreign_keys=[sidr], passive_deletes=True)

	def __init__(self, uid, sidl, sidr, winner):
		self.uid = uid
		self.sidl = sidl
		self.sidr = sidr
		self.winner = winner

	def __repr__(self):
		return '<Judgement %r>' % self.id

class CJ_Model(db.Model):
	__tablename__ = 'CJ_Model'
	id = db.Column(db.Integer, primary_key=True)
	sidl = db.Column(db.Integer, db.ForeignKey('Script.id'))
	sidr = db.Column(db.Integer, db.ForeignKey('Script.id'))
	diff = db.Column(db.Float, unique=False)

	scriptl = db.relationship('Script', foreign_keys=[sidl])
	scriptr = db.relationship('Script', foreign_keys=[sidr])

	def __init__(self, sidl, sidr, diff):
		self.sidl = sidl
		self.sidr = sidr
		self.diff = diff

	def __repr__(self):
		return '<CJ_Model %r>' % self.id

class Score(db.Model):
	__tablename__ = 'Score'
	id = db.Column(db.Integer, primary_key=True)
	sid = db.Column(db.Integer, db.ForeignKey('Script.id'))
	score = db.Column(db.Float, unique=False)

	script = db.relationship('Script')

	def __init__(self, sid, score):
		self.sid = sid
		self.score = score

	def __repr__(self):
		return '<Score %r>' % self.sid
