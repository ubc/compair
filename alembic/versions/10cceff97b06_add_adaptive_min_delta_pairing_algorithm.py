"""add adaptive min delta pairing algorithm

Revision ID: 10cceff97b06
Revises: 346c3877ffae
Create Date: 2017-10-16 21:40:44.134149

"""

# revision identifiers, used by Alembic.
revision = '10cceff97b06'
down_revision = '346c3877ffae'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType

from enum import Enum
from sqlalchemy import bindparam
from sqlalchemy.sql.expression import null, update

from compair.models import convention

# In order to handle both upgrade and downgrade scenarios, we are not depending
# on definitions in compair.models.PairingAlgorithm.  Define our own here
class _OldPairingAlgorithm(Enum):
    adaptive = "adaptive"
    random = "random"

class _NewPairingAlgorithm(Enum):
    adaptive = "adaptive"
    random = "random"
    adaptive_min_delta = "adaptive_min_delta"

_table_names = ['assignment', 'comparison']

def upgrade():
    # Refer http://alembic.zzzcomputing.com/en/latest/ops.html#alembic.operations.Operations.alter_column
    # MySQL can't ALTER a column without a full spec.
    # So including existing_type, existing_server_default, and existing_nullable
    for table_name in _table_names:
        with op.batch_alter_table(table_name, naming_convention=convention) as batch_op:
            batch_op.alter_column('pairing_algorithm',
                type_=EnumType(_NewPairingAlgorithm, '_NewPairingAlgorithm'),
                existing_type=EnumType(_OldPairingAlgorithm, '_OldPairingAlgorithm'),
                existing_server_default=null(),
                existing_nullable=True)

def downgrade():
    connection = op.get_bind()
    for table_name in _table_names:
        # first update the adaptive_min_delta algo to adaptive algo
        table = sa.table(table_name,
            sa.Column('id', sa.Integer()),
            sa.Column('pairing_algorithm', EnumType(_NewPairingAlgorithm, '_NewPairingAlgorithm')))
        stmt = update(table).\
            where(table.c.pairing_algorithm == bindparam('from_algo')).\
            values(pairing_algorithm = bindparam('to_algo'))
        connection.execute(stmt, [{
            'from_algo': _NewPairingAlgorithm.adaptive_min_delta,
            'to_algo': _NewPairingAlgorithm.adaptive}])

        # then modify the enum type
        with op.batch_alter_table(table_name, naming_convention=convention) as batch_op:
            batch_op.alter_column('pairing_algorithm',
                type_=EnumType(_OldPairingAlgorithm, '_OldPairingAlgorithm'),
                existing_type=EnumType(_NewPairingAlgorithm, '_NewPairingAlgorithm'),
                existing_server_default=null(),
                existing_nullable=True)
