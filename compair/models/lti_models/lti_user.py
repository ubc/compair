# sqlalchemy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_enum34 import EnumType
from flask import current_app

from . import *

from compair.core import db

class LTIUser(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'lti_user'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    lis_person_name_given = db.Column(db.String(255), nullable=True)
    lis_person_name_family = db.Column(db.String(255), nullable=True)
    lis_person_name_full = db.Column(db.String(255), nullable=True)
    lis_person_contact_email_primary = db.Column(db.String(255), nullable=True)
    compair_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True)
    system_role = db.Column(EnumType(SystemRole, name="system_role"), nullable=False)
    student_number = db.Column(db.String(255), nullable=True)

    # relationships
    # user via User Model
    # lti_consumer via LTIConsumer Model
    lti_memberships = db.relationship("LTIMembership", backref="lti_user", lazy="dynamic")
    lti_user_resource_links = db.relationship("LTIUserResourceLink", backref="lti_user", lazy="dynamic")

    # hybrid and other functions
    lti_consumer_uuid = association_proxy('lti_consumer', 'uuid')
    oauth_consumer_key = association_proxy('lti_consumer', 'oauth_consumer_key')
    compair_user_uuid = association_proxy('compair_user', 'uuid')

    def is_linked_to_user(self):
        return self.compair_user_id != None

    @classmethod
    def get_by_lti_consumer_id_and_user_id(cls, lti_consumer_id, user_id):
        return LTIUser.query \
            .filter_by(
                lti_consumer_id=lti_consumer_id,
                user_id=user_id
            ) \
            .one_or_none()

    @classmethod
    def get_by_tool_provider(cls, lti_consumer, tool_provider):
        from . import SystemRole

        if tool_provider.user_id == None:
            return None

        lti_user = LTIUser.get_by_lti_consumer_id_and_user_id(
            lti_consumer.id, tool_provider.user_id)

        if not lti_user:
            lti_user = LTIUser(
                lti_consumer_id=lti_consumer.id,
                user_id=tool_provider.user_id,
                system_role=SystemRole.instructor  \
                    if tool_provider.roles and any(
                        role.lower().find("instructor") >= 0 or
                        role.lower().find("faculty") >= 0 or
                        role.lower().find("staff") >= 0
                        for role in tool_provider.roles
                    ) \
                    else SystemRole.student
            )
            db.session.add(lti_user)

        lti_user.lis_person_name_given = tool_provider.lis_person_name_given
        lti_user.lis_person_name_family = tool_provider.lis_person_name_family
        lti_user.lis_person_name_full = tool_provider.lis_person_name_full
        lti_user.fix_name()
        lti_user.lis_person_contact_email_primary = tool_provider.lis_person_contact_email_primary

        if lti_consumer.student_number_param and lti_consumer.student_number_param in tool_provider.launch_params:
            lti_user.student_number = tool_provider.launch_params[lti_consumer.student_number_param]
        else:
            lti_user.student_number = None

        db.session.commit()

        return lti_user

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "LTI User Unavailable"
        if not message:
            message = "Sorry, this LTI user was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    # relationships

    def update_user_profile(self):
        if self.compair_user and self.compair_user.system_role == SystemRole.student:
            # overwrite first/last name if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_NAME'):
                self.compair_user.firstname = self.lis_person_name_given
                self.compair_user.lastname = self.lis_person_name_family

            # overwrite email if student not allowed to change it
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_EMAIL'):
                self.compair_user.email = self.lis_person_contact_email_primary

            # overwrite student number if student not allowed to change it and lti_consumer has a student_number_param
            if not current_app.config.get('ALLOW_STUDENT_CHANGE_STUDENT_NUMBER') and self.lti_consumer.student_number_param:
                self.compair_user.student_number = self.student_number

    def upgrade_system_role(self):
        # upgrade system role is needed
        if self.compair_user:
            if self.compair_user.system_role == SystemRole.student and self.system_role in [SystemRole.instructor, SystemRole.sys_admin]:
                self.compair_user.system_role = self.system_role
            elif self.compair_user.system_role == SystemRole.instructor and self.system_role == SystemRole.sys_admin:
                self.compair_user.system_role = self.system_role

            db.session.commit()

    def fix_name(self):
        if self.lis_person_name_full and (not self.lis_person_name_given or not self.lis_person_name_family):
            full_name_parts = self.lis_person_name_full.split(" ")
            if len(full_name_parts) >= 2:
                # assume lis_person_name_given is all but last part
                self.lis_person_name_given = " ".join(full_name_parts[:-1])
                self.lis_person_name_family = full_name_parts[-1]
            else:
                # not sure what is first or last name, just assignment both to full name
                self.lis_person_name_given = self.lis_person_name_full
                self.lis_person_name_family = self.lis_person_name_full

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_consumer_id', 'user_id', name='_unique_lti_consumer_and_lti_user'),
        DefaultTableMixin.default_table_args
    )
