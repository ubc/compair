"""Rename LTI namespaced columns

Revision ID: 0a0d9eab68a3
Revises: 014281cc823f
Create Date: 2016-10-28 22:23:13.589342

"""

# revision identifiers, used by Alembic.
revision = '0a0d9eab68a3'
down_revision = '014281cc823f'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    # lti_context
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_context_acj_course_id_course', 'foreignkey')

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('acj_course_id', new_column_name='compair_course_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_context_compair_course_id_course',
            'course', ['compair_course_id'], ['id'], ondelete="CASCADE")

    # lti_resource_link
    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_resource_link_acj_assignment_id_assignment', 'foreignkey')

    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('acj_assignment_id', new_column_name='compair_assignment_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_resource_link_compair_assignment_id_assignment',
            'assignment', ['compair_assignment_id'], ['id'], ondelete="CASCADE")

    # lti_user
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_user_acj_user_id_user', 'foreignkey')

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('acj_user_id', new_column_name='compair_user_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_user_compair_user_id_user',
            'user', ['compair_user_id'], ['id'], ondelete="CASCADE")


def downgrade():
    # lti_user
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_user_compair_user_id_user', 'foreignkey')

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('compair_user_id', new_column_name='acj_user_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_user_acj_user_id_user',
            'user', ['acj_user_id'], ['id'], ondelete="CASCADE")

    # lti_resource_link
    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_resource_link_compair_assignment_id_assignment', 'foreignkey')

    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('compair_assignment_id', new_column_name='acj_assignment_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_resource_link_acj_assignment_id_assignment',
            'assignment', ['acj_assignment_id'], ['id'], ondelete="CASCADE")

    # lti_context
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_lti_context_compair_course_id_course', 'foreignkey')

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('compair_course_id', new_column_name='acj_course_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_lti_context_acj_course_id_course',
            'course', ['acj_course_id'], ['id'], ondelete="CASCADE")