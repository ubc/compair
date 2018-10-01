"""Mark current LTI as legacy

Revision ID: 20176ed1779d
Revises: b492a8f2132c
Create Date: 2018-10-02 16:41:56.661805

"""

# revision identifiers, used by Alembic.
revision = '20176ed1779d'
down_revision = 'b492a8f2132c'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('uq_lti_consumer_oauth_consumer_key', type_='unique')
        batch_op.drop_constraint('uq_lti_consumer_uuid', type_='unique')
        batch_op.drop_constraint('uq_lti_consumer_tool_consumer_instance_guid', type_='unique')
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_context_lti_consumer_id_lti_consumer', 'foreignkey')
        batch_op.drop_constraint('fk_lti_context_compair_course_id_course', 'foreignkey')
        batch_op.drop_constraint('uq_lti_context_uuid', type_='unique')
    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_resource_link_lti_consumer_id_lti_consumer', 'foreignkey')
        batch_op.drop_constraint('fk_lti_resource_link_lti_context_id_lti_context', 'foreignkey')
        batch_op.drop_constraint('fk_lti_resource_link_compair_assignment_id_assignment', 'foreignkey')
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_user_lti_consumer_id_lti_consumer', 'foreignkey')
        batch_op.drop_constraint('fk_lti_user_compair_user_id_user', 'foreignkey')
        batch_op.drop_constraint('uq_lti_user_uuid', type_='unique')
    with op.batch_alter_table('lti_user_resource_link', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_user_resource_link_lti_resource_link_id_lti_resource_link', 'foreignkey')
        batch_op.drop_constraint('fk_lti_user_resource_link_lti_user_id_lti_user', 'foreignkey')
    with op.batch_alter_table('lti_nonce', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_nonce_lti_consumer_id_lti_consumer', 'foreignkey')
    with op.batch_alter_table('lti_membership', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_lti_membership_lti_context_id_lti_context', 'foreignkey')
        batch_op.drop_constraint('fk_lti_membership_lti_user_id_lti_user', 'foreignkey')

    op.rename_table('lti_consumer', 'legacy_lti_consumer')
    op.rename_table('lti_context', 'legacy_lti_context')
    op.rename_table('lti_resource_link', 'legacy_lti_resource_link')
    op.rename_table('lti_user', 'legacy_lti_user')
    op.rename_table('lti_user_resource_link', 'legacy_lti_user_resource_link')
    op.rename_table('lti_nonce', 'legacy_lti_nonce')
    op.rename_table('lti_membership', 'legacy_lti_membership')

    with op.batch_alter_table('legacy_lti_consumer', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('uq_lti_consumer_oauth_consumer_key', ['oauth_consumer_key'])
        batch_op.create_unique_constraint('uq_lti_consumer_uuid', ['uuid'])
        batch_op.create_unique_constraint('uq_lti_consumer_tool_consumer_instance_guid', ['tool_consumer_instance_guid'])
    with op.batch_alter_table('legacy_lti_context', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_context_lti_consumer_id_legacy_lti_consumer', 'legacy_lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_context_compair_course_id_course', 'course', ['compair_course_id'], ['id'], ondelete="CASCADE")
        batch_op.create_unique_constraint('uq_lti_context_uuid', ['uuid'])
    with op.batch_alter_table('legacy_lti_resource_link', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_resource_link_lti_consumer_id_legacy_lti_consumer', 'legacy_lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_resource_link_lti_context_id_legacy_lti_context', 'legacy_lti_context', ['lti_context_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_resource_link_compair_assignment_id_assignment', 'assignment', ['compair_assignment_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('legacy_lti_user', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_user_lti_consumer_id_legacy_lti_consumer', 'legacy_lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_user_compair_user_id_user', 'user', ['compair_user_id'], ['id'], ondelete="CASCADE")
        batch_op.create_unique_constraint('uq_lti_user_uuid', ['uuid'])
    with op.batch_alter_table('legacy_lti_user_resource_link', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_user_resource_link_lti_resource_link_id_legacy_lti_resource_link', 'legacy_lti_resource_link', ['lti_resource_link_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_user_resource_link_lti_user_id_legacy_lti_user', 'legacy_lti_user', ['lti_user_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('legacy_lti_nonce', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_nonce_lti_consumer_id_legacy_lti_consumer', 'legacy_lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('legacy_lti_membership', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_membership_lti_context_id_legacy_lti_context', 'legacy_lti_context', ['lti_context_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_membership_lti_user_id_legacy_lti_user', 'legacy_lti_user', ['lti_user_id'], ['id'], ondelete="CASCADE")


def downgrade():
    # this try catch is here because alembic unit tests will auto load using naming convention
    # but we aren't using since the constraint names are too long for mysql for this legacy business
    try:
        with op.batch_alter_table('legacy_lti_membership', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_membership_lti_context_id_legacy_lti_context', 'foreignkey')
            batch_op.drop_constraint('fk_lti_membership_lti_user_id_legacy_lti_user', 'foreignkey')
        with op.batch_alter_table('legacy_lti_nonce', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_nonce_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
        with op.batch_alter_table('legacy_lti_user_resource_link', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_user_resource_link_lti_resource_link_id_legacy_lti_resource_link', 'foreignkey')
            batch_op.drop_constraint('fk_lti_user_resource_link_lti_user_id_legacy_lti_user', 'foreignkey')
        with op.batch_alter_table('legacy_lti_user', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_user_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_lti_user_compair_user_id_user', 'foreignkey')
            batch_op.drop_constraint('uq_lti_user_uuid', type_='unique')
        with op.batch_alter_table('legacy_lti_resource_link', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_resource_link_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_lti_resource_link_lti_context_id_legacy_lti_context', 'foreignkey')
            batch_op.drop_constraint('fk_lti_resource_link_compair_assignment_id_assignment', 'foreignkey')
        with op.batch_alter_table('legacy_lti_context', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_lti_context_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_lti_context_compair_course_id_course', 'foreignkey')
            batch_op.drop_constraint('uq_lti_context_uuid', type_='unique')
        with op.batch_alter_table('legacy_lti_consumer', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('uq_lti_consumer_oauth_consumer_key', type_='unique')
            batch_op.drop_constraint('uq_lti_consumer_uuid', type_='unique')
            batch_op.drop_constraint('uq_lti_consumer_tool_consumer_instance_guid', type_='unique')
    except ValueError:
        with op.batch_alter_table('legacy_lti_membership', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_membership_lti_context_id_legacy_lti_context', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_membership_lti_user_id_legacy_lti_user', 'foreignkey')
        with op.batch_alter_table('legacy_lti_nonce', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_nonce_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
        with op.batch_alter_table('legacy_lti_user_resource_link', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_user_resource_link_lti_resource_link_id_legacy_lti_resource_link', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_user_resource_link_lti_user_id_legacy_lti_user', 'foreignkey')
        with op.batch_alter_table('legacy_lti_user', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_user_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_user_compair_user_id_user', 'foreignkey')
            batch_op.drop_constraint('uq_legacy_lti_user_uuid', type_='unique')
        with op.batch_alter_table('legacy_lti_resource_link', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_resource_link_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_resource_link_lti_context_id_legacy_lti_context', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_resource_link_compair_assignment_id_assignment', 'foreignkey')
        with op.batch_alter_table('legacy_lti_context', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_legacy_lti_context_lti_consumer_id_legacy_lti_consumer', 'foreignkey')
            batch_op.drop_constraint('fk_legacy_lti_context_compair_course_id_course', 'foreignkey')
            batch_op.drop_constraint('uq_legacy_lti_context_uuid', type_='unique')
        with op.batch_alter_table('legacy_lti_consumer', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('uq_legacy_lti_consumer_oauth_consumer_key', type_='unique')
            batch_op.drop_constraint('uq_legacy_lti_consumer_uuid', type_='unique')
            batch_op.drop_constraint('uq_legacy_lti_consumer_tool_consumer_instance_guid', type_='unique')

    op.rename_table('legacy_lti_membership', 'lti_membership')
    op.rename_table('legacy_lti_nonce', 'lti_nonce')
    op.rename_table('legacy_lti_user_resource_link', 'lti_user_resource_link')
    op.rename_table('legacy_lti_user', 'lti_user')
    op.rename_table('legacy_lti_resource_link', 'lti_resource_link')
    op.rename_table('legacy_lti_context', 'lti_context')
    op.rename_table('legacy_lti_consumer', 'lti_consumer')

    with op.batch_alter_table('lti_membership', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_membership_lti_context_id_lti_context', 'lti_context', ['lti_context_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_membership_lti_user_id_lti_user', 'lti_user', ['lti_user_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('lti_user_resource_link', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_user_resource_link_lti_resource_link_id_lti_resource_link', 'lti_resource_link', ['lti_resource_link_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_user_resource_link_lti_user_id_lti_user', 'lti_user', ['lti_user_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('lti_nonce', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_nonce_lti_consumer_id_lti_consumer', 'lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_user_lti_consumer_id_lti_consumer', 'lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_user_compair_user_id_user', 'user', ['compair_user_id'], ['id'], ondelete="CASCADE")
        batch_op.create_unique_constraint('uq_lti_user_uuid', ['uuid'])
    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_resource_link_lti_consumer_id_lti_consumer', 'lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_resource_link_lti_context_id_lti_context', 'lti_context', ['lti_context_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_resource_link_compair_assignment_id_assignment', 'assignment', ['compair_assignment_id'], ['id'], ondelete="CASCADE")
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_lti_context_lti_consumer_id_lti_consumer', 'lti_consumer', ['lti_consumer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_lti_context_compair_course_id_course', 'course', ['compair_course_id'], ['id'], ondelete="CASCADE")
        batch_op.create_unique_constraint('uq_lti_context_uuid', ['uuid'])
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('uq_lti_consumer_oauth_consumer_key', ['oauth_consumer_key'])
        batch_op.create_unique_constraint('uq_lti_consumer_uuid', ['uuid'])
        batch_op.create_unique_constraint('uq_lti_consumer_tool_consumer_instance_guid', ['tool_consumer_instance_guid'])