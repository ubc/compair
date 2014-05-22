"""
	Database Manager, manipulate the database from commandline
"""

from flask.ext.script import Manager, prompt_bool

manager = Manager(usage="Perform database operations")


@manager.command
def drop():
	"""Drops database tables"""
	if prompt_bool("Are you sure you want to lose all your data"):
		from acj.core import db
		db.drop_all()
		print ('All tables are dropped.')
		return True

	return False


@manager.command
def create(default_data=True, sample_data=False):
	"""Creates database tables from sqlalchemy models"""
	from acj.core import db
	db.create_all()
	populate(default_data, sample_data)
	print ('All tables are created and data is loaded.')


@manager.command
def recreate(default_data=True, sample_data=False):
	"""Recreates database tables (same as issuing 'drop' and then 'create')"""
	print ("Resetting database state...")
	if drop():
		create(default_data, sample_data)
	# TODO This is going to be broken with new db
	# also hard to update, should use the db models to insert data
	#with open('acj/static/test/testdata.sql', 'r') as f:
	#	db.execute(f.read().decode("utf8"))
	#db.commit()
	#print ("finished resetting db state")


@manager.command
def populate(default_data=False, sample_data=False):
	"""Populate database with default data"""
	from data.fixtures import dbfixture, all_data

	if default_data:
		#from fixtures.default_data import all

		default_data = dbfixture.data(*all_data)
		default_data.setup()

	if sample_data:
		#from fixtures.sample_data import all

		sample_data = dbfixture.data(*all_data)
		sample_data.setup()
