# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from oauthlib.oauth1 import Client
import base64
import hashlib

class LTIMemerbshipServiceOauthClient(Client):
    def get_oauth_params(self, request):
        """Get the basic OAuth parameters to be used in generating a signature.
        """
        params = super(LTIMemerbshipServiceOauthClient, self).get_oauth_params(request)

        # unlike parent class we need to include oauth_body_hash even if the body content is empty
        content_type = request.headers.get('Content-Type', None)
        content_type_eligible = content_type is None or content_type.find('application/x-www-form-urlencoded') < 0
        if content_type_eligible and request.body is None:
            params.append(('oauth_body_hash', base64.b64encode(hashlib.sha1("".encode('utf-8')).digest()).decode('utf-8')))

        return params