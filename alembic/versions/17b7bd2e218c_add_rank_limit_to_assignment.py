"""Add rank_limit to assignment

Revision ID: 17b7bd2e218c
Revises: 3f27a2b13b82
Create Date: 2016-08-10 12:39:04.501928

"""

# revision identifiers, used by Alembic.
revision = '17b7bd2e218c'
down_revision = '3f27a2b13b82'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.add_column('assignment', sa.Column('rank_display_limit', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('rank_display_limit')