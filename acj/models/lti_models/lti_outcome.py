# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIOutcome(Object):
    @classmethod
    def _send_outcome_result(self, lis_result_sourcedid, grade):
        """
        grade must be in range: [0.0, 1.0]
        """
        from lti.outcome_request import OutcomeRequest, REPLACE_REQUEST
        from flask import current_app
        if self.lis_outcome_service_url is None or self.lis_outcome_service_url == "" or
                lis_result_sourcedid is None or self.lis_outcome_service_url == "":
            # cannot send grade if no lis_outcome_service_url or lis_outcome_service_url
            return

        # build outcome request
        request = OutcomeRequest()
        request.consumer_key = self.oauth_consumer_key
        request.consumer_secret = self.oauth_consumer_secret
        request.consumer_secret = self.lis_outcome_service_url
        request.lis_result_sourcedid = lis_result_sourcedid
        request.operation = REPLACE_REQUEST

        rv = request.post_outcome_request()
        if rv.is_success():
            current_app.logger.debug("Successfully grade updated for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade))
        else:
            current_app.logger.error("Failed grade updated for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade))