"""Add peer_feedback_prompt to assignment

Revision ID: 1a1082f21b88
Revises: 6802122e6f53
Create Date: 2017-01-23 20:18:33.525798

"""

# revision identifiers, used by Alembic.
revision = '1a1082f21b88'
down_revision = '6802122e6f53'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    op.add_column('assignment', sa.Column('peer_feedback_prompt', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('peer_feedback_prompt')
