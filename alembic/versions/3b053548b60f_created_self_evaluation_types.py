"""created self-evaluation types

Revision ID: 3b053548b60f
Revises: 5a1981173d9
Create Date: 2014-10-30 09:40:47.093018

"""

# revision identifiers, used by Alembic.
revision = '3b053548b60f'
down_revision = '5a1981173d9'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from compair.models import convention


def upgrade():
    op.create_table(
        'SelfEvalTypes',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    # populate table with a self evaluation type
    insert = text(
        "INSERT INTO SelfEvalTypes (name) " +
        "VALUES ('No Comparison with Another Answer')"
    )
    op.get_bind().execute(insert)

    with op.batch_alter_table('Questions', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('selfevaltype_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('Questions', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key(
            'fk_Questions_selfevaltype_id_SelfEvalTypes', 'SelfEvalTypes',
            ['selfevaltype_id'], ['id'], ondelete="CASCADE")


def downgrade():
    with op.batch_alter_table('Questions', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_Questions_selfevaltype_id_SelfEvalTypes', type_='foreignkey')
        # drop key/index + column
        batch_op.drop_column("selfevaltype_id")
    # batch_op.drop_index("selfevaltype_id")

    op.drop_table('SelfEvalTypes')
