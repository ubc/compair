from alembic import command

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from acj import db

from acj.tests.test_acj import ACJTestCase
from acj.tests import test_app_settings


class TestMigration(ACJTestCase):
	def test_migration(self):
		alembic_cfg = Config("alembic.ini")
		alembic_cfg.set_main_option('sqlalchemy.url', str(test_app_settings['SQLALCHEMY_DATABASE_URI']))
		connection = db.engine.connect()
		# alembic_cfg.set_main_option('connection', connection)
		context = MigrationContext.configure(connection)

		context._ensure_version_table()

		script = ScriptDirectory.from_config(alembic_cfg)
		head_revision = script.get_current_head()
		context.stamp(script, head_revision)

		command.downgrade(alembic_cfg, "base")

		command.upgrade(alembic_cfg, "head")
