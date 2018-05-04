"""merge d8f2aa162e1f and 265dc6402cf8

Revision ID: 907993a4de86
Revises: ('d8f2aa162e1f', '265dc6402cf8')
Create Date: 2018-05-04 16:32:28.445865

"""

# revision identifiers, used by Alembic.
revision = '907993a4de86'
down_revision = ('d8f2aa162e1f', '265dc6402cf8')

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    pass


def downgrade():
    pass
