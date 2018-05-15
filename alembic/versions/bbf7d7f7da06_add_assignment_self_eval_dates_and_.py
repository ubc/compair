"""add assignment self-eval dates and instructional text

Revision ID: bbf7d7f7da06
Revises: c8d5a5c16f59
Create Date: 2018-02-05 23:25:02.312998

"""

# revision identifiers, used by Alembic.
revision = 'bbf7d7f7da06'
down_revision = 'c8d5a5c16f59'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('self_eval_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('self_eval_end', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('self_eval_instructions', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('self_eval_start')
        batch_op.drop_column('self_eval_end')
        batch_op.drop_column('self_eval_instructions')
