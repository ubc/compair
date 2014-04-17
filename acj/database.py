from __future__ import unicode_literals # for convenience & prep for python 3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

import sys

import settings # where the database settings are stored

# TODO CONNECT WILL FAIL IF DATABASE DOES NOT ALREADY EXIST, NEED INSTALLER
# TO CREATE DATABASE IF NOT EXIST
db_url = URL(**settings.DATABASE)
if len(sys.argv) > 1 and str(sys.argv[1]) == '--t':
	db_url = URL(**settings.DATABASE_TEST)

engine = create_engine(db_url, convert_unicode=True, pool_recycle=300)
db_session = scoped_session(sessionmaker(autocommit=False, 
										 autoflush=False, 
										 bind=engine))

# All tables should have this set of options enabled to make porting easier.
# In case we have to move to MariaDB instead of MySQL, e.g.: InnoDB in MySQL
# is replaced by XtraDB.
default_table_args = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB',
		'mysql_collate': 'utf8_unicode_ci'}

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
	import acj.models.UserTypesForSystem
	import acj.models.UserTypesForCourse
	import acj.models.Users
	Base.metadata.create_all(bind=engine)

#reset the database state; used in the e2e testcases
def reset_db():
	print ("resetting db state...")
	Base.metadata.drop_all(bind=engine)
	Base.metadata.create_all(bind=engine)
	# TODO This is going to be broken with new db
	# also hard to update, should use the db models to insert data
	with open('acj/static/test/testdata.sql', 'r') as f:
		db_session.execute(f.read().decode("utf8"))
	db_session.commit()
	print ("finished resetting db state")
