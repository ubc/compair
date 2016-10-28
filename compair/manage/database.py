"""
    Database Manager, manipulate the database from commandline
"""
from alembic.config import Config
from flask_script import Manager, prompt_bool

from alembic import command
from acj.core import db

from sqlalchemy.engine import reflection
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table, DropTable, ForeignKeyConstraint, DropConstraint

manager = Manager(usage="Perform database operations")


@manager.command
def drop():
    """Drops database tables"""
    if prompt_bool("Are you sure you want to lose all your data"):
        inspector = reflection.Inspector.from_engine(db.engine)
        metadata = MetaData()
        tbs = []
        all_fks = []
        for table_name in inspector.get_table_names():
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append( ForeignKeyConstraint((),(),name=fk['name']) )
            t = Table(table_name,metadata,*fks)
            tbs.append(t)
            all_fks.extend(fks)

        for fkc in all_fks:
            db.engine.execute(DropConstraint(fkc))

        for table in tbs:
            db.engine.execute(DropTable(table))

        db.session.commit()

        print ('All tables are dropped.')
        return True

    return False


@manager.command
def create(default_data=True, sample_data=False):
    """Creates database tables from sqlalchemy models"""
    db.create_all()
    populate(default_data, sample_data)

    # add database version table and add current head version
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, 'head')

    print ('All tables are created and data is loaded.')


@manager.command
def recreate(default_data=True, sample_data=False):
    """Recreates database tables (same as issuing 'drop' and then 'create')"""
    print ("Resetting database state...")
    if drop():
        create(default_data, sample_data)


@manager.command
def populate(default_data=False, sample_data=False):
    """Populate database with default data"""

    if default_data:
        # from fixtures.default_data import all
        from data.fixtures import DefaultFixture
        DefaultFixture()
        db.session.commit()

    if sample_data:
        from data.fixtures import SampleDataFixture
        SampleDataFixture()
        db.session.commit()
