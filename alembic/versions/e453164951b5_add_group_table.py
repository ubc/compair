"""Add group table

Revision ID: e453164951b5
Revises: 04529827d9af
Create Date: 2018-06-05 21:24:05.509185

"""

# revision identifiers, used by Alembic.
revision = 'e453164951b5'
down_revision = '04529827d9af'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType
from enum import Enum

from compair.models import convention

def upgrade():
    # STEP 1: add new tables and fields
    op.create_table('group',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.CHAR(length=22), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_group_active'), 'group', ['active'], unique=False)

    # (need to temporarily remove the answer user_id foreign key)
    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_answer_user_id_user', 'foreignkey')
    except sa.exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('answer') as batch_op:
            batch_op.drop_constraint('answer_ibfk_2', 'foreignkey')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
        batch_op.create_foreign_key('fk_answer_group_id_group', 'group', ['group_id'], ['id'], ondelete="SET NULL")

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_answer_user_id_user', 'user', ['user_id'], ['id'], ondelete="SET NULL")

    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('enable_group_answers', sa.Boolean(),
            nullable=False, default=False, server_default='0'))

    with op.batch_alter_table('user_course', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_user_course_group_id_group', 'group', ['group_id'], ['id'], ondelete="SET NULL")


def downgrade():
    # STEP 1: delete all answers without a user_id (group answers)

    answer_table = sa.table('answer',
        sa.column('id', sa.Integer), sa.column('user_id', sa.Integer)
    )

    connection = op.get_bind()
    connection.execute(
        answer_table.delete().where(answer_table.c.user_id == None)
    )

    # STEP 2: migrate the data
    with op.batch_alter_table('user_course', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_user_course_group_id_group', 'foreignkey')

    with op.batch_alter_table('user_course', naming_convention=convention) as batch_op:
        batch_op.drop_column('group_id')

    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('enable_group_answers')

    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
            batch_op.drop_constraint('fk_answer_user_id_user', 'foreignkey')
    except sa.exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('answer') as batch_op:
            batch_op.drop_constraint('answer_ibfk_2', 'foreignkey')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_answer_group_id_group', 'foreignkey')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('group_id')

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_answer_user_id_user', 'user', ['user_id'], ['id'], ondelete="CASCADE")

    op.drop_table('group')
