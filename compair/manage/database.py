"""
    Database Manager, manipulate the database from commandline
"""
from alembic.config import Config
import click
from flask.cli import AppGroup

from alembic import command
from compair.core import db
from data.fixtures import DefaultFixture
from data.fixtures import DemoDataFixture

from sqlalchemy.engine import reflection
from sqlalchemy.schema import MetaData, Table, DropTable, ForeignKeyConstraint, DropConstraint

database_cli = AppGroup('database')

def _drop_tables():
    db.drop_all()

    print ('All tables dropped...')

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


@database_cli.command('drop')
@click.option('-y', '--yes', 'yes',  type=bool,
              prompt='Are you sure you want to lose all your data')
def click_drop(yes):
    if yes:
        drop()


def drop():
    """Drops database tables"""
    try:
        _drop_tables()
        db.session.commit()
    except Exception as e:
        print ("Database drop error: "+str(e))
        print ('Rolling back...')
        db.session.rollback()
        raise e

    print ('Drop database tables successful.')


@database_cli.command('create')
@click.argument('default_data', default=True, type=bool)
@click.argument('sample_data', default=False, type=bool)
def click_create(default_data, sample_data):
    create(default_data, sample_data)


# we separated the click configured function from the actual function so that
# we can call them from the tests. Calling them from the tests doesn't work
# with the click decorators applied.
def create(default_data, sample_data):
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


@database_cli.command('recreate')
@click.option('-y', '--yes', 'yes',  type=bool,
              prompt='Are you sure you want to lose all your data')
@click.option('-d', '--default-data', 'default_data', default=True, type=bool)
@click.option('-s', '--sample-data', 'sample_data', default=False, type=bool)
def click_recreate(yes, default_data, sample_data):
    if yes:
        recreate(default_data, sample_data)


def recreate(default_data=True, sample_data=False):
    """Recreates database tables (same as issuing 'drop' and then 'create')"""
    print ("Resetting database state...")
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


@database_cli.command('populate')
@click.argument('default_data', default=False, type=bool)
@click.argument('sample_data', default=False, type=bool)
def click_populate(default_data, sample_data):
    populate(default_data, sample_data)


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
