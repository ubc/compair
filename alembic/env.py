from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

from compair.configuration import config as compairconfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.get_main_option('sqlalchemy.url') is None:
    config.set_main_option('sqlalchemy.url', str(compairconfig['SQLALCHEMY_DATABASE_URI']))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.attributes.get('configure_logger', True):
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from compair.core import db

target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # the connection may come from the config object
    if hasattr(config, 'connection'):
        # load connection from config object
        connection = config.connection
    else:
        # load connection from config file
        engine = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix='sqlalchemy.',
            poolclass=pool.NullPool
        )
        connection = engine.connect()

    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        # don't close connection if it is from outside
        if not hasattr(config, 'connection'):
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

