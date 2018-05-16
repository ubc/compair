# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from alembic.config import Config

from alembic import command
from compair import db
from compair.tests.test_compair import ComPAIRTestCase


class TestMigration(ComPAIRTestCase):
    def test_migration(self):
        # create config object
        alembic_cfg = Config("compair/tests/alembic.ini")
        # get connection from db object
        connection = db.engine.connect()
        alembic_cfg.connection = connection

        command.stamp(alembic_cfg, 'head')

        command.downgrade(alembic_cfg, "base")

        command.upgrade(alembic_cfg, "head")

        command.downgrade(alembic_cfg, "base")
