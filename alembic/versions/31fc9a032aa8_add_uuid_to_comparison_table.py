"""Add uuid to comparison table and add xpai_log table

Revision ID: 31fc9a032aa8
Revises: 1301ba274487
Create Date: 2016-11-10 23:31:36.173311

"""

# revision identifiers, used by Alembic.
revision = '31fc9a032aa8'
down_revision = '1301ba274487'

from alembic import op
import sqlalchemy as sa
import uuid
import base64

from compair.models import convention

def upgrade():
    # step 1, add new uuid column
    op.add_column('comparison', sa.Column('uuid', sa.CHAR(22), nullable=False, server_default=''))

    connection = op.get_bind()
    # step 2, fill in unique uuids (base64 url safe strings)
    comparison_table = sa.table('comparison', sa.Column('id', sa.Integer()), sa.Column('uuid', sa.CHAR(22)))
    for record in connection.execute(comparison_table.select()):
        connection.execute(
            comparison_table.update()
            .where(comparison_table.c.id == record.id)
            .values(uuid=base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').replace('=', ''))
        )

    # step 3, apply unique constraint on generated table
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint("uq_comparison_uuid", ['uuid'])

    # step 4 create xapi_log table
    op.create_table('xapi_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('statement', sa.Text(), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('xapi_log')

    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq_comparison_uuid", type_='unique')
        batch_op.drop_column('uuid')
