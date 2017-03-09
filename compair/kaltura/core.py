from flask import current_app
from flask_login import current_user
from compair.core import abort

from compair.core import db

from . import *

class KalturaCore(object):
    API_VERSION = 'api_v3'
    SESSION_TYPE_USER = 0
    SESSION_TYPE_ADMIN = 2

    @classmethod
    def enabled(cls):
        return current_app.config.get('KALTURA_ENABLED')

    @classmethod
    def service_url(cls):
        return current_app.config.get('KALTURA_SERVICE_URL')

    @classmethod
    def base_url(cls):
        return cls.service_url()+'/'+cls.API_VERSION

    @classmethod
    def enforce_ssl(cls):
        return current_app.config.get('ENFORCE_SSL', True)

    @classmethod
    def partner_id(cls):
        return current_app.config.get('KALTURA_PARTNER_ID')

    @classmethod
    def user_id(cls):
        return current_app.config.get('KALTURA_USER_ID')

    @classmethod
    def secret(cls):
        return current_app.config.get('KALTURA_SECRET')

    @classmethod
    def player_id(cls):
        return current_app.config.get('KALTURA_PLAYER_ID')

    @classmethod
    def video_extensions(cls):
        return current_app.config.get('KALTURA_VIDEO_EXTENSIONS')

    @classmethod
    def audio_extensions(cls):
        return current_app.config.get('KALTURA_AUDIO_EXTENSIONS')
