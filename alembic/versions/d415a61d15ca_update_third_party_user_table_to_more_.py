"""Update third_party_user table to more generically work with cas

Revision ID: d415a61d15ca
Revises: 0a0d9eab68a3
Create Date: 2016-10-27 18:36:32.967124

"""

# revision identifiers, used by Alembic.
revision = 'd415a61d15ca'
down_revision = '0a0d9eab68a3'

from alembic import op
import sqlalchemy as sa

from compair.models import convention
from sqlalchemy_enum34 import EnumType
from enum import Enum

class NewThirdPartyType(Enum):
    cas = "CAS"

class OldThirdPartyType(Enum):
    cwl = "CWL"

class IntermediateThirdPartyType(Enum):
    cwl = "CWL"
    cas = "CAS"

intermediate_party_user_table = sa.table('third_party_user',
    sa.column('third_party_type', EnumType(IntermediateThirdPartyType))
)

def upgrade():
    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('_params', sa.Text, nullable=True))
        batch_op.alter_column('third_party_type',
            type_=EnumType(IntermediateThirdPartyType),
            existing_type=EnumType(OldThirdPartyType))

    connection = op.get_bind()
    connection.execute(
        intermediate_party_user_table.update()
        .where(intermediate_party_user_table.c.third_party_type == IntermediateThirdPartyType.cwl)
        .values(third_party_type=IntermediateThirdPartyType.cas)
    )

    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('third_party_type',
            type_=EnumType(NewThirdPartyType),
            existing_type=EnumType(IntermediateThirdPartyType))

def downgrade():
    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('third_party_type',
            type_=EnumType(IntermediateThirdPartyType),
            existing_type=EnumType(NewThirdPartyType))

    connection = op.get_bind()
    connection.execute(
        intermediate_party_user_table.update()
        .where(intermediate_party_user_table.c.third_party_type == IntermediateThirdPartyType.cas)
        .values(third_party_type=IntermediateThirdPartyType.cwl)
    )

    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('third_party_type',
            type_=EnumType(OldThirdPartyType),
            existing_type=EnumType(IntermediateThirdPartyType))
        batch_op.drop_column('_params')