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


def upgrade():

    op.create_table('SelfEvaluationTypes',
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
        "INSERT INTO SelfEvaluationTypes (name) " +
        "VALUES ('No Comparison with Another Answer')"
    )
    op.get_bind().execute(insert)

    op.add_column(u'PostsForQuestions', sa.Column('selfevaltype_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'PostsForQuestions', 'SelfEvaluationTypes',
        ['selfevaltype_id'], ['id'], ondelete="CASCADE")

def downgrade():

    fq_name = text(
        "SELECT constraint_name FROM information_schema.key_column_usage " + \
        "WHERE table_name ='PostsForQuestions' and column_name = 'selfevaltype_id'"
    )
    conn = op.get_bind()
    res = conn.execute(fq_name)
    names = res.fetchall()
    for name in names:
        op.drop_constraint(name[0], 'PostsForQuestions', 'foreignkey')
    # drop key/index + column
    op.drop_index("selfevaltype_id", "PostsForQuestions")
    op.drop_column("PostsForQuestions", "selfevaltype_id")
    op.drop_table('SelfEvaluationTypes')

