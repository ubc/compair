"""create default criteria attribute

Revision ID: 2b8a3bb24e9a
Revises: 316f3b73962c
Create Date: 2014-10-02 13:34:25.313161

"""

# revision identifiers, used by Alembic.
revision = '2b8a3bb24e9a'
down_revision = '316f3b73962c'

from alembic import op
import sqlalchemy as sa


def upgrade():

	op.add_column('Criteria', sa.Column('default', sa.Boolean, default=True, server_default='1', nullable=False))


def downgrade():

    op.drop_column('Criteria', 'default')
