"""Modify comparison table

Revision ID: 622121ae2f36
Revises: aa532b17a272
Create Date: 2017-01-12 21:30:56.834999

"""

# revision identifiers, used by Alembic.
revision = '622121ae2f36'
down_revision = 'aa532b17a272'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType
import uuid
import base64
from enum import Enum

from compair.models import convention

class PairingAlgorithm(Enum):
    adaptive = "adaptive"
    random = "random"

class WinningAnswer(Enum):
    answer1 = "answer1"
    answer2 = "answer2"
    draw = "draw"

def upgrade():
    # Rename score table to answer_criterion_score
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_comparison_comparison_example_id_comparison_example', 'foreignkey')
        batch_op.drop_index('ix_comparison_completed')
        batch_op.drop_constraint("uq_comparison_uuid", type_='unique')

    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('fk_comparison_assignment_id_assignment', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_user_id_user', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_criterion_id_criterion', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_answer1_id_answer', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_answer2_id_answer', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_modified_user_id_user', 'foreignkey')
            batch_op.drop_constraint('fk_comparison_created_user_id_user', 'foreignkey')
    except sa.exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('comparison') as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('comparison_ibfk_1', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_2', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_3', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_4', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_5', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_7', 'foreignkey')
            batch_op.drop_constraint('comparison_ibfk_8', 'foreignkey')

    # remname comparison table comparison_temp
    op.rename_table('comparison', 'comparison_temp')

    # create new tables
    comparison_table = op.create_table('comparison',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.CHAR(length=22), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('answer1_id', sa.Integer(), nullable=False),
        sa.Column('answer2_id', sa.Integer(), nullable=False),
        sa.Column('winner', EnumType(WinningAnswer), nullable=True),
        sa.Column('comparison_example_id', sa.Integer(), nullable=True),
        sa.Column('round_compared', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('pairing_algorithm', EnumType(PairingAlgorithm), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer1_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answer2_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comparison_example_id'], ['comparison_example.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_comparison_completed'), 'comparison', ['completed'], unique=False)

    comparison_criterion_table = op.create_table('comparison_criterion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.CHAR(length=22), nullable=False),
        sa.Column('comparison_id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('winner', EnumType(WinningAnswer), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['comparison_id'], ['comparison.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

    # migrate data
    connection = op.get_bind()

    comparison_temp_table = sa.table('comparison_temp',
        sa.column('id', sa.Integer), sa.column('uuid', sa.CHAR(22)),
        sa.Column('assignment_id', sa.Integer), sa.Column('user_id', sa.Integer), sa.Column('criterion_id', sa.Integer),
        sa.Column('answer1_id', sa.Integer), sa.Column('answer2_id', sa.Integer), sa.Column('winner_id', sa.Integer),
        sa.Column('comparison_example_id', sa.Integer),
        sa.Column('round_compared', sa.Integer), sa.Column('content', sa.Text), sa.Column('completed', sa.Boolean),
        sa.Column('pairing_algorithm', EnumType(PairingAlgorithm)),
        sa.Column('modified_user_id', sa.Integer), sa.Column('created_user_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    )

    # key is assignment_id+user_id+answer1_id+answer2_id
    # data is criteria wins per answer
    # if record pre-exists in this hash, then do no add new comparison table row
    comparison_aggregate_data = {}

    chunk_size = 5000
    select_result = connection.execution_options(stream_results=True).execute(comparison_temp_table.select())
    chunk = select_result.fetchmany(chunk_size)
    while chunk:
        for comparison in chunk:
            key = str(comparison.assignment_id)+"+"+str(comparison.user_id)+"+"+str(comparison.answer1_id)+"+"+str(comparison.answer2_id)
            comparison_data = comparison_aggregate_data.get(key)

            modified = comparison.modified if comparison.modified else datetime.utcnow()
            created = comparison.created if comparison.created else datetime.utcnow()
            winner = None
            if comparison.completed:
                if comparison.winner_id == comparison.answer1_id:
                    winner = WinningAnswer.answer1
                elif comparison.winner_id == comparison.answer2_id:
                    winner = WinningAnswer.answer2

            if not comparison_data:
                # populate comparison table
                result = connection.execute(
                    comparison_table.insert().values(
                        uuid=base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').replace('=', ''),
                        assignment_id=comparison.assignment_id, user_id=comparison.user_id,
                        answer1_id=comparison.answer1_id, answer2_id=comparison.answer2_id,
                        winner=None, #to be decided after talling all comparisons
                        comparison_example_id=comparison.comparison_example_id,
                        round_compared=comparison.round_compared, completed=comparison.completed,
                        pairing_algorithm=comparison.pairing_algorithm,
                        modified=modified, created=created
                    )
                )
                comparison_data = {
                    'comparison_id': result.lastrowid,
                    'completed': comparison.completed
                }
                if comparison.completed:
                    comparison_data['answer1'] = 0
                    comparison_data['answer2'] = 0

                comparison_aggregate_data[key] = comparison_data

            if winner == WinningAnswer.answer1:
                comparison_data['answer1'] += 1
            elif winner == WinningAnswer.answer2:
                comparison_data['answer2'] += 1

            # populate comparison_criterion table
            connection.execute(
                comparison_criterion_table.insert().values(
                    uuid=comparison.uuid,
                    comparison_id=comparison_data.get('comparison_id'),
                    criterion_id=comparison.criterion_id,
                    winner=winner,
                    content=comparison.content,
                    modified=modified, created=created
                )
            )
        # fetch next chunk
        chunk = select_result.fetchmany(chunk_size)

    # only update completed comparisons
    for key, comparison_data in comparison_aggregate_data.items():
        if comparison_data.get('completed'):
            comparison_id = comparison_data.get('comparison_id')
            answer1 = comparison_data.get('answer1')
            answer2 = comparison_data.get('answer2')

            winner = WinningAnswer.draw
            if answer1 > answer2:
                winner = WinningAnswer.answer1
            elif answer2 > answer1:
                winner = WinningAnswer.answer2

            connection.execute(
                comparison_table.update().where(
                    comparison_table.c.id == comparison_id
                ).values(
                    winner=winner
                )
            )

    # drop old data table
    op.drop_table('comparison_temp')


def downgrade():
    # expected foreign key to follow naming conventions
    with op.batch_alter_table('comparison', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_comparison_assignment_id_assignment', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_user_id_user', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_answer1_id_answer', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_answer2_id_answer', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_modified_user_id_user', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_created_user_id_user', 'foreignkey')
        batch_op.drop_constraint('fk_comparison_comparison_example_id_comparison_example', 'foreignkey')
        batch_op.drop_index('ix_comparison_completed')
        batch_op.drop_constraint("uq_comparison_uuid", type_='unique')

    # remname comparison_temp table comparison
    op.rename_table('comparison', 'comparison_temp')

    # create old comparison table
    comparison_table = op.create_table('comparison',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.CHAR(22), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('answer1_id', sa.Integer(), nullable=False),
        sa.Column('answer2_id', sa.Integer(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('comparison_example_id', sa.Integer(), nullable=True),
        sa.Column('round_compared', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('pairing_algorithm', EnumType(PairingAlgorithm), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer1_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answer2_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comparison_example_id'], ['comparison_example.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_id'], ['answer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_comparison_completed'), 'comparison', ['completed'], unique=False)

    # migrate data
    connection = op.get_bind()

    comparison_temp_table = sa.table('comparison_temp',
        sa.column('id', sa.Integer),
        sa.Column('assignment_id', sa.Integer), sa.Column('user_id', sa.Integer),
        sa.Column('answer1_id', sa.Integer), sa.Column('answer2_id', sa.Integer),
        sa.Column('comparison_example_id', sa.Integer),
        sa.Column('round_compared', sa.Integer),  sa.Column('completed', sa.Boolean),
        sa.Column('pairing_algorithm', EnumType(PairingAlgorithm)),
        sa.Column('modified_user_id', sa.Integer), sa.Column('created_user_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    )

    comparison_criterion_table = sa.table('comparison_criterion',
        sa.column('id', sa.Integer), sa.column('uuid', sa.CHAR(22)),
        sa.Column('comparison_id', sa.Integer), sa.Column('criterion_id', sa.Integer),
        sa.Column('winner', EnumType(WinningAnswer)),
        sa.Column('content', sa.Text),
        sa.Column('modified_user_id', sa.Integer), sa.Column('created_user_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    )

    chunk_size = 5000
    select_result = connection.execution_options(stream_results=True).execute(comparison_criterion_table.select())
    chunk = select_result.fetchmany(chunk_size)
    while chunk:
        for comparison_criterion in chunk:
            comparison = None
            comparisons = connection.execute(comparison_temp_table.select().where(
                comparison_temp_table.c.id == comparison_criterion.comparison_id))
            for c in comparisons:
                comparison = c

            if comparison == None:
                continue

            modified = comparison_criterion.modified if comparison_criterion.modified else datetime.utcnow()
            created = comparison_criterion.created if comparison_criterion.created else datetime.utcnow()

            winner_id = None
            if comparison_criterion.winner == WinningAnswer.answer1:
                winner_id = comparison.answer1_id
            elif comparison_criterion.winner == WinningAnswer.answer2:
                winner_id = comparison.answer2_id

            # populate comparison table
            connection.execute(
                comparison_table.insert().values(
                    uuid=comparison_criterion.uuid,
                    assignment_id=comparison.assignment_id, user_id=comparison.user_id,
                    criterion_id=comparison_criterion.criterion_id,
                    answer1_id=comparison.answer1_id, answer2_id=comparison.answer2_id,
                    winner_id=winner_id,
                    comparison_example_id=comparison.comparison_example_id,
                    round_compared=comparison.round_compared,
                    content=comparison_criterion.content,
                    completed=comparison.completed, pairing_algorithm=comparison.pairing_algorithm,
                    modified=modified, created=created
                )
            )
        # fetch next chunk
        chunk = select_result.fetchmany(chunk_size)

    # drop new tables
    op.drop_table('comparison_criterion')
    op.drop_table('comparison_temp')