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

from acj.models import convention


def upgrade():
	# create CriteriaAndPostsForQuestions
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

	# Scores model - create criteriaandpostsforquestions_id column
	op.add_column('Scores', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=True))
	# populate column with the scores' criteriaandpostsforquestions id
	update = text(  # rewrite into subquery to support SQLite. need more testing to verify
					"UPDATE Scores "
					"SET criteriaandpostsforquestions_id = "
					"(SELECT cq.id FROM CriteriaAndPostsForQuestions cq "
					"JOIN PostsForAnswers a ON Scores.postsforanswers_id = a.id "
					"JOIN CriteriaAndCourses c ON Scores.criteriaandcourses_id = c.id "
					"WHERE a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id)"
					# "UPDATE Scores s " + \  # "JOIN PostsForAnswers a ON s.postsforanswers_id = a.id " + \
					# "JOIN CriteriaAndCourses c ON s.criteriaandcourses_id = c.id " + \
					# "JOIN CriteriaAndPostsForQuestions cq " + \
					# "ON a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id " + \
					# "SET s.criteriaandpostsforquestions_id = cq.id"
	)
	op.get_bind().execute(update)
	with op.batch_alter_table('Scores', naming_convention=convention) as batch_op:
		batch_op.create_foreign_key('fk_criteriaandpostsforquestions_id', 'CriteriaAndPostsForQuestions',
									['criteriaandpostsforquestions_id'], ['id'], ondelete="CASCADE")
		batch_op.alter_column('criteriaandpostsforquestions_id', nullable=False, existing_type=sa.Integer())
		# batch_op.drop_constraint('criteriaandcourses_id', 'foreignkey')
		batch_op.drop_column("criteriaandcourses_id")

	# Judgements model - create criteriaandpostsforquestions_id column
	op.add_column('Judgements', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=True))
	# populate column with the judgements' criteriaandpostsforquestions_id
	update = text(  # rewrite into subquery to support SQLite. need more testing to verify
					"UPDATE Judgements "
					"SET criteriaandpostsforquestions_id = "
					"(SELECT cq.id FROM CriteriaAndPostsForQuestions cq "
					"JOIN PostsForAnswers a ON Judgements.postsforanswers_id_winner = a.id  "
					"JOIN CriteriaAndCourses c ON Judgements.criteriaandcourses_id = c.id  "
					"WHERE a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id)"
					# "UPDATE Judgements j " +   # "JOIN PostsForAnswers a ON j.postsforanswers_id_winner = a.id " +
					# "JOIN CriteriaAndCourses c ON j.criteriaandcourses_id = c.id " +
					# "JOIN CriteriaAndPostsForQuestions cq " +
					# "ON a.postsforquestions_id = cq.postsforquestions_id AND c.criteria_id = cq.criteria_id " +
					# "SET j.criteriaandpostsforquestions_id = cq.id"
	)
	op.get_bind().execute(update)
	with op.batch_alter_table('Judgements', naming_convention=convention) as batch_op:
		batch_op.create_foreign_key('fk_criteriaandpostsforquestions_id', 'CriteriaAndPostsForQuestions',
									['criteriaandpostsforquestions_id'], ['id'], ondelete="CASCADE")
		batch_op.alter_column('criteriaandpostsforquestions_id', nullable=False, existing_type=sa.Integer())
		# batch_op.drop_index("criteriaandcourses_id")
		batch_op.drop_column("criteriaandcourses_id")


def downgrade():
	# revert table Judgements
	op.add_column("Judgements", sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
	# populate column with the judgements' criteriaandcourses_id
	update = text(  # rewrite into subquery to support SQLite. need more testing to verify
					"UPDATE Judgements "
					"SET criteriaandcourses_id = "
					"(SELECT cc.id FROM CriteriaAndCourses cc "
					"JOIN CriteriaAndPostsForQuestions cq ON Judgements.criteriaandpostsforquestions_id = cq.id "
					"JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id "
					"JOIN Posts p ON q.posts_id = p.id "
					"WHERE cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id)"
					# "UPDATE Judgements j " + \
					# "JOIN CriteriaAndPostsForQuestions cq ON j.criteriaandpostsforquestions_id = cq.id " + \
					# "JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id " + \
					# "JOIN Posts p ON q.posts_id = p.id " + \
					# "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
					# "SET j.criteriaandcourses_id = cc.id"
	)
	op.get_bind().execute(update)
	with op.batch_alter_table('Judgements', naming_convention=convention) as batch_op:
		batch_op.create_foreign_key('fk_criteriaandcourses_id', 'CriteriaAndCourses',
									['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
		batch_op.alter_column('criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
		batch_op.drop_constraint('fk_Judgements_criteriaandpostsforquestions_id_CriteriaAndPostsForQuestions',
								 'foreignkey')
		# batch_op.drop_index("criteriaandpostsforquestions_id")
		batch_op.drop_column("criteriaandpostsforquestions_id")

	# revert table Scores
	op.add_column('Scores', sa.Column('criteriaandcourses_id', sa.Integer(), nullable=True))
	# populate column with the scores' criteriaandcourses_id
	update = text(  # rewrite into subquery to support SQLite. need more testing to verify
					"UPDATE Scores "
					"SET criteriaandcourses_id = "
					"(SELECT cc.id FROM CriteriaAndCourses cc "
					"JOIN CriteriaAndPostsForQuestions cq ON Scores.criteriaandpostsforquestions_id = cq.id "
					"JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id "
					"JOIN Posts p ON q.posts_id = p.id "
					"WHERE cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id)"  # "UPDATE Scores s " + \
					# "JOIN CriteriaAndPostsForQuestions cq ON s.criteriaandpostsforquestions_id = cq.id " + \
					# "JOIN PostsForQuestions q ON cq.postsforquestions_id = q.id " + \
					# "JOIN Posts p ON q.posts_id = p.id " + \
					# "JOIN CriteriaAndCourses cc ON cq.criteria_id = cc.criteria_id AND p.courses_id = cc.courses_id " + \
					# "SET s.criteriaandcourses_id = cc.id"
	)
	op.get_bind().execute(update)
	with op.batch_alter_table('Scores', naming_convention=convention) as batch_op:
		batch_op.create_foreign_key('fk_criteriaandcourses_id', 'CriteriaAndCourses',
									['criteriaandcourses_id'], ['id'], ondelete="CASCADE")
		batch_op.alter_column('criteriaandcourses_id', nullable=False, existing_type=sa.Integer())
		batch_op.drop_constraint('fk_Scores_criteriaandpostsforquestions_id_CriteriaAndPostsForQuestions', 'foreignkey')
		# batch_op.drop_index('criteriaandpostsforquestions_id')
		batch_op.drop_column('criteriaandpostsforquestions_id')

	# drop table CriteriaAndPostsForQuestions
	op.drop_table('CriteriaAndPostsForQuestions')