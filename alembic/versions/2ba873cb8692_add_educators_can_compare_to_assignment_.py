"""add educators_can_compare to assignment table

Revision ID: 2ba873cb8692
Revises: b7b941f61291
Create Date: 2016-09-20 17:50:04.644507

"""

# revision identifiers, used by Alembic.
revision = '2ba873cb8692'
down_revision = 'b7b941f61291'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('educators_can_compare', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('educators_can_compare')
