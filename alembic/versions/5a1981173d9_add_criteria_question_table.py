"""add criteria question table

Revision ID: 5a1981173d9
Revises: 14eb50b4c37
Create Date: 2014-10-17 13:18:36.314558

"""

# revision identifiers, used by Alembic.
revision = '5a1981173d9'
down_revision = '14eb50b4c37'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from compair.models import convention


def upgrade():
    # create CriteriaAndQuestions
    op.create_table(
        'CriteriaAndQuestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['criteria_id'], ['Criteria.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    # populate table with existing questions and their criteria
    insert = text(
        "INSERT INTO CriteriaAndQuestions (criteria_id, Questions_id, active) " +
        "SELECT c.id, q.id, cc.active " +
        "FROM Questions as q " +
        "JOIN Posts as p ON q.posts_id = p.id " +
        "JOIN CriteriaAndCourses as cc ON p.courses_id = cc.courses_id " +
        "JOIN Criteria as c ON cc.criteria_id = c.id "
    )
    op.get_bind().execute(insert)

    # Scores model - create criteriaandquestions_id column
    op.add_column('Scores', sa.Column('criteriaandquestions_id', sa.Integer(), nullable=True))
    # populate column with the scores' criteriaandquestions id
    update = text(
        # rewrite into subquery to support SQLite. need more testing to verify
        "UPDATE Scores "
        "SET criteriaandquestions_id = "
        "(SELECT cq.id FROM CriteriaAndQuestions cq "
        "JOIN Answers a ON a.questions_id = cq.questions_id "
        "JOIN CriteriaAndCourses c ON c.criteria_id = cq.criteria_id "
        "WHERE Scores.criteriaandcourses_id = c.id AND Scores.answers_id = a.id)"
        # "UPDATE Scores s " + \  # "JOIN PostsForAnswers a ON s.postsforanswers_id = a.id " + \
        # "JOIN CriteriaAndCourses c ON s.criteriaandcourses_id = c.id " + \
        # "JOIN CriteriaAndQuestions cq " + \
        # "ON a.questions_id = cq.questions_id AND c.criteria_id = cq.criteria_id " + \
        # "SET s.criteriaandquestions_id = cq.id"
    )
    op.get_bind().execute(update)
    with op.batch_alter_table('Scores', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_Scores_criteriaandquestions_id_CriteriaAndQuestions', 'CriteriaAndQuestions',
                                    ['criteriaandquestions_id'], ['id'], ondelete="CASCADE")
        batch_op.alter_column('criteriaandquestions_id', nullable=False, existing_type=sa.Integer())
        batch_op.drop_constraint('fk_Scores_criteriaandcourses_id_CriteriaAndCourses', 'foreignkey')
        batch_op.drop_column("criteriaandcourses_id")

    # Judgements model - create criteriaandquestions_id column
    op.add_column('Judgements', sa.Column('criteriaandquestions_id', sa.Integer(), nullable=True))
    # populate column with the judgements' criteriaandquestions_id
    update = text(
        # rewrite into subquery to support SQLite. need more testing to verify
        "UPDATE Judgements "
        "SET criteriaandquestions_id = "
        "(SELECT cq.id FROM CriteriaAndQuestions cq "
        "JOIN Answers a ON a.questions_id = cq.questions_id  "
        "JOIN CriteriaAndCourses c ON c.criteria_id = cq.criteria_id "
        "WHERE Judgements.answers_id_winner = a.id AND Judgements.criteriaandcourses_id = c.id)"
        # "UPDATE Judgements j " +   # "JOIN PostsForAnswers a ON j.postsforanswers_id_winner = a.id " +
        # "JOIN CriteriaAndCourses c ON j.criteriaandcourses_id = c.id " +
        # "JOIN CriteriaAndQuestions cq " +
        # "ON a.questions_id = cq.questions_id AND c.criteria_id = cq.criteria_id " +
        # "SET j.criteriaandquestions_id = cq.id"
    )
    op.get_bind().execute(update)
    with op.batch_alter_table('Judgements', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_Judgements_criteriaandquestions_id_CriteriaAndQuestions',
                                    'CriteriaAndQuestions',
                                    ['criteriaandquestions_id'], ['id'], ondelete="CASCADE")
        batch_op.alter_column('criteriaandquestions_id', nullable=False, existing_type=sa.Integer())
        batch_op.drop_constraint('fk_Judgements_criteriaandcourses_id_CriteriaAndCourses', 'foreignkey')
        # batch_op.drop_index("criteriaandcourses_id")
        batch_op.drop_column("criteriaandcourses_id")


def downgrade():
    # revert table Judgements
    op.add_column("Judgements", sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
    # populate column with the judgements' criteriaandcourses_id
    update = text(
        # rewrite into subquery to support SQLite. need more testing to verify
        "UPDATE Judgements "
        "SET criteriaandcourses_id = "
        "(SELECT cc.id FROM CriteriaAndCourses cc "
        "JOIN CriteriaAndQuestions cq ON cq.criteria_id = cc.criteria_id  "
        "JOIN Questions q ON cq.questions_id = q.id "
        "JOIN Posts p ON q.posts_id = p.id "
        "WHERE Judgements.criteriaandquestions_id = cq.id AND p.courses_id = cc.courses_id)"
        # "UPDATE Judgements j " + \
        # "JOIN CriteriaAndQuestions cq ON j.criteriaandquestions_id = cq.id " + \
        # "JOIN Questions q ON cq.questions_id = q.id " + \
        # "JOIN Posts p ON q.posts_id = p.id " + \
        # "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
        # "SET j.criteriaandcourses_id = cc.id"
    )
    op.get_bind().execute(update)
    with op.batch_alter_table('Judgements', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_Judgements_criteriaandcourses_id_CriteriaAndCourses', 'CriteriaAndCourses',
                                    ['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
        batch_op.alter_column('criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
        batch_op.drop_constraint('fk_Judgements_criteriaandquestions_id_CriteriaAndQuestions',
                                 'foreignkey')
        # batch_op.drop_index("criteriaandquestions_id")
        batch_op.drop_column("criteriaandquestions_id")

    # revert table Scores
    op.add_column('Scores', sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
    # populate column with the scores' criteriaandcourses_id
    update = text(
        # rewrite into subquery to support SQLite. need more testing to verify
        "UPDATE Scores "
        "SET criteriaandcourses_id = "
        "(SELECT cc.id FROM CriteriaAndCourses cc "
        "JOIN CriteriaAndQuestions cq ON cq.criteria_id = cc.criteria_id "
        "JOIN Questions q ON cq.questions_id = q.id "
        "JOIN Posts p ON q.posts_id = p.id "
        "WHERE Scores.criteriaandquestions_id = cq.id AND p.courses_id = cc.courses_id)"
        # "UPDATE Scores s " + \
        # "JOIN CriteriaAndQuestions cq ON s.criteriaandquestions_id = cq.id " + \
        # "JOIN Questions q ON cq.questions_id = q.id " + \
        # "JOIN Posts p ON q.posts_id = p.id " + \
        # "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
        # "SET s.criteriaandcourses_id = cc.id"
    )
    op.get_bind().execute(update)
    with op.batch_alter_table('Scores', naming_convention=convention) as batch_op:
        batch_op.create_foreign_key('fk_Scores_criteriaandcourses_id_CriteriaAndCourses', 'CriteriaAndCourses',
                                    ['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
        batch_op.alter_column('criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
        batch_op.drop_constraint('fk_Scores_criteriaandquestions_id_CriteriaAndQuestions', 'foreignkey')
        # batch_op.drop_index('criteriaandquestions_id')
        batch_op.drop_column('criteriaandquestions_id')

    # drop table CriteriaAndQuestions
    op.drop_table('CriteriaAndQuestions')
