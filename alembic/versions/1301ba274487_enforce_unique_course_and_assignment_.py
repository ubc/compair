"""enforce unique course and assignment grade constraints

Revision ID: 1301ba274487
Revises: d415a61d15ca
Create Date: 2016-11-23 18:35:02.187013

"""

# revision identifiers, used by Alembic.
revision = '1301ba274487'
down_revision = 'd415a61d15ca'

from alembic import op

from compair.models import convention

def upgrade():
    with op.batch_alter_table('assignment_grade', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('_unique_user_and_assignment', ['assignment_id', 'user_id'])

    with op.batch_alter_table('course_grade', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('_unique_user_and_course', ['course_id', 'user_id'])

def downgrade():
    with op.batch_alter_table('assignment_grade', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('_unique_user_and_assignment', type_='unique')

    with op.batch_alter_table('course_grade', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('_unique_user_and_course', type_='unique')