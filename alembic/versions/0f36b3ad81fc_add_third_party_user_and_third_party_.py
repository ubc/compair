"""Add third_party_user table.

Revision ID: 0f36b3ad81fc
Revises: deafd926294b
Create Date: 2016-08-15 14:24:38.640736

"""

# revision identifiers, used by Alembic.
revision = '0f36b3ad81fc'
down_revision = 'deafd926294b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType
from enum import Enum

class ThirdPartyType(Enum):
    cwl = "CWL"

def upgrade():
    op.create_table('third_party_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('third_party_type', EnumType(ThirdPartyType), nullable=False),
        sa.Column('unique_identifier', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('third_party_type', 'unique_identifier', name='_unique_third_party_type_and_unique_identifier'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('third_party_user')
