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
        with KalturaSession.generate_api_session() as ks:
            upload_token = UploadToken.generate_upload_token(ks)
            upload_token_id = upload_token.get('id')

        # generate an upload ks
        upload_ks = KalturaSession.generate_upload_ks(upload_token_id)

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
        kaltura_media = KalturaMedia.query \
            .filter_by(
                upload_token_id=upload_token_id,
                user_id=current_user.id,
                entry_id=None
            ) \
            .first()

        if not kaltura_media:
            abort(400, title="Attachment Not Uploaded",
                message="Upload token does not exist or already used.")

        with KalturaSession.generate_api_session() as ks:
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