"""Add assignment_grade and course_grade

Revision ID: ad3d3931f78b
Revises: 2ba873cb8692
Create Date: 2016-09-27 16:54:17.194750

"""

# revision identifiers, used by Alembic.
revision = 'ad3d3931f78b'
down_revision = '2ba873cb8692'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.create_table('course_grade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Float(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.create_table('assignment_grade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Float(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    op.add_column('assignment', sa.Column('answer_grade_weight', sa.Integer(), server_default='1', nullable=False))
    op.add_column('assignment', sa.Column('comparison_grade_weight', sa.Integer(), server_default='1', nullable=False))
    op.add_column('assignment', sa.Column('self_evaluation_grade_weight', sa.Integer(), server_default='1', nullable=False))

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('self_evaluation_grade_weight')
        batch_op.drop_column('comparison_grade_weight')
        batch_op.drop_column('answer_grade_weight')

    op.drop_table('assignment_grade')
    op.drop_table('course_grade')
