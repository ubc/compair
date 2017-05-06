"""
    Database Manager, manipulate the database from commandline
"""
from alembic.config import Config
from flask_script import Manager, prompt_bool

from alembic import command
from compair.core import db
from data.fixtures import DefaultFixture
from data.fixtures import DemoDataFixture

from sqlalchemy.engine import reflection
from sqlalchemy.schema import MetaData, Table, DropTable, ForeignKeyConstraint, DropConstraint

manager = Manager(usage="Perform database operations")

def _drop_tables():
    db.drop_all()

    print ('All tables dropped...')

def _truncate_tables():
    metadata = MetaData()
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())

def _create_tables():
    db.create_all()

    # add database version table and add current head version
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.attributes['configure_logger'] = False
    command.stamp(alembic_cfg, 'head')

    print ('All tables created...')

def _populate_tables(default_data=False, sample_data=False):
    if default_data:
        DefaultFixture()

    if sample_data:
        DemoDataFixture()

    print ('All tables populated...')


@manager.command
def drop(yes=False):
    """Drops database tables"""
    if yes or prompt_bool("Are you sure you want to lose all your data"):
        try:
            _drop_tables()
            db.session.commit()
        except Exception as e:
            print ("Database drop error: "+str(e))
            print ('Rolling back...')
            db.session.rollback()
            raise e

        print ('Drop database tables successful.')


@manager.command
def create(default_data=True, sample_data=False):
    """Creates database tables from sqlalchemy models"""
    if db.engine.has_table('user'):
        print ('Tables exist. Skipping database create. Use database recreate instead.')
    else:
        try:
            _create_tables()
            _populate_tables(default_data, sample_data)
            db.session.commit()
        except Exception as e:
            print ("Database create error: "+str(e))
            print ('Rolling back...')
            db.session.rollback()
            raise e

        print ('Create database successful.')


@manager.command
def recreate(yes=False, default_data=True, sample_data=False):
    """Recreates database tables (same as issuing 'drop' and then 'create')"""
    print ("Resetting database state...")
    if yes or prompt_bool("Are you sure you want to lose all your data"):

        try:
            _drop_tables()
            _create_tables()
            _populate_tables(default_data, sample_data)
            db.session.commit()
        except Exception as e:
            print ("Database recreate error: "+str(e))
            print ('Rolling back...')
            db.session.rollback()
            raise e

        print ('Recreate database successful.')


@manager.command
def populate(default_data=False, sample_data=False):
    """Populate database with default data"""

    try:
        _populate_tables(default_data, sample_data)
        db.session.commit()
    except Exception as e:
        print ("Database populate error: "+str(e))
        print ('Rolling back...')
        db.session.rollback()
        raise e

    print ('Populate database successful.')