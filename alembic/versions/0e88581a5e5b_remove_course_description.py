"""Remove course description

Revision ID: 0e88581a5e5b
Revises: ed763e759c2a
Create Date: 2017-02-06 20:47:07.952542

"""

# revision identifiers, used by Alembic.
revision = '0e88581a5e5b'
down_revision = 'ed763e759c2a'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('course', naming_convention=convention) as batch_op:
        batch_op.drop_column('description')

def downgrade():
    with op.batch_alter_table('course', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text, nullable=True))
