"""Add LTI course offering and section ids

Revision ID: 4670092712d7
Revises: 59646d2ad22c
Create Date: 2018-10-05 19:10:51.882637

"""

# revision identifiers, used by Alembic.
revision = '4670092712d7'
down_revision = '59646d2ad22c'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('lis_course_offering_sourcedid', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('lis_course_section_sourcedid', sa.String(length=255), nullable=True))

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('lis_person_sourcedid', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.drop_column('lis_person_sourcedid')

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.drop_column('lis_course_section_sourcedid')
        batch_op.drop_column('lis_course_offering_sourcedid')