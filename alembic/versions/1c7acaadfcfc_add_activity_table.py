"""Add activity table

Revision ID: 1c7acaadfcfc
Revises: None
Create Date: 2014-09-08 00:46:46.207694

"""

# revision identifiers, used by Alembic.
revision = '1c7acaadfcfc'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'Activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=True),
        sa.Column('courses_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('event', sa.String(length=50), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('Activities')
