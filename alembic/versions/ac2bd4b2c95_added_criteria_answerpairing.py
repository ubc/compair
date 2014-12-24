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


def upgrade():

	#op.add_column('AnswerPairings', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=False))
	op.add_column('AnswerPairings', sa.Column('criteriaandpostsforquestions_id', sa.Integer(), nullable=True))
	update = text(
		"UPDATE AnswerPairings ap " +
		"JOIN " +
		"(SELECT q.id as questionId, cq.id " +
		"FROM PostsForQuestions q " +
		"JOIN CriteriaAndPostsForQuestions cq " +
		"ON cq.id = (SELECT id " +
		"FROM CriteriaAndPostsForQuestions c " +
		"WHERE c.postsforquestions_id = q.id AND cq.active = True " +
		"LIMIT 1)) criteria " +
		"ON ap.postsforquestions_id = criteria.questionId " +
		"SET ap.criteriaandpostsforquestions_id = criteria.id"
	)
	op.get_bind().execute(update)
	op.create_foreign_key(None, 'AnswerPairings', 'CriteriaAndPostsForQuestions',
		['criteriaandpostsforquestions_id'], ['id'], ondelete="CASCADE")

def downgrade():

	fq_name = text(
		"SELECT constraint_name FROM information_schema.key_column_usage " + \
		"WHERE table_name ='AnswerPairings' and column_name = 'criteriaandpostsforquestions_id'"
	)
	conn = op.get_bind()
	res = conn.execute(fq_name)
	names = res.fetchall()
	for name in names:
		op.drop_constraint(name[0], 'AnswerPairings', 'foreignkey')
	# drop key/index + column
	op.drop_index("criteriaandpostsforquestions_id", "AnswerPairings")
	op.drop_column('AnswerPairings', 'criteriaandpostsforquestions_id')

