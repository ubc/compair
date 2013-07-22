from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import backref, scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

engine = create_engine('mysql://testuser:testpw@localhost/acj', convert_unicode=True, pool_recycle=300)
db_session = scoped_session(sessionmaker (autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
Base.metadata.create_all(bind=engine)

def init_db():
	Base.metadata.create_all(bind=engine)

class User(Base):
	__tablename__ = 'User'
	id = Column(Integer, primary_key=True)
	username = Column(String(80), unique=True)
	password = Column(String(120), unique=False)
	usertype = Column(Enum('Admin', 'Teacher', 'Student'))
	judgement = relationship('Judgement', cascade="all,delete")
	enrollment = relationship('Enrollment', cascade="all,delete")

	def __init__(self, username, password, usertype):
		self.username = username
		self.password = password
		self.usertype = usertype

	def __repr__(self):
		return '<User %r>' % self.username

class Course(Base):
	__tablename__ = 'Course'
	id = Column(Integer, primary_key=True)
	name = Column(String(80), unique=True)
	question = relationship('Question', cascade="all,delete")
	enrollment = relationship('Enrollment', cascade="all,delete")

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Course %r>' % self.name

class Question(Base):
	__tablename__ = 'Question'
	id = Column(Integer, primary_key=True)
	cid = Column(Integer, ForeignKey('Course.id', ondelete='CASCADE'))
	author = Column(String(80), default='anonym')
	time = Column(DateTime, default=datetime.datetime.utcnow)
	title = Column(String(80))
	content = Column(Text)
	script = relationship('Script', cascade="all,delete")

	def __init__(self, cid, author, title, content):
		self.cid = cid
		self.author = author
		self.title = title
		self.content = content

	def __repr__(self):
		return '<Question %r>' % self.id

class Script(Base):
	__tablename__ = 'Script'
	id = Column(Integer, primary_key=True)
	qid = Column(Integer, ForeignKey('Question.id', ondelete='CASCADE'))
	title = Column(String(80), default='answer')
	author = Column(String(80), unique=False)
	time = Column(DateTime, default=datetime.datetime.utcnow)
	content = Column(Text, unique=False)
	wins = Column(Integer, default=0)
	count = Column(Integer, default=0)
	score = Column(Float, default=0)

	def __init__(self, qid, author, content):
		self.qid = qid
		self.author = author
		self.content = content

	def __repr__(self):
		return '<Script %r>' % self.id

class Judgement(Base):
	__tablename__ = 'Judgement'
	id = Column(Integer, primary_key=True)
	uid = Column(Integer, ForeignKey('User.id', ondelete='CASCADE'))
	sidl= Column(Integer, ForeignKey('Script.id', ondelete='CASCADE'))
	sidr = Column(Integer, ForeignKey('Script.id', ondelete='CASCADE'))
	winner = Column(Integer, unique=False)

	script1 = relationship('Script', foreign_keys=[sidl], backref=backref("judge1", cascade="all,delete"))
	script2 = relationship('Script', foreign_keys=[sidr], backref=backref("judge2", cascade="all,delete"))

	def __init__(self, uid, sidl, sidr, winner):
		self.uid = uid
		self.sidl = sidl
		self.sidr = sidr
		self.winner = winner

	def __repr__(self):
		return '<Judgement %r>' % self.id

class CJ_Model(Base):
	__tablename__ = 'CJ_Model'
	id = Column(Integer, primary_key=True)
	sidl = Column(Integer, ForeignKey('Script.id'))
	sidr = Column(Integer, ForeignKey('Script.id'))
	diff = Column(Float, unique=False)

	scriptl = relationship('Script', foreign_keys=[sidl])
	scriptr = relationship('Script', foreign_keys=[sidr])

	def __init__(self, sidl, sidr, diff):
		self.sidl = sidl
		self.sidr = sidr
		self.diff = diff

	def __repr__(self):
		return '<CJ_Model %r>' % self.id

class Score(Base):
	__tablename__ = 'Score'
	id = Column(Integer, primary_key=True)
	sid = Column(Integer, ForeignKey('Script.id'))
	score = Column(Float, unique=False)

	script = relationship('Script')

	def __init__(self, sid, score):
		self.sid = sid
		self.score = score

	def __repr__(self):
		return '<Score %r>' % self.sid

class Enrollment(Base):
	__tablename__ = 'Enrollment'
	id = Column(Integer, primary_key=True)
	uid = Column(Integer, ForeignKey('User.id', ondelete='CASCADE'))
	cid = Column(Integer, ForeignKey('Course.id', ondelete='CASCADE'))

	def __init__(self, uid, cid):
		self.uid = uid
		self.cid = cid

	def __repr__(self):
		return '<Enrollment %r>' % self.id
