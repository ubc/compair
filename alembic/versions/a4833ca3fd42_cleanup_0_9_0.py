"""cleanup 0.9.0

Revision ID: a4833ca3fd42
Revises: e74cf0affe74
Create Date: 2016-09-06 09:54:39.423881

"""

# revision identifiers, used by Alembic.
revision = 'a4833ca3fd42'
down_revision = 'e74cf0affe74'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('score', naming_convention=convention) as batch_op:
        batch_op.drop_column('excepted_score')


def downgrade():
    op.add_column('score', sa.Column('excepted_score', sa.Integer(), nullable=True))
