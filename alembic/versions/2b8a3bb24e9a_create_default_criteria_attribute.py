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
from sqlalchemy import UniqueConstraint

from acj.models import convention


def upgrade():
    op.add_column(
        'Criteria',
        sa.Column('default', sa.Boolean(name='default'), default=True, server_default='1', nullable=False))


def downgrade():
    with op.batch_alter_table(
            'Criteria', naming_convention=convention,
            table_args=(UniqueConstraint('name'))) as batch_op:
        batch_op.drop_column('default')
