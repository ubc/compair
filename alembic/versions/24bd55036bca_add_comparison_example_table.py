"""Add comparison_example table

Revision ID: 24bd55036bca
Revises: fff3fc7f636a
Create Date: 2016-07-12 15:14:57.095400

"""

# revision identifiers, used by Alembic.
revision = '24bd55036bca'
down_revision = 'fff3fc7f636a'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.create_table('comparison_example',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('answer1_id', sa.Integer(), nullable=False),
        sa.Column('answer2_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer1_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answer2_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_comparison_example_active'), 'comparison_example', ['active'], unique=False)

    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('comparison_example_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_comparison_comparison_example_id_comparison_example',
            'comparison_example', ['comparison_example_id'], ['id'], ondelete="SET NULL")

def downgrade():
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_comparison_comparison_example_id_comparison_example', 'foreignkey')
        batch_op.drop_column('comparison_example_id')

    op.drop_table('comparison_example')