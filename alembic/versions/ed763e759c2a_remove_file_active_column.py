"""Remove file active column

Revision ID: ed763e759c2a
Revises: 622121ae2f36
Create Date: 2017-02-08 21:07:33.579874

"""

# revision identifiers, used by Alembic.
revision = 'ed763e759c2a'
down_revision = '622121ae2f36'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_file_active')
        batch_op.drop_column('active')

    op.create_index(op.f('ix_answer_draft'), 'answer', ['draft'], unique=False)
    op.create_index(op.f('ix_answer_comment_draft'), 'answer_comment', ['draft'], unique=False)


def downgrade():
    with op.batch_alter_table('answer_comment', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_answer_comment_draft')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_answer_draft')

    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), default=True, server_default='1', nullable=False))
    op.create_index(op.f('ix_file_active'), 'file', ['active'], unique=False)
