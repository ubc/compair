"""Add assignment ending notification

Revision ID: 8387e6236c72
Revises: 4670092712d7
Create Date: 2019-02-05 19:41:47.028857

"""

# revision identifiers, used by Alembic.
revision = '8387e6236c72'
down_revision = '4670092712d7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'assignment_notification',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_assignment_notification'), 'assignment_notification', ['assignment_id', 'user_id', 'notification_type'], unique=False)

def downgrade():
    op.drop_table('assignment_notification')
