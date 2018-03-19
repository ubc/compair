import hashlib
import json

from flask import current_app
from datetime import datetime
import time

# sqlalchemy
from sqlalchemy.orm import synonym
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_enum34 import EnumType

from . import *

from compair.core import db

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class ThirdPartyUser(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'third_party_user'

    # table columns
    third_party_type = db.Column(EnumType(ThirdPartyType, name="third_party_type"), nullable=False)
    unique_identifier = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    _params = db.Column(db.Text)

    # relationships
    # user via User Model
    compair_user_uuid = association_proxy('user', 'uuid')

    # hyprid and other functions

    @property
    def params(self):
        return json.loads(self._params) if self._params else None

    @params.setter
    def params(self, params):
        self._params = json.dumps(params) if params else None

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('third_party_type', 'unique_identifier', name='_unique_third_party_type_and_unique_identifier'),
        DefaultTableMixin.default_table_args
    )

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Third Party User Unavailable"
        if not message:
            message = "Sorry, this third party user was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)


    def update_user_profile(self):
        # TODO: Handle SAML in master
        if self.user and self.user.system_role == SystemRole.student and self.params:
            # overwrite first/last name if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_NAME'):
                firstname_attribute = current_app.config.get('CAS_ATTRIBUTE_FIRST_NAME')
                if self.third_party_type == ThirdPartyType.cas and firstname_attribute and firstname_attribute in self.params:
                    self.user.firstname = self.params.get(firstname_attribute)

                lastname_attribute = current_app.config.get('CAS_ATTRIBUTE_LAST_NAME')
                if self.third_party_type == ThirdPartyType.cas and lastname_attribute and lastname_attribute in self.params:
                    self.user.lastname = self.params.get(lastname_attribute)

            # overwrite email if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_EMAIL'):

                email_attribute = current_app.config.get('CAS_ATTRIBUTE_EMAIL')
                if self.third_party_type == ThirdPartyType.cas and email_attribute and email_attribute in self.params:
                    self.user.email = self.params.get(email_attribute)

            # overwrite student number if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'):

                student_number_attribute = current_app.config.get('CAS_ATTRIBUTE_STUDENT_NUMBER')
                if self.third_party_type == ThirdPartyType.cas and student_number_attribute and student_number_attribute in self.params:
                    self.user.student_number = self.params.get(student_number_attribute)
