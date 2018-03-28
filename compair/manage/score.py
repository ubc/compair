"""
    Recalculate Scores
"""

from flask_script import Manager, prompt_bool
from compair.models import Comparison, Assignment


manager = Manager(usage="Recalculate Assignment Answer Scores")


@manager.option('-a', '--assignment', dest='assignment_id', help='Specify a Assignment ID to generate report from.')
def recalculate(assignment_id):
    if not assignment_id:
        raise RuntimeError("Assignment with ID {} is not found.".format(assignment_id))

    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if not assignment:
        raise RuntimeError("Assignment with ID {} is not found.".format(assignment_id))

    if prompt_bool("""All current answer scores and answer criterion scores will be overwritten.
Final scores may differ slightly due to floating point rounding (especially if recalculating on different systems).
Are you sure?"""):
        print ('Recalculating scores...')
        Comparison.calculate_scores(assignment.id)
        print ('Recalculate scores successful.')
