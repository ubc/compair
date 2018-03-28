"""refactor group members table

Revision ID: 14eb50b4c37
Revises: c9ad3551e18
Create Date: 2014-10-14 09:23:28.962011

"""

# revision identifiers, used by Alembic.
revision = '14eb50b4c37'
down_revision = 'c9ad3551e18'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('GroupsAndCoursesAndUsers')
    op.create_table(
        'GroupsAndUsers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('groups_id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['groups_id'], ['Groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('groups_id', 'users_id', name='_unique_group_and_user'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table("GroupsAndUsers")
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
