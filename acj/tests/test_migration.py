from alembic import command

from alembic.config import Config
from acj import db

from acj.tests.test_acj import ACJTestCase


class TestMigration(ACJTestCase):
	def test_migration(self):
		# create config object
		alembic_cfg = Config("alembic.ini")
		# get connection from db object
		connection = db.engine.connect()
		alembic_cfg.connection = connection

		command.stamp(alembic_cfg, 'head')

		command.downgrade(alembic_cfg, "base")

		command.upgrade(alembic_cfg, "head")
