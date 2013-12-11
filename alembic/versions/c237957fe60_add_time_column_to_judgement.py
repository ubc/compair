"""Add time column to Judgement

Revision ID: c237957fe60
Revises: None
Create Date: 2013-12-11 13:25:09.535584

"""

# revision identifiers, used by Alembic.
revision = 'c237957fe60'
down_revision = None

from alembic import op
import sqlalchemy as sa
import datetime

def upgrade():
     op.add_column('Judgement', sa.Column('time', sa.DateTime, default=datetime.datetime.now))


def downgrade():
    op.drop_column('Judgement', 'time')
