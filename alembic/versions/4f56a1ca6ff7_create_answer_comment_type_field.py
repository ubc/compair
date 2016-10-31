"""create answer comment type field

Revision ID: 4f56a1ca6ff7
Revises: 4c4e55aabae6
Create Date: 2015-06-29 15:31:00.833331

"""

# revision identifiers, used by Alembic.

revision = '4f56a1ca6ff7'
down_revision = '4c4e55aabae6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from compair.models import convention


def upgrade():
    op.add_column(
        'AnswersAndComments',
        sa.Column('type', sa.SmallInteger(), nullable=False, server_default='0', default=0))
    # now we need to upgrade data
    update = text(
        # rewrite into subquery to support SQLite. need more testing to verify
        "UPDATE AnswersAndComments "
        "SET type = 1 "
        "WHERE evaluation = 0 AND selfeval = 0"
    )
    op.get_bind().execute(update)

def downgrade():
    with op.batch_alter_table('AnswersAndComments', naming_convention=convention) as batch_op:
        batch_op.drop_column('type')
