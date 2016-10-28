"""added criteria answerpairing

Revision ID: ac2bd4b2c95
Revises: 4667f38426eb
Create Date: 2014-12-23 15:28:26.939498

"""

# revision identifiers, used by Alembic.
revision = 'ac2bd4b2c95'
down_revision = '4667f38426eb'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from compair.models import convention


def upgrade():
    op.add_column('AnswerPairings', sa.Column('criteriaandquestions_id', sa.Integer(), nullable=True))
    update = text(
        "UPDATE AnswerPairings SET criteriaandquestions_id = "
        "(SELECT criteria.id FROM "
        "(SELECT q.id AS questionId, cq.id "
        "FROM Questions q "
        "JOIN CriteriaAndQuestions cq "
        "ON cq.id = (SELECT id "
        "FROM CriteriaAndQuestions c "
        "WHERE c.questions_id = q.id AND cq.active = 1  LIMIT 1)) criteria "
        "WHERE AnswerPairings.questions_id = criteria.questionId)"
    )
    op.get_bind().execute(update)

    with op.batch_alter_table('AnswerPairings', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_AnswerPairings_criteriaandquestions_id_CriteriaAndQuestions',
                                    'CriteriaAndQuestions',
                                    ['criteriaandquestions_id'], ['id'], ondelete="CASCADE")


def downgrade():
    with op.batch_alter_table('AnswerPairings', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_AnswerPairings_criteriaandquestions_id_CriteriaAndQuestions',
                                 'foreignkey')
        # drop key/index + column
        # batch_op.drop_index("criteriaandpostsforquestions_id")
        batch_op.drop_column('criteriaandquestions_id')
