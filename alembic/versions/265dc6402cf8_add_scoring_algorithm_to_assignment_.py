"""Add scoring_algorithm to assignment table

Revision ID: 265dc6402cf8
Revises: a91d59c2cfd5
Create Date: 2018-04-05 20:30:02.370380

"""

# revision identifiers, used by Alembic.
revision = '265dc6402cf8'
down_revision = 'a91d59c2cfd5'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

from sqlalchemy_enum34 import EnumType
from enum import Enum

class ScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating"
    true_skill = "true_skill_rating"

def upgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('scoring_algorithm', EnumType(ScoringAlgorithm), nullable=True))

    # set scoring algorithm to first answer score found for assignment (default elo if no scoring has occurred yet)
    connection = op.get_bind()
    assignment_table = sa.table('assignment',
        sa.column('id', sa.Integer), sa.column('scoring_algorithm', EnumType(ScoringAlgorithm))
    )
    answer_score_table = sa.table('answer_score',
        sa.column('id', sa.Integer), sa.column('assignment_id', sa.Integer),
        sa.column('scoring_algorithm', EnumType(ScoringAlgorithm))
    )

    scoring_algorithm_assignment_ids = {
        ScoringAlgorithm.comparative_judgement.value : [],
        ScoringAlgorithm.elo.value : [],
        ScoringAlgorithm.true_skill.value : []
    }

    for assignment in connection.execute(assignment_table.select()):
        answer_scores = connection.execute(answer_score_table.select().where(
                answer_score_table.c.assignment_id == assignment.id).limit(1))

        scoring_algorithm = ScoringAlgorithm.elo
        for answer_score in answer_scores:
            scoring_algorithm = answer_score.scoring_algorithm

        scoring_algorithm_assignment_ids[scoring_algorithm.value].append(assignment.id)

    for scoring_algorithm, assignment_ids in scoring_algorithm_assignment_ids.items():
        if len(assignment_ids) > 0:
            connection.execute(
                assignment_table.update().where(
                    assignment_table.c.id.in_(assignment_ids)
                ).values(
                    scoring_algorithm=ScoringAlgorithm(scoring_algorithm)
                )
            )

def downgrade():
    with op.batch_alter_table('assignment', naming_convention=convention) as batch_op:
        batch_op.drop_column('scoring_algorithm')
