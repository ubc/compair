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


def upgrade():
    #### create CriteriaAndPostsForQuestions
    op.create_table('CriteriaAndPostsForQuestions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('criteria_id', sa.Integer(), nullable=False),
    sa.Column('postsforquestions_id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['criteria_id'], ['Criteria.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['postsforquestions_id'], ['PostsForQuestions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_charset='utf8',
    mysql_collate='utf8_unicode_ci',
    mysql_engine='InnoDB'
    )

    # populate table with existing questions and their criteria
    insert = text(
        "INSERT INTO CriteriaAndPostsForQuestions (criteria_id, postsforquestions_id, active) " +
        "SELECT c.id, q.id, cc.active " +
        "FROM PostsForQuestions as q " +
        "JOIN Posts as p ON q.posts_id = p.id " +
        "JOIN CriteriaAndCourses as cc ON p.courses_id = cc.courses_id " +
        "JOIN Criteria as c ON cc.criteria_id = c.id "
    )
    op.get_bind().execute(insert)

    #### Scores model - create criteriaandpostsforquestions_id column
    op.add_column('Scores', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=True))
    # populate column with the scores' criteriaandpostsforquestions id
    update = text(
        "UPDATE Scores s " + \
        "JOIN PostsForAnswers a ON s.postsforanswers_id = a.id " + \
        "JOIN CriteriaAndCourses c ON s.criteriaandcourses_id = c.id " + \
        "JOIN CriteriaAndPostsForQuestions cq " + \
        "ON a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id " + \
        "SET s.criteriaandpostsforquestions_id = cq.id"
    )
    op.get_bind().execute(update)
    op.create_foreign_key(None, 'Scores', 'CriteriaAndPostsForQuestions',
        ['criteriaandpostsforquestions_id'], ['id'], ondelete="CASCADE")
    op.alter_column('Scores', 'criteriaandpostsforquestions_id', nullable=False, existing_type=sa.Integer())
    # drop criteriaandcourses_id - drop foreign key
    fq_name = text(
        "SELECT constraint_name FROM information_schema.key_column_usage " + \
        "WHERE table_name ='Scores' and column_name = 'criteriaandcourses_id'"
    )
    conn = op.get_bind()
    res = conn.execute(fq_name)
    names = res.fetchall()
    for name in names:
        op.drop_constraint(name[0], 'Scores', 'foreignkey')
    # drop key/index + column
    op.drop_index("criteriaandcourses_id", "Scores")
    op.drop_column("Scores", "criteriaandcourses_id")

    #### Judgements model - create criteriaandpostsforquestions_id column
    op.add_column('Judgements', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=True))
    # populate column with the judgements' criteriaandpostsforquestions_id
    update = text(
        "UPDATE Judgements j " + \
        "JOIN PostsForAnswers a ON j.postsforanswers_id_winner = a.id " + \
        "JOIN CriteriaAndCourses c ON j.criteriaandcourses_id = c.id " + \
        "JOIN CriteriaAndPostsForQuestions cq " + \
        "ON a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id " + \
        "SET j.criteriaandpostsforquestions_id = cq.id"
    )
    op.get_bind().execute(update)
    op.create_foreign_key(None, 'Judgements', 'CriteriaAndPostsForQuestions',
        ['criteriaandpostsforquestions_id'], ['id'], ondelete="CASCADE")
    op.alter_column('Judgements', 'criteriaandpostsforquestions_id', nullable=False, existing_type=sa.Integer())
    # drop criteriaandcourses_id - drop foreign key
    fq_name = text(
        "SELECT constraint_name FROM information_schema.key_column_usage " + \
        "WHERE table_name ='Judgements' and column_name = 'criteriaandcourses_id'"
    )
    conn = op.get_bind()
    res = conn.execute(fq_name)
    names = res.fetchall()
    for name in names:
        op.drop_constraint(name[0], 'Judgements', 'foreignkey')
    # drop key/index + column
    op.drop_index("criteriaandcourses_id", "Judgements")
    op.drop_column("Judgements", "criteriaandcourses_id")

def downgrade():

    #### revert table Judgements
    op.add_column("Judgements", sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
    # populate column with the judgements' criteriaandcourses_id
    update = text(
        "UPDATE Judgements j " + \
        "JOIN CriteriaAndPostsForQuestions cq ON j.criteriaandpostsforquestions_id = cq.id " + \
        "JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id " + \
        "JOIN Posts p ON q.posts_id = p.id " + \
        "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
        "SET j.criteriaandcourses_id = cc.id"
    )
    op.get_bind().execute(update)
    op.create_foreign_key(None, 'Judgements', 'CriteriaAndCourses',
         ['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
    op.alter_column('Judgements', 'criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
    # drop criteriaandpostsforquestions_id - drop foreign key
    fq_name = text(
        "SELECT constraint_name FROM information_schema.key_column_usage " + \
        "WHERE table_name ='Judgements' and column_name = 'criteriaandpostsforquestions_id'"
    )
    conn = op.get_bind()
    res = conn.execute(fq_name)
    names = res.fetchall()
    for name in names:
        op.drop_constraint(name[0], 'Judgements', 'foreignkey')
    # drop key/index + column
    op.drop_index("criteriaandpostsforquestions_id", "Judgements")
    op.drop_column("Judgements", "criteriaandpostsforquestions_id")

    #### revert table Scores
    op.add_column('Scores', sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
    # populate column with the scores' criteriaandcourses_id
    update = text(
        "UPDATE Scores s " + \
        "JOIN CriteriaAndPostsForQuestions cq ON s.criteriaandpostsforquestions_id = cq.id " + \
        "JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id " + \
        "JOIN Posts p ON q.posts_id = p.id " + \
        "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
        "SET s.criteriaandcourses_id = cc.id"
    )
    op.get_bind().execute(update)
    op.create_foreign_key(None, 'Scores', 'CriteriaAndCourses',
        ['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
    op.alter_column('Scores', 'criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
    # drop criteriaandpostsforquestions_id - drop foreign key
    fq_name = text(
        "SELECT constraint_name FROM information_schema.key_column_usage " + \
        "WHERE table_name ='Scores' and column_name = 'criteriaandpostsforquestions_id'"
    )
    conn = op.get_bind()
    res = conn.execute(fq_name)
    names = res.fetchall()
    for name in names:
        op.drop_constraint(name[0], 'Scores', 'foreignkey')
    # drop key/index + column
    op.drop_index("criteriaandpostsforquestions_id", "Scores")
    op.drop_column("Scores", "criteriaandpostsforquestions_id")

    #### drop table CriteriaAndPostsForQuestions
    op.drop_table('CriteriaAndPostsForQuestions')