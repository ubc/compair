"""Add lti tables

Revision ID: 485ff3eedf19
Revises: 3f3dd5a97fc7
Create Date: 2016-07-20 10:43:22.986658

"""

# revision identifiers, used by Alembic.
revision = '485ff3eedf19'
down_revision = '3f3dd5a97fc7'

from alembic import op
import sqlalchemy as sa

from sqlalchemy_enum34 import EnumType
from enum import Enum

from compair.models import convention

class SystemRole(Enum):
    student = "Student"
    instructor = "Instructor"
    sys_admin = "System Administrator"

class CourseRole(Enum):
    dropped = "Dropped"
    instructor = "Instructor"
    teaching_assistant = "Teaching Assistant"
    student = "Student"


def upgrade():
    op.create_table('lti_consumer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('oauth_consumer_key', sa.String(length=255), nullable=False),
        sa.Column('oauth_consumer_secret', sa.String(length=255), nullable=False),
        sa.Column('lti_version', sa.String(length=20), nullable=False),
        sa.Column('tool_consumer_instance_guid', sa.String(length=255), nullable=True),
        sa.Column('tool_consumer_instance_name', sa.String(length=255), nullable=True),
        sa.Column('tool_consumer_instance_url', sa.Text(), nullable=True),
        sa.Column('lis_outcome_service_url', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('oauth_consumer_key'),
        sa.UniqueConstraint('tool_consumer_instance_guid'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_lti_consumer_active'), 'lti_consumer', ['active'], unique=False)

    op.create_table('lti_context',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_consumer_id', sa.Integer(), nullable=False),
        sa.Column('context_id', sa.String(length=255), nullable=False),
        sa.Column('context_type', sa.String(length=255), nullable=True),
        sa.Column('context_title', sa.String(length=255), nullable=True),
        sa.Column('ext_ims_lis_memberships_id', sa.String(length=255), nullable=True),
        sa.Column('ext_ims_lis_memberships_url', sa.Text(), nullable=True),
        sa.Column('acj_course_id', sa.Integer(), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['acj_course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_consumer_id'], ['lti_consumer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_consumer_id', 'context_id', name='_unique_lti_consumer_and_lti_context'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.create_table('lti_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_consumer_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('lis_person_name_given', sa.String(length=255), nullable=True),
        sa.Column('lis_person_name_family', sa.String(length=255), nullable=True),
        sa.Column('lis_person_name_full', sa.String(length=255), nullable=True),
        sa.Column('lis_person_contact_email_primary', sa.String(length=255), nullable=True),
        sa.Column('acj_user_id', sa.Integer(), nullable=True),
        sa.Column('system_role', EnumType(SystemRole), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_consumer_id'], ['lti_consumer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['acj_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_consumer_id', 'user_id', name='_unique_lti_consumer_and_lti_user'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.create_table('lti_resource_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_consumer_id', sa.Integer(), nullable=False),
        sa.Column('lti_context_id', sa.Integer(), nullable=True),
        sa.Column('resource_link_id', sa.String(length=255), nullable=False),
        sa.Column('resource_link_title', sa.String(length=255), nullable=True),
        sa.Column('launch_presentation_return_url', sa.Text(), nullable=True),
        sa.Column('custom_param_assignment_id', sa.String(length=255), nullable=True),
        sa.Column('acj_assignment_id', sa.Integer(), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['acj_assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_consumer_id'], ['lti_consumer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lti_context_id'], ['lti_context.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_consumer_id', 'resource_link_id', name='_unique_lti_consumer_and_lti_resource_link'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.create_table('lti_membership',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_context_id', sa.Integer(), nullable=False),
        sa.Column('lti_user_id', sa.Integer(), nullable=False),
        sa.Column('roles', sa.String(length=255), nullable=True),
        sa.Column('lis_result_sourcedid', sa.String(length=255), nullable=True),
        sa.Column('course_role', EnumType(CourseRole), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_context_id'], ['lti_context.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lti_user_id'], ['lti_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_context_id', 'lti_user_id', name='_unique_lti_context_and_lti_user'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.create_table('lti_user_resource_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_resource_link_id', sa.Integer(), nullable=False),
        sa.Column('lti_user_id', sa.Integer(), nullable=False),
        sa.Column('roles', sa.String(length=255), nullable=True),
        sa.Column('lis_result_sourcedid', sa.String(length=255), nullable=True),
        sa.Column('course_role', EnumType(CourseRole), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_resource_link_id'], ['lti_resource_link.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lti_user_id'], ['lti_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_resource_link_id', 'lti_user_id', name='_unique_lti_resource_link_and_lti_user'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('lti_user_resource_link')
    op.drop_table('lti_membership')
    op.drop_table('lti_resource_link')
    op.drop_table('lti_user')
    op.drop_table('lti_context')
    op.drop_table('lti_consumer')
