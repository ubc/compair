"""Add SAML to third_party_type

Revision ID: 0a1ad609fc0a
Revises: 2561c39ac4d9
Create Date: 2017-12-07 00:43:05.761509

"""

# revision identifiers, used by Alembic.
revision = '0a1ad609fc0a'
down_revision = '2561c39ac4d9'

from alembic import op
import sqlalchemy as sa

from compair.models import convention
from sqlalchemy_enum34 import EnumType
from enum import Enum

class NewThirdPartyType(Enum):
    cas = "CAS"
    saml = "SAML"

class OldThirdPartyType(Enum):
    cas = "CAS"

def upgrade():
    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('third_party_type', type_=EnumType(NewThirdPartyType), existing_type=EnumType(OldThirdPartyType))


def downgrade():
    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('third_party_type', type_=EnumType(OldThirdPartyType), existing_type=EnumType(NewThirdPartyType))