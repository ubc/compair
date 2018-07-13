import requests
try:
    from urlparse import urlparse
    from urllib import quote_plus
except ImportError:
    from urllib.parse import urlparse
    from urllib.parse import quote_plus
from contextlib import contextmanager
from flask import current_app
from compair.core import abort

from . import KalturaCore

class KalturaSession(object):

    @classmethod
    @contextmanager
    def generate_api_session(cls, kaltura_user_id):
        ks = cls._api_start(kaltura_user_id)
        yield ks
        cls._api_end(ks)

    @classmethod
    def generate_upload_ks(cls, kaltura_user_id, upload_token_id):
        edit = "edit:"+upload_token_id
        urirestrict = "urirestrict:/"+KalturaCore.API_VERSION+"/service/uploadtoken/action/upload*"
        return cls._api_start(kaltura_user_id, privileges=edit+","+urirestrict)

    @classmethod
    def generate_direct_media_access_ks(cls, kaltura_user_id, entry_id, url, expiry=300):
        sview = "sview:" + entry_id
        urirestrict = ''
        if url:
            chunks = urlparse(url)
            if chunks.path:
                urirestrict = "urirestrict:" + chunks.path + '/*'
        if not urirestrict:
            urirestrict = "urirestrict:" + "/p/" + quote_plus(str(KalturaCore.partner_id()), '') + "/sp/*"

        return str(cls._api_start(kaltura_user_id, privileges=sview+","+urirestrict, expiry=expiry))

    @classmethod
    def _api_start(cls, kaltura_user_id, privileges=None, expiry=None):
        url = KalturaCore.base_url()+"/service/session/action/start"
        params = {
            'partnerId': KalturaCore.partner_id(),
            'userId': kaltura_user_id,
            'secret': KalturaCore.secret(),
            'type': KalturaCore.SESSION_TYPE_USER, # safer to go with user
            'format': 1, # json return value
        }
        if privileges:
            params['privileges'] = privileges
        if expiry:
            params['expiry'] = expiry
        result = requests.get(url, params=params, verify=KalturaCore.enforce_ssl())

        if result.status_code == 200:
            return result.json()
        else:
            current_app.logger.error(result)
            abort(400, title="File Not Uploaded",
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
            abort(400, title="File Not Uploaded",
                message="There was a problem with the Kaltura server. Please try again later.")