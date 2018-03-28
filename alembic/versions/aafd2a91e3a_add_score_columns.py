"""Add scoring_algorithm, variable1, variable2, and loses columns to score table

Revision ID: aafd2a91e3a
Revises: 36c9fd392e33
Create Date: 2016-06-28 15:49:10.314622

"""

# revision identifiers, used by Alembic.
revision = 'aafd2a91e3a'
down_revision = '36c9fd392e33'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType
from enum import Enum

from compair.models import convention

class ScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating"
    true_skill = "true_skill_rating"

def upgrade():
    with op.batch_alter_table('score', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('scoring_algorithm', EnumType(ScoringAlgorithm), nullable=True))
        batch_op.add_column(sa.Column('variable1', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('variable2', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('loses', sa.Integer(), nullable=False, default='0', server_default='0'))

def downgrade():
    with op.batch_alter_table('score', naming_convention=convention) as batch_op:
        batch_op.drop_column('loses')
        batch_op.drop_column('variable2')
        batch_op.drop_column('variable1')
        batch_op.drop_column('scoring_algorithm')

