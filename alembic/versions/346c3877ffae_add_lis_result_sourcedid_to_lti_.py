"""Add lis_result_sourcedid to lti_membership

Revision ID: 346c3877ffae
Revises: d402c96606ce
Create Date: 2017-08-15 23:30:27.653010

"""

# revision identifiers, used by Alembic.
revision = '346c3877ffae'
down_revision = 'd402c96606ce'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    with op.batch_alter_table('lti_membership', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('lis_result_sourcedids', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('lti_membership', naming_convention=convention) as batch_op:
        batch_op.drop_column('lis_result_sourcedids')
