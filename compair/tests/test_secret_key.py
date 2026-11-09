# -*- coding: utf-8 -*-
"""
ComPAIR signs its Flask session cookie with SECRET_KEY. Older releases shipped a
fixed SECRET_KEY in compair/settings.py. Any deployment that kept it accepted
session cookies forged by anyone who had read the (open source) key: a cookie
carrying `_user_id` of an admin was accepted as that admin (account takeover).

These tests pin the fix:
  1. No usable SECRET_KEY ships in the source, and create_app() refuses to run
     with a missing/blank key or with the historically leaked key.
  2. A running app does not use the leaked key, so a cookie signed with the
     leaked key cannot produce a session the app will accept.
"""
from flask import Flask
from itsdangerous import BadSignature

from compair import create_app
from compair import settings as default_settings
from compair.configuration import config as base_config
from compair.tests import test_app_settings
from compair.tests.test_compair import ComPAIRAPITestCase

# The value that shipped in compair/settings.py up to and including 1.2.12.
# It is public, so a running app must never sign cookies with it again.
PUBLICLY_KNOWN_SECRET_KEY = "zfjlkfaweerP* SDF()U@#$haDJ;JKLASDFHUIO"

_UNSET = object()


def _settings_with_secret_key(secret_key):
    settings = dict(test_app_settings)
    if secret_key is _UNSET:
        settings.pop('SECRET_KEY', None)
    else:
        settings['SECRET_KEY'] = secret_key
    return settings


def _conf_without_secret_key():
    """The loaded configuration minus SECRET_KEY.

    create_app() applies `conf` before `settings_override`, and `conf` picks up
    SECRET_KEY from the environment or config.py (e.g. the dev docker-compose
    sets one). Strip it so the missing-key test does not depend on the
    developer's environment.
    """
    return {k: v for k, v in base_config.items() if k != 'SECRET_KEY'}


class SecretKeyConfigTest(ComPAIRAPITestCase):
    def test_default_settings_do_not_ship_a_usable_secret_key(self):
        shipped = getattr(default_settings, 'SECRET_KEY', None)
        self.assertIn(shipped, (None, ''),
                      "compair/settings.py must not ship a usable SECRET_KEY")

    def test_running_app_does_not_use_the_publicly_known_secret_key(self):
        self.assertNotEqual(self.app.config.get('SECRET_KEY'), PUBLICLY_KNOWN_SECRET_KEY)

    def test_create_app_refuses_a_missing_secret_key(self):
        with self.assertRaises(RuntimeError):
            create_app(conf=_conf_without_secret_key(),
                       settings_override=_settings_with_secret_key(_UNSET))

    def test_create_app_refuses_a_blank_secret_key(self):
        for blank in ('', '   '):
            with self.assertRaises(RuntimeError):
                create_app(settings_override=_settings_with_secret_key(blank))

    def test_create_app_refuses_the_publicly_known_secret_key(self):
        with self.assertRaises(RuntimeError):
            create_app(settings_override=_settings_with_secret_key(PUBLICLY_KNOWN_SECRET_KEY))


class ForgedSessionCookieTest(ComPAIRAPITestCase):
    def _sign_session_with(self, key, data):
        """Sign a session payload using Flask's real session serializer and `key`."""
        signer_app = Flask('signer')
        signer_app.secret_key = key
        signer_app.config.update(
            SESSION_COOKIE_NAME=self.app.config.get('SESSION_COOKIE_NAME', 'session'),
            SECRET_KEY_FALLBACKS=self.app.config.get('SECRET_KEY_FALLBACKS'),
        )
        serializer = self.app.session_interface.get_signing_serializer(signer_app)
        return serializer.dumps(dict(data))

    def test_leaked_key_cannot_sign_a_session_this_app_accepts(self):
        # An attacker signs an admin session (user id 1 is the default root
        # admin) with the publicly known key, using the app's own session salt.
        forged = self._sign_session_with(PUBLICLY_KNOWN_SECRET_KEY, {'_user_id': '1'})

        # The running app, using its own key, must reject that signature rather
        # than recover the attacker's session.
        app_serializer = self.app.session_interface.get_signing_serializer(self.app)
        with self.assertRaises(BadSignature):
            app_serializer.loads(forged)
