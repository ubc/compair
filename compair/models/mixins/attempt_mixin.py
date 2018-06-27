import datetime
import dateutil.parser
import pytz
import re

import uuid
from duration import to_iso8601

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from compair.core import db, abort

class AttemptMixin(db.Model):
    __abstract__ = True

    @declared_attr
    def attempt_uuid(cls):
        # Note: not base64 encoded like in UUID Mixin (due to it being used for registration field in xAPI)
        return db.Column(db.CHAR(36), nullable=False, default=lambda: str(uuid.uuid4()))

    @declared_attr
    def attempt_started(cls):
        return db.Column(db.DateTime, nullable=True)

    @declared_attr
    def attempt_ended(cls):
        return db.Column(db.DateTime, nullable=True)

    def update_attempt(self, attempt_uuid, attempt_started, attempt_ended):
        uuid4_validation = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)

        if attempt_uuid and uuid4_validation.match(attempt_uuid):
            self.attempt_uuid = attempt_uuid

            self.attempt_started = attempt_started
            if self.attempt_started is not None:
                self.attempt_started = datetime.datetime.strptime(self.attempt_started, '%Y-%m-%dT%H:%M:%S.%fZ')

            self.attempt_ended = attempt_ended
            if self.attempt_ended is not None:
                self.attempt_ended = datetime.datetime.strptime(self.attempt_ended, '%Y-%m-%dT%H:%M:%S.%fZ')


    # hybrid and other functions
    @hybrid_property
    def attempt_duration(self):
        if self.attempt_started and self.attempt_ended:
            return to_iso8601(self.attempt_ended - self.attempt_started)
        return None
