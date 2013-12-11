"""Remove score from Script

Revision ID: 573c88e973e
Revises: c237957fe60
Create Date: 2013-12-11 13:26:40.186328

"""

# revision identifiers, used by Alembic.
revision = '573c88e973e'
down_revision = 'c237957fe60'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('Script', 'score')
    op.drop_column('Judgement', 'winner')


def downgrade():
    op.add_column('Script', sa.Column('score', Float, default=0))
    op.add_column('Judgement', sa.Column('winner', Integer, unique=False))
