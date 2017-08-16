"""Allow user's username and password to be null

Revision ID: e74cf0affe74
Revises: 0f36b3ad81fc
Create Date: 2016-08-26 10:34:27.420511

"""

# revision identifiers, used by Alembic.
revision = 'e74cf0affe74'
down_revision = '0f36b3ad81fc'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.alter_column('_password', nullable=True, existing_type=sa.String(length=255))
        batch_op.alter_column('username', nullable=True, existing_type=sa.String(length=255))


def downgrade():
    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.alter_column('_password', nullable=False, existing_type=sa.String(length=255))
        batch_op.alter_column('username', nullable=False, existing_type=sa.String(length=255))
