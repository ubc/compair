"""refactor self evaluation

Revision ID: 380522bcdac1
Revises: 472780bc3c62
Create Date: 2014-11-12 16:14:03.622271

"""

# revision identifiers, used by Alembic.
revision = '380522bcdac1'
down_revision = '472780bc3c62'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from acj.models import convention


def upgrade():
	op.create_table('PostsForQuestionsAndSelfEvaluationTypes',
					sa.Column('id', sa.Integer(), nullable=False),
					sa.Column('postsforquestions_id', sa.Integer(), nullable=False),
					sa.Column('selfevaluationtypes_id', sa.Integer(), nullable=False),
					sa.ForeignKeyConstraint(['postsforquestions_id'], ['PostsForQuestions.id'], ondelete='CASCADE'),
					sa.ForeignKeyConstraint(['selfevaluationtypes_id'], ['SelfEvaluationTypes.id'], ondelete='CASCADE'),
					sa.PrimaryKeyConstraint('id'),
					mysql_charset='utf8',
					mysql_collate='utf8_unicode_ci',
					mysql_engine='InnoDB'
	)

	# populate table above
	populate = text(
		"INSERT INTO PostsForQuestionsAndSelfEvaluationTypes (postsforquestions_id, selfevaluationtypes_id) " +
		"SELECT q.id, q.selfevaltype_id " +
		"FROM PostsForQuestions as q " +
		"WHERE q.selfevaltype_id IS NOT NULL"
	)
	op.get_bind().execute(populate)

	# drop selfevaltype_id foreign key
	with op.batch_alter_table('PostsForQuestions', naming_convention=convention) as batch_op:
		batch_op.drop_constraint('fk_PostsForQuestions_selfevaltype_id_SelfEvaluationTypes', 'foreignkey')
		# drop key/index + column
		#batch_op.drop_index("selfevaltype_id")
		batch_op.drop_column("selfevaltype_id")

	op.add_column('PostsForJudgements',
				  sa.Column('selfeval', sa.Boolean(), nullable=False, server_default='0', default=False))


# insert = text(
# "INSERT INTO SelfEvaluationTypes (name) " +
# "VALUES ('Comparison to a Similarly Scored Answer'), ('Comparison to a Higher Scored Answer')"
#)
#op.get_bind().execute(insert)

def downgrade():
	# insert selfevaltype_id column into PostsForQuestions table
	op.add_column(u'PostsForQuestions', sa.Column('selfevaltype_id', sa.Integer(), nullable=True))

	# populate the column - only populate the no comparison self evaluation type
	type = text(
		"SELECT id FROM SelfEvaluationTypes " +
		"WHERE name='No Comparison with Another Answer'"
	)
	conn = op.get_bind()
	res = conn.execute(type)
	selfevaltype = res.fetchall()

	populate = text(
		"UPDATE PostsForQuestions " +
		"SET selfevaltype_id = "
		"(SELECT qs.selfevaluationtypes_id " +
		"FROM PostsForQuestionsAndSelfEvaluationTypes qs "
		"WHERE PostsForQuestions.id = qs.postsforquestions_id " +
		"AND qs.selfevaluationtypes_id = " + str(selfevaltype[0][0]) + ')'
	)
	op.get_bind().execute(populate)

	with op.batch_alter_table('PostsForQuestions', naming_convention=convention) as batch_op:
		batch_op.create_foreign_key('fk_PostsForQuestions_selfevaltype_id_SelfEvaluationTypes', 'SelfEvaluationTypes',
									['selfevaltype_id'], ['id'], ondelete="CASCADE")


	with op.batch_alter_table('PostsForJudgements', naming_convention=convention) as batch_op:
		batch_op.drop_column('selfeval')

	op.drop_table('PostsForQuestionsAndSelfEvaluationTypes')


#drop = text(
#	"DELETE FROM SelfEvaluationTypes " +
#	"WHERE name='Comparison to a Similarly Scored Answer' or name='Comparison to a Higher Scored Answer'"
#)
#op.get_bind().execute(drop)

