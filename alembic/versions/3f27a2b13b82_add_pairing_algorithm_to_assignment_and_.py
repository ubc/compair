"""Add pairing_algorithm to assignment and comparison tables

Revision ID: 3f27a2b13b82
Revises: 24bd55036bca
Create Date: 2016-07-15 14:00:31.190921

"""

# revision identifiers, used by Alembic.
revision = '3f27a2b13b82'
down_revision = '24bd55036bca'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy_enum34 import EnumType
from enum import Enum
from compair.models import convention

class PairingAlgorithm(Enum):
    adaptive = "adaptive"
    random = "random"

def upgrade():
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('pairing_algorithm', EnumType(PairingAlgorithm), nullable=True))
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('pairing_algorithm', EnumType(PairingAlgorithm), nullable=True))


def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('pairing_algorithm')
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.drop_column('pairing_algorithm')
