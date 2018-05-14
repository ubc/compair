"""Modify score table

Revision ID: aa532b17a272
Revises: 3112cccea8d5
Create Date: 2017-01-12 01:03:08.157356

"""

# revision identifiers, used by Alembic.
revision = 'aa532b17a272'
down_revision = '3112cccea8d5'

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy_enum34 import EnumType
from enum import Enum

from compair.models import convention

class ScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating"
    true_skill = "true_skill_rating"

def upgrade():
    # Rename score table to answer_criterion_score
    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('score', naming_convention=convention) as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('fk_score_assignment_id_assignment', 'foreignkey')
            batch_op.drop_constraint('fk_score_answer_id_answer', 'foreignkey')
            batch_op.drop_constraint('fk_score_criterion_id_criterion', 'foreignkey')
    except sa.exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('score') as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('score_ibfk_1', 'foreignkey')
            batch_op.drop_constraint('score_ibfk_2', 'foreignkey')
            batch_op.drop_constraint('score_ibfk_3', 'foreignkey')

    op.rename_table('score', 'answer_criterion_score')

    with op.batch_alter_table('answer_criterion_score', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_answer_criterion_score_assignment_id_assignment', 'assignment', ['assignment_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_answer_criterion_score_answer_id_answer', 'answer', ['answer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_answer_criterion_score_criterion_id_criterion', 'criterion', ['criterion_id'], ['id'], ondelete="CASCADE")

    # create new answer_score table
    answer_score_table = op.create_table('answer_score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('scoring_algorithm', EnumType(ScoringAlgorithm), nullable=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('variable1', sa.Float(), nullable=True),
        sa.Column('variable2', sa.Float(), nullable=True),
        sa.Column('rounds', sa.Integer(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False),
        sa.Column('loses', sa.Integer(), nullable=False),
        sa.Column('opponents', sa.Integer(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('answer_id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_answer_score_score'), 'answer_score', ['score'], unique=False)

    # migrate aggregate data from answer_criteria_score to answer_score
    answer_criterion_score_table = sa.table('answer_criterion_score',
        sa.column('id', sa.Integer),
        sa.Column('assignment_id', sa.Integer), sa.Column('answer_id', sa.Integer), sa.Column('criterion_id', sa.Integer),
        sa.Column('scoring_algorithm', EnumType(ScoringAlgorithm)),
        sa.Column('score', sa.Float), sa.Column('variable1', sa.Float), sa.Column('variable2', sa.Float),
        sa.Column('rounds', sa.Integer), sa.Column('wins', sa.Integer), sa.Column('loses', sa.Integer), sa.Column('opponents', sa.Integer)
    )

    connection = op.get_bind()

    answer_scores = {}
    for answer_criterion_score in connection.execute(answer_criterion_score_table.select()):
        answer_scores.setdefault(answer_criterion_score.answer_id, {
            'assignment_id': answer_criterion_score.assignment_id,
            'answer_id': answer_criterion_score.answer_id,
            'scoring_algorithm': answer_criterion_score.scoring_algorithm,
            'rounds': answer_criterion_score.rounds,
            'wins': answer_criterion_score.wins,
            'loses': answer_criterion_score.loses,
            'opponents': answer_criterion_score.opponents,
            # to be averaged
            'score': [],
            'variable1': [],
            'variable2': []
        })


        answer_scores[answer_criterion_score.answer_id]['score'].append(answer_criterion_score.score)
        if answer_criterion_score.variable1:
            answer_scores[answer_criterion_score.answer_id]['variable1'].append(answer_criterion_score.variable1)
        if answer_criterion_score.variable2:
            answer_scores[answer_criterion_score.answer_id]['variable2'].append(answer_criterion_score.variable2)

    for answer_id, score in answer_scores.items():
        average_score = sum(score['score'])/float(len(score['score'])) if len(score['score']) else 0
        average_variable1 = sum(score['variable1'])/float(len(score['variable1'])) if len(score['variable1']) else None
        average_variable2 = sum(score['variable2'])/float(len(score['variable2'])) if len(score['variable2']) else None

        connection.execute(
            answer_score_table.insert().values(
                assignment_id=score['assignment_id'], answer_id=score['answer_id'],
                scoring_algorithm=score['scoring_algorithm'],
                rounds=score['rounds'], wins=score['wins'], loses=score['loses'], opponents=score['opponents'],
                score=average_score, variable1=average_variable1, variable2=average_variable2,
                modified=datetime.utcnow(), created=datetime.utcnow()
            )
        )


def downgrade():
    # no data to migrate

    # drop answer_score table
    op.drop_index(op.f('ix_answer_score_score'), table_name='answer_score')
    op.drop_table('answer_score')

    # Rename answer_criterion_score table to score
    with op.batch_alter_table('answer_criterion_score', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_answer_criterion_score_assignment_id_assignment', 'foreignkey')
        batch_op.drop_constraint('fk_answer_criterion_score_answer_id_answer', 'foreignkey')
        batch_op.drop_constraint('fk_answer_criterion_score_criterion_id_criterion', 'foreignkey')

    op.rename_table('answer_criterion_score', 'score')

    with op.batch_alter_table('score', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_score_assignment_id_assignment', 'assignment', ['assignment_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_score_answer_id_answer', 'answer', ['answer_id'], ['id'], ondelete="CASCADE")
        batch_op.create_foreign_key('fk_score_criterion_id_criterion', 'criterion', ['criterion_id'], ['id'], ondelete="CASCADE")