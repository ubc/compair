"""
    Recalculate Scores
"""

import click
from flask.cli import AppGroup
from compair.models import Comparison, Assignment

score_cli = AppGroup('score', help="Recalculate Assignment Answer Scores")

@score_cli.command('recalculate')
@click.option('-a', '--assignment-id', required=True, help='Specify an Assignment ID to recalculate scores for.')
def recalculate(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if not assignment:
        raise RuntimeError(f"Assignment with ID {assignment_id} is not found.")

    if click.confirm("""All current answer scores and answer criterion scores will be overwritten.
Final scores may differ slightly due to floating point rounding (especially if recalculating on different systems).
Are you sure?"""):
        print ('Recalculating scores...')
        Comparison.calculate_scores(assignment.id)
        print ('Recalculate scores successful.')
