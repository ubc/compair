"""Add position to assignment_criterion

Revision ID: 12167f268066
Revises: 31fc9a032aa8
Create Date: 2016-11-30 23:49:11.830461

"""

# revision identifiers, used by Alembic.
revision = '12167f268066'
down_revision = '31fc9a032aa8'

from alembic import op
import sqlalchemy as sa
from compair.models import convention

def upgrade():
    op.add_column('assignment_criterion', sa.Column('position', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('assignment_criterion', naming_convention=convention) as batch_op:
        batch_op.drop_column('position')
