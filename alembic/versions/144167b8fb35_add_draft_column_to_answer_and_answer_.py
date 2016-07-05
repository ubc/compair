"""Add draft column to answer and answer_comment tables

Revision ID: 144167b8fb35
Revises: aafd2a91e3a
Create Date: 2016-07-05 12:09:24.279648

"""

# revision identifiers, used by Alembic.
revision = '144167b8fb35'
down_revision = 'aafd2a91e3a'

from alembic import op
import sqlalchemy as sa

from acj.models import convention

def upgrade():
    op.add_column('answer', sa.Column('draft', sa.Boolean(name='draft'), nullable=False, default='0', server_default='0'))
    op.add_column('answer_comment', sa.Column('draft', sa.Boolean(name='draft'), nullable=False, default='0', server_default='0'))

def downgrade():
    with op.batch_alter_table('answer_comment', naming_convention=convention) as batch_op:
        batch_op.drop_column('draft')
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_column('draft')
