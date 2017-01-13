"""Add weight to assignment_criterion

Revision ID: 3112cccea8d5
Revises: 1a1082f21b88
Create Date: 2017-01-11 23:40:31.058719

"""

# revision identifiers, used by Alembic.
revision = '3112cccea8d5'
down_revision = '1a1082f21b88'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    with op.batch_alter_table('assignment_criterion', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('weight', sa.Integer(), server_default='1', nullable=False))


def downgrade():
    with op.batch_alter_table('assignment_criterion', naming_convention=convention) as batch_op:
        batch_op.drop_column('weight')
