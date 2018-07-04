"""Allow instructor answers to be included in comparisons

Revision ID: 2561c39ac4d9
Revises: f6145781f130
Create Date: 2017-12-06 21:07:23.219244

"""

# revision identifiers, used by Alembic.
revision = '2561c39ac4d9'
down_revision = 'f6145781f130'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from compair.models import convention

def upgrade():
    # add a new "comparable" column. default as true
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('comparable', sa.Integer(), nullable=False, default=True, server_default='1'))

    # Patch existing answers from instructors and TAs as non-comparable.
    # Note that existing answers from sys admin are considered comparable (i.e. no need to patch).
    # sqlite doesn't support in-clause with multiple columns...
    # update = text(
    #     "UPDATE answer SET comparable = 0 "
    #     "WHERE (assignment_id, user_id) IN ( "
    #     "  SELECT a.id, uc.user_id "
    #     "  FROM user_course uc "
    #     "  JOIN assignment a "
    #     "    ON a.course_id = uc.course_id "
    #     "  WHERE uc.course_role IN ('Instructor', 'Teaching Assistant'))"
    # )
    # ... use a potentially slower query
    update = text(
        "UPDATE answer SET comparable = 0 "
        "WHERE EXISTS ( "
        "  SELECT 1 "
        "  FROM user_course "
        "  JOIN assignment "
        "    ON assignment.course_id = user_course.course_id "
        "  WHERE "
        "    assignment.id = answer.assignment_id "
        "    AND user_course.user_id = answer.user_id "
        "    AND user_course.course_role IN ('Instructor', 'Teaching Assistant'))"
    )
    op.get_bind().execute(update)

def downgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_column('comparable')
