"""Add submission date to answer

Revision ID: d6c88adfe909
Revises: 8b4e3c1d8c41
Create Date: 2018-08-09 03:25:24.549790

"""

# revision identifiers, used by Alembic.
revision = 'd6c88adfe909'
down_revision = '8b4e3c1d8c41'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('submission_date', sa.DateTime(), nullable=True))
    op.execute('UPDATE answer SET submission_date=modified')

def downgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_column('submission_date')
