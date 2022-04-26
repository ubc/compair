import hashlib
import json

from flask import current_app
from datetime import datetime
import time

# sqlalchemy
from sqlalchemy.orm import synonym
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy

from . import *

from compair.core import db, display_name_generator

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class ThirdPartyUser(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'third_party_user'

    # table columns
    third_party_type = db.Column(Enum(ThirdPartyType), nullable=False)
    unique_identifier = db.Column(db.String(191), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    _params = db.Column(db.Text)

    # relationships
    # user via User Model
    user_uuid = association_proxy('user', 'uuid')

    # hybrid and other functions

    @property
    def params(self):
        return json.loads(self._params) if self._params else None

    @params.setter
    def params(self, params):
        self._params = json.dumps(params) if params else None

    @property
    def global_unique_identifier(self):
        if self.params:
            global_unique_identifier_attribute = None
            if self.third_party_type == ThirdPartyType.cas:
                global_unique_identifier_attribute = current_app.config.get('CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD')
            elif self.third_party_type == ThirdPartyType.saml:
                global_unique_identifier_attribute = current_app.config.get('SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD')

            if global_unique_identifier_attribute and global_unique_identifier_attribute in self.params:
                global_unique_identifier = self.params.get(global_unique_identifier_attribute)
                if isinstance(global_unique_identifier, list):
                    global_unique_identifier = global_unique_identifier[0] if len(global_unique_identifier) > 0 else None
                return global_unique_identifier

        return None

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

    def generate_or_link_user_account(self):
        from . import SystemRole, User

        if not self.user:
            # check if global_unique_identifier user already exists
            if self.global_unique_identifier:
                self.user = User.query \
                    .filter_by(global_unique_identifier=self.global_unique_identifier) \
                    .one_or_none()

            if not self.user:
                self.user = User(
                    username=None,
                    password=None,
                    system_role=self._get_system_role(),
                    global_unique_identifier=self.global_unique_identifier
                )
                self._sync_name()
                self._sync_email()
                if self.user.system_role == SystemRole.student:
                    self._sync_student_number()

                # instructors can have their display names set to their full name by default
                if self.user.system_role != SystemRole.student and self.user.fullname != None:
                    self.user.displayname = self.user.fullname
                else:
                    self.user.displayname = display_name_generator(self.user.system_role.value)

    def update_user_profile(self):
        if self.user and self.user.system_role == SystemRole.student and self.params:
            # overwrite first/last name if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_NAME'):
                self._sync_name()

            # overwrite email if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_EMAIL'):
                self._sync_email()

            # overwrite student number if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'):
                self._sync_student_number()

    def _sync_name(self):
        if self.params:
            firstname_attribute = lastname_attribute = None
            if self.third_party_type == ThirdPartyType.cas:
                firstname_attribute = current_app.config.get('CAS_ATTRIBUTE_FIRST_NAME')
                lastname_attribute = current_app.config.get('CAS_ATTRIBUTE_LAST_NAME')
            elif self.third_party_type == ThirdPartyType.saml:
                firstname_attribute = current_app.config.get('SAML_ATTRIBUTE_FIRST_NAME')
                lastname_attribute = current_app.config.get('SAML_ATTRIBUTE_LAST_NAME')

            if firstname_attribute and firstname_attribute in self.params:
                first_name = self.params.get(firstname_attribute)
                if isinstance(first_name, list):
                    first_name = first_name[0] if len(first_name) > 0 else None
                self.user.firstname = first_name

            if lastname_attribute and lastname_attribute in self.params:
                last_name = self.params.get(lastname_attribute)
                if isinstance(last_name, list):
                    last_name = last_name[0] if len(last_name) > 0 else None
                self.user.lastname = last_name

    def _sync_email(self):
        if self.params:
            email_attribute = None
            if self.third_party_type == ThirdPartyType.cas:
                email_attribute = current_app.config.get('CAS_ATTRIBUTE_EMAIL')
            elif self.third_party_type == ThirdPartyType.saml:
                email_attribute = current_app.config.get('SAML_ATTRIBUTE_EMAIL')

            if email_attribute and email_attribute in self.params:
                email = self.params.get(email_attribute)
                if isinstance(email, list):
                    email = email[0] if len(email) > 0 else None
                self.user.email = email

    def _sync_student_number(self):
        if self.params:
            student_number_attribute = None
            if self.third_party_type == ThirdPartyType.cas:
                student_number_attribute = current_app.config.get('CAS_ATTRIBUTE_STUDENT_NUMBER')
            elif self.third_party_type == ThirdPartyType.saml:
                student_number_attribute = current_app.config.get('SAML_ATTRIBUTE_STUDENT_NUMBER')

            if student_number_attribute and student_number_attribute in self.params:
                student_number = self.params.get(student_number_attribute)
                if isinstance(student_number, list):
                    student_number = student_number[0] if len(student_number) > 0 else None
                self.user.student_number = student_number

    def _get_system_role(self):
        from . import SystemRole

        if self.params:
            user_roles_attribute = instructor_role_values = None
            if self.third_party_type == ThirdPartyType.cas:
                user_roles_attribute = current_app.config.get('CAS_ATTRIBUTE_USER_ROLE')
                instructor_role_values = list(current_app.config.get('CAS_INSTRUCTOR_ROLE_VALUES'))
            if self.third_party_type == ThirdPartyType.saml:
                user_roles_attribute = current_app.config.get('SAML_ATTRIBUTE_USER_ROLE')
                instructor_role_values = list(current_app.config.get('SAML_INSTRUCTOR_ROLE_VALUES'))

            if user_roles_attribute and instructor_role_values and user_roles_attribute in self.params:
                user_roles = self.params.get(user_roles_attribute)
                if not isinstance(user_roles, list):
                    user_roles = [user_roles]

                for user_role in user_roles:
                    if user_role in instructor_role_values:
                        return SystemRole.instructor

        return SystemRole.student

    def upgrade_system_role(self):
        # upgrade system role is needed
        if self.user and self.params and self._get_system_role():
            system_role = self._get_system_role()
            if self.user.system_role == SystemRole.student and system_role == SystemRole.instructor:
                self.user.system_role = system_role

            db.session.commit()
