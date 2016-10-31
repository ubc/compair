"""add answer_id and criteriaquestion_id constraint to score table

Revision ID: 48e3b9d1750b
Revises: 4f56a1ca6ff7
Create Date: 2015-08-28 23:17:44.797369

"""

# revision identifiers, used by Alembic.
import logging

import sqlalchemy as sa
from sqlalchemy import UniqueConstraint, exc

from compair.models import convention

revision = '48e3b9d1750b'
down_revision = '4f56a1ca6ff7'

from alembic import op


def upgrade():
    with op.batch_alter_table('Scores', naming_convention=convention) as batch_op:
        # this query will delete the duplicate scores and keep the one with max round number
        query = ('DELETE FROM Scores WHERE id IN (' +
                 'SELECT id FROM (SELECT * FROM Scores) as s ' +
                 'JOIN (' +
                 'SELECT MAX(rounds) AS max_round, answers_id, criteriaandquestions_id ' +
                 'FROM Scores AS s2 ' +
                 'GROUP BY s2.answers_id, s2.criteriaandquestions_id ' +
                 'HAVING count(*) > 1) AS s1 ' +
                 'ON s.criteriaandquestions_id = s1.criteriaandquestions_id ' +
                 'AND s.answers_id = s1.answers_id ' +
                 'AND s.rounds != s1.max_round)')
        op.get_bind().execute(query)
        batch_op.create_unique_constraint(
            'uq_Scores_answers_id_criteriaandquestions_id', ['answers_id', 'criteriaandquestions_id'])
        # has to drop the fk before alter the column
        batch_op.drop_constraint('fk_Scores_answers_id_Answers', 'foreignkey')
        batch_op.alter_column('answers_id', nullable=False, existing_type=sa.Integer)
        batch_op.create_foreign_key('fk_Scores_answers_id_Answers', 'Answers',
                                    ['answers_id'], ['id'], ondelete="CASCADE")


def downgrade():
    try:
        with op.batch_alter_table(
                'Scores', naming_convention=convention,
                table_args=(UniqueConstraint('answers_id', 'criteriaandquestions_id'))) as batch_op:
            batch_op.drop_constraint('uq_Scores_answers_id_criteriaandquestions_id', 'unique')
            batch_op.alter_column('answers_id', nullable=True, existing_type=sa.Integer)
    except exc.InternalError:
        with op.batch_alter_table(
                'Scores', naming_convention=convention,
                table_args=(UniqueConstraint('answers_id', 'criteriaandquestions_id'))) as batch_op:
            batch_op.drop_constraint('uq_Scores_answers_id_criteriaandquestions_id', type_='unique')
            batch_op.alter_column('answers_id', nullable=True, existing_type=sa.Integer)
    except ValueError:
        logging.warning('Drop unique constraint is not support for SQLite, dropping uq_Scores_answers_id_criteriaandquestions_id ignored!')

