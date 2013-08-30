from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import backref, scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.engine.url import URL
import datetime
import hashlib
import settings

engine = create_engine(URL(**settings.DATABASE), convert_unicode=True, pool_recycle=300)
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
	email = Column(String(254))
	firstname = Column(String(254))
	lastname = Column(String(254))
	display = Column(String(254), unique=True)

	judgement = relationship('Judgement', cascade="all,delete")
	enrollment = relationship('Enrollment', cascade="all,delete")

	def __init__(self, username, password, usertype, email, firstname, lastname, display):
		self.username = username
		self.password = password
		self.usertype = usertype
		self.email = email
		self.firstname = firstname
		self.lastname = lastname
		self.display = display

	def __repr__(self):
		return '<User %r>' % self.username

	@hybrid_property
	def fullname(self):
		return self.firstname + ' ' + self.lastname

	@hybrid_property
	def avatar(self):
		m = hashlib.md5()
		m.update(self.email)
		return m.hexdigest()

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

class Entry(Base):
	__tablename__ = 'Entry'
	id = Column(Integer, primary_key=True)
	uid = Column(Integer, ForeignKey('User.id', ondelete='CASCADE'))
	type = Column(String(50))
	time = Column(DateTime, default=datetime.datetime.utcnow)
	content = Column(Text)

	__mapper_args__ = {
		'polymorphic_identity': 'Entry',
		'polymorphic_on': type
	}

	def __init__(self, uid, content):
		self.uid = uid
		self.content = content
	
	def __repr__(self):
		return '<Entry %r>' % self.id

class Question(Entry):
	__tablename__ = 'Question'
	id = Column(Integer, ForeignKey('Entry.id', ondelete='CASCADE'), primary_key=True)
	cid = Column(Integer, ForeignKey('Course.id', ondelete='CASCADE'))
	title = Column(String(255))

	__mapper_args__ = {
		'polymorphic_identity': 'Question',
	}

	def __init__(self, cid, uid, title, content):
		self.cid = cid
		self.uid = uid 
		self.title = title
		self.content = content

	def __repr__(self):
		return '<Question %r>' % self.id

class Script(Entry):
	__tablename__ = 'Script'
	id = Column(Integer, ForeignKey('Entry.id', ondelete="CASCADE"), primary_key=True)
	qid = Column(Integer, ForeignKey('Question.id', ondelete='CASCADE'))
	title = Column(String(80), default='answer')
	wins = Column(Integer, default=0)
	count = Column(Integer, default=0)
	score = Column(Float, default=0)

	question = relationship('Question', foreign_keys=[qid], backref=backref('Script', cascade="all,delete"))

	__mapper_args__ = {
		'polymorphic_identity': 'Script',
	}

	def __init__(self, qid, uid, content):
		self.qid = qid
		self.uid = uid 
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

class CommentA(Entry):
	__tablename__ = 'CommentA'
	id = Column(Integer, ForeignKey('Entry.id', ondelete='CASCADE'), primary_key=True)
	sid = Column(Integer, ForeignKey('Script.id', ondelete='CASCADE'))

	script = relationship('Script', foreign_keys=[sid], backref=backref('CommentA', cascade="all,delete"))

	__mapper_args__ = {
		'polymorphic_identity': 'CommentA',
	}

	def __init__(self, sid, uid, content):
		self.sid = sid
		self.uid = uid 
		self.content = content

	def __repr__(self):
		return '<CommentA %r>' % self.id

class CommentQ(Entry):
	__tablename__ = 'CommentQ'
	id = Column(Integer, ForeignKey('Entry.id', ondelete='CASCADE'), primary_key=True)
	qid = Column(Integer, ForeignKey('Question.id', ondelete='CASCADE'))

	question = relationship('Question', foreign_keys=[qid], backref=backref('CommentQ', cascade="all,delete"))

	__mapper_args__ = {
		'polymorphic_identity': 'CommentQ',
	}
	
	def __init__(self, qid, uid, content):
		self.qid = qid
		self.uid = uid 
		self.content = content

	def __repr__(self):
		return '<CommentQ %r>' % self.id
