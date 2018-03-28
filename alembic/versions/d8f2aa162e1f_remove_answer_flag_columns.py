"""remove answer flag columns

Revision ID: d8f2aa162e1f
Revises: 6b69e8e22dfb
Create Date: 2018-03-21 19:20:16.395313

"""

# revision identifiers, used by Alembic.
revision = 'd8f2aa162e1f'
down_revision = '6b69e8e22dfb'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import exc

from compair.models import convention

def upgrade():
    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_answer_flagger_user_id_user', 'foreignkey')
    except exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('answer') as batch_op:
            batch_op.drop_constraint('answer_ibfk_4', 'foreignkey')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_column('flagger_user_id')
        batch_op.drop_column('flagged')


def downgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('flagged', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('flagger_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_answer_flagger_user_id_user',
            'user', ['flagger_user_id'], ['id'], ondelete="SET NULL")
