## Template for creating a new table. Note, the first 3 are taken care of by
## the default_table_args defined in database.py.
## * If MySQL, table engine must be InnoDB, for native foreign key support.
## * The default character set must be utf8, cause utf8 everywhere makes
##	 text encodings much easier to deal with.
## * Collation is using the slightly slower utf8_unicode_ci due to it's better
##	 conformance to human expectations for sorting. 
## * There must always be a primary key id field. 
## * creation_time and modification_time fields are self updating, they're nice
##	 to have for troubleshooting, but not all tables need them.
## * Additional fields given are meant for reference only. 
## * Foreign keys must be named in the format of <tablename>_id for
##	 consistency. 
## * 'ON DELETE CASCADE' is the preferred resolution method so that we don't
##	 have to worry about database consistency as much.
## * Junction tables names must be the two table's names, connected by
##	 "And".
## * Some tables might have subcategories, use the word "For" to indicated the
##	 subcategory, e.g.: we have a "Posts" table for all posts and a 
##	 "PostsForQuestions" table for posts that are meant to be questions

import logging
import hashlib

from sqlalchemy import Boolean, Column, DateTime, event, Float, ForeignKey, Integer, String, Text, TIMESTAMP, \
	UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

#  import the context under an app-specific name (so it can easily be replaced later)
from passlib.apps import custom_app_context as pwd_context

from flask.ext.login import UserMixin

from acj.database import Base, db_session, default_table_args

logger = logging.getLogger(__name__)

#################################################
# Users
#################################################

# User types at the course level
class UserTypesForCourse(Base):
	__tablename__ = "UserTypesForCourse"
	__table_args__ = default_table_args

	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)

	# constants for the user types
	TYPE_DROPPED = "Dropped"
	TYPE_STUDENT = "Student"
	TYPE_TA = "Teaching Assistant"
	TYPE_INSTRUCTOR = "Instructor"


# initialize the database with preloaded data using the event system
@event.listens_for(UserTypesForCourse.__table__, "after_create", propagate=True)
def populate_usertypesforcourse(target, connection, **kw):
	usertypes = [
		UserTypesForCourse.TYPE_DROPPED,
		UserTypesForCourse.TYPE_STUDENT,
		UserTypesForCourse.TYPE_TA,
		UserTypesForCourse.TYPE_INSTRUCTOR
	]
	for usertype in usertypes:
		entry = UserTypesForCourse(name=usertype)
		db_session.add(entry)
	db_session.commit()


# User types at the system level
class UserTypesForSystem(Base):
	__tablename__ = "UserTypesForSystem"
	__table_args__ = default_table_args

	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)

	TYPE_NORMAL = "Normal User"
	TYPE_SYSADMIN = "System Administrator"


@event.listens_for(UserTypesForSystem.__table__, "after_create", propagate=True)
def populate_usertypesforsystem(target, connection, **kw):
	usertypes = [UserTypesForSystem.TYPE_NORMAL,
				 UserTypesForSystem.TYPE_SYSADMIN]
	for usertype in usertypes:
		entry = UserTypesForSystem(name=usertype)
		db_session.add(entry)
	db_session.commit()


# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class Users(Base, UserMixin):
	__tablename__ = 'Users'
	__table_args__ = default_table_args

	id = Column(Integer, primary_key=True, nullable=False)
	username = Column(String(255), unique=True, nullable=False)
	password = Column(String(255), unique=False, nullable=False)

	# Apparently, enabling the equivalent of ON DELETE CASCADE requires
	# the ondelete option in the foreign key and the cascade + passive_deletes
	# option in relationship().
	usertypesforsystem_id = Column(
		Integer,
		ForeignKey('UserTypesForSystem.id', ondelete="CASCADE"),
		nullable=False)
	usertypeforsystem = relationship("UserTypesForSystem")

	email = Column(String(254))  # email addresses are max 254 characters, no
	# idea if the unicode encoding of email addr
	# changes this.
	firstname = Column(String(255))
	lastname = Column(String(255))
	displayname = Column(String(255), unique=True)
	lastonline = Column(DateTime)
	# Note that MySQL before 5.6.5 doesn't allow more than one auto init/update
	# column for timestamps! Auto init/update after 5.6.5 allows multiple 
	# columns and can be applied to the DateTime field as well. This means that
	# 'modified' can be counted on to be auto init/updated for manual
	# (non-SQLAlchemy) database operations while 'created' will not.
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)
	coursesandusers = relationship("CoursesAndUsers")

	@hybrid_property
	def fullname(self):
		if self.firstname and self.lastname:
			return '%s %s' % (self.firstname, self.lastname)
		elif self.firstname:  # only first name provided
			return self.firstname
		elif self.lastname:  # only last name provided
			return self.lastname
		else:
			return None

	# Note that in order for avatar to be provided with Flask-Restless, it can't
	# be a hybrid_property due to self.email not being resolved yet when
	# Flask-Restless tries to use it.
	# According to gravatar's hash specs
	# 	1.Trim leading and trailing whitespace from an email address
	# 	2.Force all characters to lower-case
	# 	3.md5 hash the final string
	def avatar(self):
		if self.email:
			m = hashlib.md5()
			m.update(self.email.strip().lower())
			return m.hexdigest()
		else:
			return None

	def set_password(self, password, is_admin=False):
		category = None
		if is_admin:
			# enables more rounds for admin passwords
			category = "admin"
		self.password = pwd_context.encrypt(password, category=category)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password)

	def update_lastonline(self):
		logger.debug("Update Last Online");
		self.lastonline = func.current_timestamp()
		db_session.add(self)
		db_session.commit()


# create a default root user with sysadmin role
@event.listens_for(Users.__table__, "after_create", propagate=True)
def populate_users(target, connection, **kw):
	sysadmintype = UserTypesForSystem.query.filter(
		UserTypesForSystem.name == UserTypesForSystem.TYPE_SYSADMIN).first()
	user = Users(username="root", displayname="root")
	user.set_password("password", True)
	user.usertypeforsystem = sysadmintype
	db_session.add(user)
	db_session.commit()


#################################################
# Courses and Enrolment
#################################################

class Courses(Base):
	__tablename__ = 'Courses'
	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)
	description = Column(Text)
	available = Column(Boolean, default=True, nullable=False)
	coursesandusers = relationship("CoursesAndUsers")
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)

# A "junction table" in sqlalchemy is called a many-to-many pattern. Such a
# table can be automatically created by sqlalchemy from relationship
# definitions along. But if additional fields are needed, then we can
# explicitly define such a table using the "association object" pattern.
# For determining a course's users, we're using the association object approach
# since we need to declare the user's role in the course.
class CoursesAndUsers(Base):
	__tablename__ = 'CoursesAndUsers'
	id = Column(Integer, primary_key=True, nullable=False)
	courses_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)
	course = relationship("Courses")
	users_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
	user = relationship("Users")
	usertypesforcourse_id = Column(
		Integer,
		ForeignKey('UserTypesForCourse.id', ondelete="CASCADE"),
		nullable=False)
	usertypeforcourse = relationship("UserTypesForCourse")
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)
	__table_args__ = (
		# prevent duplicate user in courses
		UniqueConstraint('courses_id', 'users_id', name='_unique_user_and_course'),
	)


#################################################
# Tags for Posts, each course has their own set of tags
#################################################

class Tags(Base):
	__tablename__ = 'Tags'
	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)
	courses_id = Column(
		Integer,
		ForeignKey('Courses.id', ondelete="CASCADE"),
		nullable=False)
	course = relationship("Courses")
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)


#################################################
# Posts - content postings made by users
#################################################

class Posts(Base):
	__tablename__ = 'Posts'
	id = Column(Integer, primary_key=True, nullable=False)
	users_id = Column(
		Integer,
		ForeignKey('Users.id', ondelete="CASCADE"),
		nullable=False)
	user = relationship("Users")
	courses_id = Column(
		Integer,
		ForeignKey('Courses.id', ondelete="CASCADE"),
		nullable=False)
	course = relationship("Courses")
	content = Column(Text)
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)


class PostsForQuestions(Base):
	__tablename__ = 'PostsForQuestions'
	id = Column(Integer, primary_key=True, nullable=False)
	posts_id = Column(
		Integer,
		ForeignKey('Posts.id', ondelete="CASCADE"),
		nullable=False)
	post = relationship("Posts")
	title = Column(String(255))
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
# don't need created time, posts store that info


class PostsForAnswers(Base):
	__tablename__ = 'PostsForAnswers'
	id = Column(Integer, primary_key=True, nullable=False)
	posts_id = Column(
		Integer,
		ForeignKey('Posts.id', ondelete="CASCADE"),
		nullable=False)
	post = relationship("Posts")


class PostsForComments(Base):
	__tablename__ = 'PostsForComments'
	id = Column(Integer, primary_key=True, nullable=False)
	posts_id = Column(
		Integer,
		ForeignKey('Posts.id', ondelete="CASCADE"),
		nullable=False)
	post = relationship("Posts")


#################################################
# Criteria - What users should judge answers by
#################################################

class Criteria(Base):
	__tablename__ = 'Criteria'
	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)
	description = Column(Text)
	# user who made this criteria
	users_id = Column(
		Integer,
		ForeignKey('Users.id', ondelete="CASCADE"),
		nullable=False)
	user = relationship("Users")
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)


# each course can have different criterias
class CriteriaAndCourses(Base):
	__tablename__ = 'CriteriaAndCourses'
	id = Column(Integer, primary_key=True, nullable=False)
	criteria_id = Column(
		Integer,
		ForeignKey('Criteria.id', ondelete="CASCADE"),
		nullable=False)
	criteria = relationship("Criteria")
	courses_id = Column(
		Integer,
		ForeignKey('Courses.id', ondelete="CASCADE"),
		nullable=False)
	course = relationship("Courses")


#################################################
# Scores - The calculated score of the answer
#################################################

class Scores(Base):
	__tablename__ = 'Scores'
	id = Column(Integer, primary_key=True, nullable=False)
	name = Column(String(255), unique=True, nullable=False)
	criteria_id = Column(
		Integer,
		ForeignKey('Criteria.id', ondelete="CASCADE"),
		nullable=False)
	criteria = relationship("Criteria")
	postsforanswers_id = Column(
		Integer,
		ForeignKey('PostsForAnswers.id', ondelete="CASCADE"),
		nullable=False)
	answer = relationship("PostsForAnswers")
	# number of times this answer has been judged
	rounds = Column(Integer, default=0)
	# number of times this answer has been picked as the better one
	wins = Column(Integer, default=0)
	# calculated score based on all previous judgements
	score = Column(Float, default=0)


#################################################
# Judgements - User's judgements on the answers
#################################################

class AnswerPairings(Base):
	__tablename__ = 'AnswerPairings'
	id = Column(Integer, primary_key=True)
	postsforquestions_id = Column(
		Integer,
		ForeignKey('PostsForQuestions.id', ondelete="CASCADE"),
		nullable=False)
	question = relationship("PostsForQuestions")
	postsforanswers_id1 = Column(
		Integer,
		ForeignKey('PostsForAnswers.id', ondelete="CASCADE"),
		nullable=False)
	answer1 = relationship("PostsForAnswers", foreign_keys=[postsforanswers_id1])
	postsforanswers_id2 = Column(
		Integer,
		ForeignKey('PostsForAnswers.id', ondelete="CASCADE"),
		nullable=False)
	answer2 = relationship("PostsForAnswers", foreign_keys=[postsforanswers_id2])
	winner_id = Column(
		Integer,
		ForeignKey('PostsForAnswers.id', ondelete="CASCADE"),
		nullable=False)
	winner = relationship("PostsForAnswers", foreign_keys=[winner_id])
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)


class Judgements(Base):
	__tablename__ = 'Judgements'
	id = Column(Integer, primary_key=True)
	users_id = Column(
		Integer,
		ForeignKey('Users.id', ondelete="CASCADE"),
		nullable=False)
	user = relationship("Users")
	answerpairings_id = Column(
		Integer,
		ForeignKey('AnswerPairings.id', ondelete="CASCADE"),
		nullable=False)
	answerpairing = relationship("AnswerPairings")
	criteria_id = Column(
		Integer,
		ForeignKey('Criteria.id', ondelete="CASCADE"),
		nullable=False)
	criteria = relationship("Criteria")
	modified = Column(
		TIMESTAMP,
		default=func.current_timestamp(),
		onupdate=func.current_timestamp(),
		nullable=False)
	created = Column(TIMESTAMP, default=func.current_timestamp(),
					 nullable=False)


class LTIInfo(Base):
	__tablename__ = 'LTIInfo'
	id = Column(Integer, primary_key=True)
	LTIid = Column(String(100))
	LTIURL = Column(String(100))
	courses_id = Column(
		Integer,
		ForeignKey('Courses.id', ondelete="CASCADE"),
		nullable=False)
	course = relationship("Courses")

