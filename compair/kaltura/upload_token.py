import requests
from flask import current_app
from compair.core import abort

from . import KalturaCore

class UploadToken(object):
    @classmethod
    def generate_upload_token(cls, ks):
        return cls._api_add(ks)

    @classmethod
    def get_upload_token(cls, ks, upload_token_id):
        return cls._api_get(ks, upload_token_id)

    @classmethod
    def _api_add(cls, ks):
        url = KalturaCore.base_url()+"/service/uploadtoken/action/add"
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

    @classmethod
    def _api_get(cls, ks, upload_token_id):
        url = KalturaCore.base_url()+"/service/uploadtoken/action/get"
        params = {
            'uploadTokenId': upload_token_id,
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