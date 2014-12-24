"""added rounds answers

Revision ID: 4667f38426eb
Revises: 380522bcdac1
Create Date: 2014-12-18 14:56:56.064146

"""

# revision identifiers, used by Alembic.
revision = '4667f38426eb'
down_revision = '380522bcdac1'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from acj.models import convention


def upgrade():
	op.add_column('PostsForAnswers', sa.Column('round', sa.Integer(), nullable=False, default='0', server_default='0'))
	populate = text(
		"UPDATE PostsForAnswers SET round ="
		"(SELECT custom.id FROM "
		"(SELECT a.id, sum(jcount) AS count "
		"FROM PostsForAnswers a, "
		"(SELECT ap.id, ap.postsforanswers_id1, ap.postsforanswers_id2, count(*) AS jcount "
		"FROM AnswerPairings ap "
		"JOIN Judgements j "
		"ON j.answerpairings_id = ap.id "
		"GROUP BY ap.id) AS ap "
		"WHERE a.id = ap.postsforanswers_id1 OR a.id = ap.postsforanswers_id2 "
		"GROUP BY a.id) custom "
		"WHERE PostsForAnswers.id = custom.id)"
	)
	op.get_bind().execute(populate)


def downgrade():
	with op.batch_alter_table('PostsForAnswers', naming_convention=convention) as batch_op:
		batch_op.drop_column('round')
