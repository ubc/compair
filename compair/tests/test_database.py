# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
from unittest import mock

from flask_testing import TestCase
from sqlalchemy import inspect

from compair import create_app
from compair.core import db
from compair.manage.database import (
    database_cli,
    recreate_db, populate_tables,
    _drop_tables, _create_tables, _truncate_tables, _populate_tables,
)
from compair.models import User
from compair.tests import test_app_settings


class DatabaseHelpersTest(TestCase):
    def create_app(self):
        app = create_app(settings_override=test_app_settings)
        app.cli.add_command(database_cli)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _tables_exist(self):
        return inspect(db.engine).has_table('user')


    def test_drop_tables_removes_all_tables(self):
        self.assertTrue(self._tables_exist())
        _drop_tables()
        self.assertFalse(self._tables_exist())


    def test_create_tables_creates_all_tables(self):
        _drop_tables()
        self.assertFalse(self._tables_exist())
        with mock.patch('compair.manage.database.command'):
            _create_tables()
        self.assertTrue(self._tables_exist())


    def test_truncate_tables_clears_data_but_keeps_structure(self):
        from data.fixtures import DefaultFixture
        DefaultFixture()
        db.session.commit()
        self.assertGreater(User.query.count(), 0)

        _truncate_tables()
        db.session.commit()

        self.assertTrue(self._tables_exist())
        self.assertEqual(User.query.count(), 0)


    def test_populate_tables_with_default_data_creates_users(self):
        _populate_tables(default_data=True)
        db.session.commit()
        self.assertGreater(User.query.count(), 0)

    def test_populate_tables_with_no_flags_creates_nothing(self):
        _populate_tables(default_data=False, sample_data=False)
        db.session.commit()
        self.assertEqual(User.query.count(), 0)


class RecreateDatabaseTest(TestCase):
    def create_app(self):
        app = create_app(settings_override=test_app_settings)
        app.cli.add_command(database_cli)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_recreate_db_repopulates_database(self):
        from data.fixtures import DefaultFixture
        DefaultFixture()
        db.session.commit()

        with mock.patch('compair.manage.database.command'):
            recreate_db(default_data=True)

        self.assertGreater(User.query.count(), 0)

    def test_recreate_db_propagates_exception(self):
        with mock.patch('compair.manage.database._drop_tables', side_effect=Exception('drop failed')):
            with self.assertRaises(Exception, msg='drop failed'):
                recreate_db()

    def test_populate_tables_propagates_exception(self):
        with mock.patch('compair.manage.database._populate_tables', side_effect=Exception('populate failed')):
            with self.assertRaises(Exception, msg='populate failed'):
                populate_tables()


class DatabaseCLITest(TestCase):
    def create_app(self):
        app = create_app(settings_override=test_app_settings)
        app.cli.add_command(database_cli)
        return app

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_skips_when_tables_already_exist(self):
        db.create_all()
        result = self.app.test_cli_runner().invoke(database_cli, ['create'])
        self.assertIn('Tables exist', result.output)
        self.assertEqual(result.exit_code, 0)

    def test_create_succeeds_when_tables_do_not_exist(self):
        with mock.patch('compair.manage.database.command'):
            result = self.app.test_cli_runner().invoke(
                database_cli, ['create', '--no-default-data']
            )
        self.assertIn('Create database successful', result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(inspect(db.engine).has_table('user'))

    def test_drop_with_yes_flag_removes_all_tables(self):
        db.create_all()
        result = self.app.test_cli_runner().invoke(database_cli, ['drop', '--yes'])
        self.assertIn('Drop database tables successful', result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(inspect(db.engine).has_table('user'))

    def test_recreate_with_yes_flag_rebuilds_database(self):
        db.create_all()
        with mock.patch('compair.manage.database.command'):
            result = self.app.test_cli_runner().invoke(
                database_cli, ['recreate', '--yes', '--no-default-data']
            )
        self.assertIn('Recreate database successful', result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(inspect(db.engine).has_table('user'))

    def test_populate_command_adds_default_data(self):
        db.create_all()
        result = self.app.test_cli_runner().invoke(
            database_cli, ['populate', '--default-data']
        )
        self.assertIn('Populate database successful', result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertGreater(User.query.count(), 0)
