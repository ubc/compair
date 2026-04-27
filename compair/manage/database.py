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

database_cli = AppGroup('database', help="Perform database operations")

def _drop_tables():
    db.drop_all()

    print ('All tables dropped...')

def _truncate_tables():
    for table in reversed(db.metadata.sorted_tables):
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


@database_cli.command('drop')
@click.option('--yes', is_flag=True, default=False)
def drop(yes):
    """Drops database tables"""
    if yes or click.confirm("Are you sure you want to lose all your data"):
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
@click.option('--default-data/--no-default-data', default=True)
@click.option('--sample-data', is_flag=True, default=False)
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


def recreate_db(default_data=True, sample_data=False):
    """Recreates database tables (drop then create). Raises on failure."""
    print("Resetting database state...")
    try:
        _drop_tables()
        _create_tables()
        _populate_tables(default_data, sample_data)
        db.session.commit()
    except Exception as e:
        print("Database recreate error: " + str(e))
        print('Rolling back...')
        db.session.rollback()
        raise e
    print('Recreate database successful.')


@database_cli.command('recreate')
@click.option('--yes', is_flag=True, default=False)
@click.option('--default-data/--no-default-data', default=True)
@click.option('--sample-data', is_flag=True, default=False)
def recreate(yes, default_data, sample_data):
    """Recreates database tables (same as issuing 'drop' and then 'create')"""
    if yes or click.confirm("Are you sure you want to lose all your data"):
        recreate_db(default_data=default_data, sample_data=sample_data)


def populate_tables(default_data=False, sample_data=False):
    try:
        _populate_tables(default_data, sample_data)
        db.session.commit()
    except Exception as e:
        print ("Database populate error: "+str(e))
        print ('Rolling back...')
        db.session.rollback()
        raise e

    print ('Populate database successful.')


@database_cli.command('populate')
@click.option('--default-data', is_flag=True, default=False)
@click.option('--sample-data', is_flag=True, default=False)
def populate(default_data, sample_data):
    """Populate database with default data"""
    populate_tables(default_data, sample_data)
