"""added selfeval flags to comments

Revision ID: 472780bc3c62
Revises: 3b053548b60f
Create Date: 2014-10-30 16:31:09.871401

"""

# revision identifiers, used by Alembic.
revision = '472780bc3c62'
down_revision = '3b053548b60f'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    with op.batch_alter_table('AnswersAndComments', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('evaluation', sa.Boolean(), nullable=False, server_default='0', default=False))
        batch_op.add_column(sa.Column('selfeval', sa.Boolean(), nullable=False, server_default='0', default=False))


def downgrade():
    with op.batch_alter_table('AnswersAndComments', naming_convention=convention) as batch_op:
        batch_op.drop_column('selfeval')
        batch_op.drop_column('evaluation')
