"""add course sandbox flag

Revision ID: 82ed8fc51745
Revises: 346c3877ffae
Create Date: 2017-10-10 11:55:58.012318

"""

# revision identifiers, used by Alembic.
revision = '82ed8fc51745'
down_revision = '346c3877ffae'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('course', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('sandbox', sa.Boolean(), nullable=False, server_default='0', default=False))
    op.create_index(op.f('ix_course_sandbox'), 'course', ['sandbox'], unique=False)

def downgrade():
    with op.batch_alter_table('course', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_course_sandbox')
        batch_op.drop_column('sandbox')