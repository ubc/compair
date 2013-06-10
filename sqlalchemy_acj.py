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
	#judgements = db.Column(postgresql.ARRAY(db.Integer), unique=False)
	judgement = db.relationship('Judgement')

	def __init__(self, username, password):
		self.username = username
		self.password = password

	def __repr__(self):
		return '<Judge %r>' % self.username

class Script(db.Model):
	__tablename__ = 'Script'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80), unique=False)
	author = db.Column(db.String(80), unique=False)
	time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	content = db.Column(db.Text, unique=False)
	score = db.Column(db.Integer, unique=False)

	def __init__(self, title, author, content, score):
		self.title = title
		self.author = author
		self.content = content
		self.score = score

	def __repr__(self):
		return '<Script %r>' % self.title

class Judgement(db.Model):
	__tablename__ = 'Judgement'
	id = db.Column(db.Integer, primary_key=True)
	uid = db.Column(db.Integer, db.ForeignKey('User.id'))
	sidl= db.Column(db.Integer, db.ForeignKey('Script.id'))
	sidr = db.Column(db.Integer, db.ForeignKey('Script.id'))

	script1 = db.relationship('Script', foreign_keys=[sidl])
	script2 = db.relationship('Script', foreign_keys=[sidr])

	def __init__(self, uid, sidl, sidr):
		self.uid = uid
		self.sidl = sidl
		self.sidr = sidr

	def __repr__(self):
		return '<Judgement %r>' % self.id
