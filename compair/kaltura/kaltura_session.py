import requests
from contextlib import contextmanager
from flask import current_app
from compair.core import abort

from . import KalturaCore

class KalturaSession(object):

    @classmethod
    @contextmanager
    def generate_api_session(cls):
        ks = cls._api_start()
        yield ks
        cls._api_end(ks)

    @classmethod
    def generate_upload_ks(cls, upload_token_id):
        edit = "edit:"+upload_token_id
        urirestrict = "urirestrict:/"+KalturaCore.API_VERSION+"/service/uploadtoken/action/upload*"
        return cls._api_start(privileges=edit+","+urirestrict)

    @classmethod
    def _api_start(cls, privileges=None):
        url = KalturaCore.base_url()+"/service/session/action/start"
        params = {
            'partnerId': KalturaCore.partner_id(),
            'userId': KalturaCore.user_id(),
            'secret': KalturaCore.secret(),
            'type': KalturaCore.SESSION_TYPE_USER, # safer to go with user
            'format': 1, # json return value
        }
        if privileges:
            params['privileges'] = privileges
        result = requests.get(url, params=params, verify=KalturaCore.enforce_ssl())

        if result.status_code == 200:
            return result.json()
        else:
            current_app.logger.error(result)
            abort(400, title="Attachment Not Uploaded",
                message="There was a problem with the Kaltura server. Please try again later.")


    @classmethod
    def _api_end(cls, ks):
        url = KalturaCore.base_url()+"/service/session/action/end"
        params = {
            'ks': ks,
            'format': 1, # json return value
        }

        result = requests.get(url, params=params, verify=KalturaCore.enforce_ssl())

        if result.status_code == 200:
            return result.json()
        else:
            current_app.logger.error(result)
            abort(400, title="Attachment Not Uploaded",
                message="There was a problem with the Kaltura server. Please try again later.")