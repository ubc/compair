"""remove assignment_comment table

Revision ID: 4593a30102c1
Revises: 0a1ad609fc0a
Create Date: 2018-03-21 19:00:15.799560

"""

# revision identifiers, used by Alembic.
revision = '4593a30102c1'
down_revision = '0a1ad609fc0a'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.drop_table('assignment_comment')


def downgrade():
    op.create_table('assignment_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(),nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('uuid', sa.CHAR(length=22), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('uuid'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )