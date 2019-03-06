"""Add Caliper log table

Revision ID: 59646d2ad22c
Revises: b492a8f2132c
Create Date: 2018-07-26 14:53:48.707995

"""

# revision identifiers, used by Alembic.
revision = '59646d2ad22c'
down_revision = 'b492a8f2132c'

import uuid

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.create_table('caliper_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event', sa.Text(), nullable=True),
        sa.Column('transmitted', sa.Boolean(), nullable=False),
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
    op.create_index(op.f('ix_caliper_log_transmitted'), 'caliper_log', ['transmitted'], unique=False)

    with op.batch_alter_table('xapi_log', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('transmitted', sa.Boolean(), nullable=False, default=False, server_default='1'))
    op.create_index('ix_xapi_log_transmitted', 'xapi_log', ['transmitted'], unique=False)

    for table_name in ['answer', 'answer_comment', 'comparison']:
        with op.batch_alter_table(table_name, naming_convention=convention) as batch_op:
            batch_op.add_column(sa.Column('attempt_uuid', sa.CHAR(length=36), nullable=False, server_default=''))
            batch_op.add_column(sa.Column('attempt_started', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('attempt_ended', sa.DateTime(), nullable=True))


    connection = op.get_bind()
    # step 2, fill in attempt uuids
    for table_name in ['answer', 'answer_comment', 'comparison']:
        table = sa.table(table_name, sa.Column('id', sa.Integer()), sa.Column('attempt_uuid', sa.CHAR(36)))
        for record in connection.execute(table.select()):
            connection.execute(
                table.update()
                .where(table.c.id == record.id)
                .values(attempt_uuid=str(uuid.uuid4()))
            )

def downgrade():
    for table in ['answer', 'answer_comment', 'comparison']:
        with op.batch_alter_table(table, naming_convention=convention) as batch_op:
            batch_op.drop_column('attempt_ended')
            batch_op.drop_column('attempt_started')
            batch_op.drop_column('attempt_uuid')

    with op.batch_alter_table('xapi_log', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_xapi_log_transmitted')
        batch_op.drop_column('transmitted')

    op.drop_table('caliper_log')
