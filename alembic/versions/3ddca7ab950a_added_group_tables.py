"""Added group tables

Revision ID: 3ddca7ab950a
Revises: 2b8a3bb24e9a
Create Date: 2014-10-03 17:27:56.553932

"""

# revision identifiers, used by Alembic.
revision = '3ddca7ab950a'
down_revision = '2b8a3bb24e9a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'Groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_table(
        'GroupsAndCoursesAndUsers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('groups_id', sa.Integer(), nullable=False),
        sa.Column('coursesandusers_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['coursesandusers_id'], ['CoursesAndUsers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['groups_id'], ['Groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('groups_id', 'coursesandusers_id', name='_unique_group_and_user'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('GroupsAndCoursesAndUsers')
    op.drop_table('Groups')
