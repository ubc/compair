try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus
from flask import current_app
from flask_login import current_user
from compair.core import abort

from compair.core import db

from compair.models import KalturaMedia
from . import KalturaCore, KalturaSession, Media, UploadToken

class KalturaAPI(object):
    @classmethod
    def enabled(cls):
        return KalturaCore.enabled()

    @classmethod
    def generate_new_upload_token(cls):
        kaltura_user_id = KalturaCore.user_id()
        if current_app.config.get('KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER', False) and current_user and current_user.global_unique_identifier:
            kaltura_user_id = current_user.global_unique_identifier

        with KalturaSession.generate_api_session(kaltura_user_id) as ks:
            upload_token = UploadToken.generate_upload_token(ks)
            upload_token_id = upload_token.get('id')

        # generate an upload ks
        upload_ks = KalturaSession.generate_upload_ks(kaltura_user_id, upload_token_id)

        media = KalturaMedia(
            user=current_user,
            service_url=KalturaCore.service_url(),
            partner_id=KalturaCore.partner_id(),
            player_id=KalturaCore.player_id(),
            upload_ks=upload_ks,
            upload_token_id=upload_token_id
        )
        db.session.add(media)
        db.session.commit()

        return KalturaCore.base_url()+"/service/uploadtoken/action/upload?format=1&uploadTokenId="+upload_token_id+"&ks="+upload_ks

    @classmethod
    def complete_upload_for_token(cls, upload_token_id):
        kaltura_user_id = KalturaCore.user_id()
        if current_app.config.get('KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER', False) and current_user and current_user.global_unique_identifier:
            kaltura_user_id = current_user.global_unique_identifier

        kaltura_media = KalturaMedia.query \
            .filter_by(
                upload_token_id=upload_token_id,
                user_id=current_user.id,
                entry_id=None
            ) \
            .first()

        if not kaltura_media:
            abort(400, title="File Not Uploaded",
                message="The upload token does not exist or is already used. Please contact support for assistance.")

        with KalturaSession.generate_api_session(kaltura_user_id) as ks:
            # fetch upload, and update kaltura_media filename
            upload_token = UploadToken.get_upload_token(ks, upload_token_id)
            kaltura_media.file_name = upload_token.get('fileName')

            # create the media entry and associate it with the completed upload
            entry = Media.generate_media_entry(ks, upload_token_id, kaltura_media.media_type)
            kaltura_media.entry_id = entry.get('id')
            kaltura_media.download_url = entry.get('downloadUrl')

        # delete the upload session
        KalturaSession._api_end(kaltura_media.upload_ks)
        db.session.commit()

        return kaltura_media

    @classmethod
    def get_direct_access_url(cls, entry_id, download_url, expiry=300):
        """
            Generate a new Kaltura Session (KS) and return an URL for direct download of Kaltura media file.
            :param entry_id: the Kaltura entry ID of the file to download
            :param download_url: URL to download the file
            :param expiry: optional expiry time of the KS, in seconds. Default is 300 seconds.
            :return: a URL with KS attached for downloading the given Kaltura media file
        """
        kaltura_user_id = KalturaCore.user_id()
        if current_app.config.get('KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER', False) and current_user and current_user.global_unique_identifier:
            kaltura_user_id = current_user.global_unique_identifier

        url = download_url
        if not url:
            abort(404, title="File Not Found",
                message="The file is not available on Kaltura server yet. Please try again later.")

        session = KalturaSession.generate_direct_media_access_ks(kaltura_user_id, entry_id, url, expiry)
        url = url + "/ks/" + quote_plus(session, '')

        return url