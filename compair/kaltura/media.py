import requests
from flask import current_app
from compair.core import abort

from . import KalturaCore

class Media(object):
    @classmethod
    def generate_media_entry(cls, ks, upload_token_id, media_type):
        entry = cls._api_add(ks, media_type)
        entry = cls._api_add_content(ks, entry.get('id'), upload_token_id)
        return entry

    @classmethod
    def _api_add(cls, ks, media_type):
        url = KalturaCore.base_url()+"/service/media/action/add"
        params = {
            'entry[mediaType]': media_type,
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

    @classmethod
    def _api_add_content(cls, ks, entry_id, upload_token_id):
        url = KalturaCore.base_url()+"/service/media/action/addContent"
        params = {
            'entryId': entry_id,
            'resource[objectType]': 'KalturaUploadedFileTokenResource',
            'resource[token]': upload_token_id,
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