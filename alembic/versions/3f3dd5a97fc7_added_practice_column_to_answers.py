"""Added practice column to answers

Revision ID: 3f3dd5a97fc7
Revises: 17b7bd2e218c
Create Date: 2016-08-19 12:55:40.174238

"""

# revision identifiers, used by Alembic.
revision = '3f3dd5a97fc7'
down_revision = '17b7bd2e218c'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('practice', sa.Boolean(), default=False, server_default='0', nullable=False))
    op.create_index(op.f('ix_answer_practice'), 'answer', ['practice'], unique=False)

    connection = op.get_bind()

    comparison_example_table = sa.table('comparison_example',
        sa.Column('answer1_id', sa.Integer),
        sa.Column('answer2_id', sa.Integer),
    )

    answer_table = sa.table('answer',
        sa.column('id', sa.Integer),
        sa.Column('practice', sa.Boolean)
    )

    answer_ids = set()
    for comparison_example in connection.execute(comparison_example_table.select()):
        answer_ids.add(comparison_example.answer1_id)
        answer_ids.add(comparison_example.answer2_id)

    answer_ids = list(answer_ids)
    if len(answer_ids) > 0:
        connection.execute(
            answer_table.update().where(
                answer_table.c.id.in_(answer_ids)
            ).values(
                practice=True
            )
        )

def downgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_answer_practice')
        batch_op.drop_column('practice')