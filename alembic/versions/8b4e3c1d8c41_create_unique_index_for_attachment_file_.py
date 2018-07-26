"""Create unique index for attachment file name

Revision ID: 8b4e3c1d8c41
Revises: bbf7d7f7da06
Create Date: 2018-07-23 16:36:20.186728

"""

# revision identifiers, used by Alembic.
revision = '8b4e3c1d8c41'
down_revision = 'bbf7d7f7da06'

import logging
from alembic import op

from compair.models import convention

def upgrade():
    # create unique index for file.name
    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint(op.f('uq_file_name'), ['name'])

def downgrade():
    # drop the unique index
    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('uq_file_name', type_='unique')
