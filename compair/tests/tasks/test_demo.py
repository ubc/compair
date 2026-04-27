# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch

from compair import create_app
from compair.tasks.demo import reset_demo
from compair.tests import test_app_settings


@pytest.fixture
def app():
    return create_app(settings_override=test_app_settings)


@pytest.fixture
def mock_recreate_db():
    with patch('compair.tasks.demo.recreate_db') as mock_recreate_db:
        yield mock_recreate_db


def test_reset_demo_calls_recreate_db_with_correct_args(app, mock_recreate_db):
    with app.app_context():
        reset_demo.apply()

    mock_recreate_db.assert_called_once_with(default_data=True, sample_data=True)


def test_reset_demo_propagates_exception_from_recreate_db(app, mock_recreate_db):
    mock_recreate_db.side_effect = Exception("db error")

    with app.app_context():
        with pytest.raises(Exception, match="db error"):
            reset_demo.apply(throw=True, retries=reset_demo.max_retries)
