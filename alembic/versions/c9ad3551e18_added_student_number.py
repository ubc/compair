"""added student number

Revision ID: c9ad3551e18
Revises: 3ddca7ab950a
Create Date: 2014-10-09 09:20:43.891993

"""

# revision identifiers, used by Alembic.
import logging

revision = 'c9ad3551e18'
down_revision = '3ddca7ab950a'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    op.add_column('Users', sa.Column('student_no', sa.String(length=50), nullable=True))
    with op.batch_alter_table('Users', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('uq_Users_student_no', ['student_no'])


def downgrade():
    try:
        with op.batch_alter_table('Users', naming_convention=convention) as batch_op:
            # it seems alembic couldn't drop unique constraint for sqlite
            batch_op.drop_constraint('uq_Users_student_no', type_='unique')
    except ValueError:
        logging.warning('Drop unique constraint is not support for SQLite, dropping uq_Users_student_no ignored!')

    with op.batch_alter_table('Users', naming_convention=convention) as batch_op:
        batch_op.drop_column('student_no')
