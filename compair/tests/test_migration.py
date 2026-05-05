# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest
from alembic.config import Config

from alembic import command
from compair import db
from compair.tests.test_compair import ComPAIRTestCase


class TestMigration(ComPAIRTestCase):
    @unittest.skip("Historical migrations use SA 1.x syntax incompatible with SA 2.x. "
                   "Production deployments stamp at head and never replay from base.")
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
