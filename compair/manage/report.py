"""
    Report Generator
"""
import unicodecsv as csv
import elo
from compair.algorithms import ScoredObject
from compair.algorithms.score import calculate_score_1vs1
import numbers
from werkzeug.utils import secure_filename

from flask_script import Manager
from sqlalchemy import and_, asc
from sqlalchemy.orm import aliased, joinedload

from compair.models import AnswerScore, AnswerCriterionScore, \
    Answer, Criterion, Comparison, WinningAnswer, \
    Course, Assignment, User, UserCourse, ScoringAlgorithm

manager = Manager(usage="Generate Reports")

"""
@manager.option('-c', '--course', dest='course_id', help='Specify a course ID to generate report from.')
def create(course_id):
    course_name = ''
    if course_id:
        course_name = Course.query.with_entities(Course.name).filter_by(id=course_id).scalar()
        if not course_name:
            raise RuntimeError("Course with ID {} is not found.".format(course_id))
        course_name = course_name.replace('"', '')
        course_name += '_'

    query = Score.query. \
        with_entities(Answer.user_id, Answer.assignment_id, Answer.id,
                      Criterion.id, Criterion.name, Score.score). \
        join(Score.answer). \
        join(Score.criterion). \
        filter(Answer.draft == False). \
        filter(Answer.practice == False). \
        order_by(Answer.assignment_id, Criterion.id, Answer.user_id)

    if course_id:
        query = query.filter(Answer.course_id == course_id)

    scores = query.all()

    write_csv(
        course_name + 'scores.csv',
        ['User Id', 'Assignment Id', 'Answer Id', 'Criterion Id', 'Criterion', 'Score'],
        scores
    )

    score2 = aliased(Score)
    query = Comparison.query. \
        with_entities(Comparison.user_id, Comparison.assignment_id,
                      Comparison.criterion_id, Criterion.name,
                      Comparison.answer1_id, Score.score, Comparison.answer2_id,
                      score2.score, Comparison.winner_id). \
        join(Comparison.criterion). \
        join(Score, and_(Score.answer_id == Comparison.answer1_id,
                          Score.criterion_id == Comparison.criterion_id)). \
        join(score2, and_(score2.answer_id == Comparison.answer2_id,
                           score2.criterion_id == Comparison.criterion_id)). \
        order_by(Comparison.assignment_id, Comparison.criterion_id, Comparison.user_id)

    if course_id:
        query = query. \
            join(Comparison.winning_answer). \
            filter(Answer.course_id == course_id)

    comparisons = query.all()

    write_csv(
        course_name + 'comparisons.csv',
        ['User Id', 'Assignment Id', 'Criterion Id', 'Criterion', 'Answer 1', 'Score 1', 'Answer 2', 'Score 2', 'Winner'],
        comparisons
    )


    query = User.query. \
        with_entities(User.id, User.student_number). \
        order_by(User.id)

    if course_id:
        query = query. \
            join(User.user_courses). \
            filter(UserCourse.course_id == course_id)

    users = query.all()

    write_csv(
            course_name + 'users.csv',
            ['User Id', 'Student #'],
            users
    )

    print('Done.')
"""

@manager.option('-a', '--assignment', dest='assignment_id', help='Specify a Assignment ID to generate report from.')
def create(assignment_id):
    """Creates report"""
    if not assignment_id:
        raise RuntimeError("Assignment with ID {} is not found.".format(assignment_id))

    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if not assignment:
        raise RuntimeError("Assignment with ID {} is not found.".format(assignment_id))
    criteria = assignment.criteria

    file_name = assignment.course.name.replace('"', '') + '_' + assignment_id + '_'

    answers = Answer.query \
        .options(joinedload('score')) \
        .options(joinedload('criteria_scores')) \
        .filter(and_(
            Answer.assignment_id == assignment.id,
            Answer.active == True,
            Answer.draft == False,
            Answer.practice == False
        )) \
        .order_by(Answer.assignment_id, Answer.user_id) \
        .all()

    scores = []
    for answer in answers:
        score = answer.score
        if score:
            scores.append([answer.user_id, answer.id, None, 'Overall',
                score.score, score.rounds, score.wins,
                score.loses, score.opponents])

        criteria_scores = answer.criteria_scores
        criteria_scores.sort(key=lambda x: x.criterion_id)

        for criterion_score in criteria_scores:
            criterion = next(criterion for criterion in criteria if criterion.id == criterion_score.criterion_id)

            scores.append([answer.user_id, answer.id, criterion.id, criterion.name,
                criterion_score.score, criterion_score.rounds, criterion_score.wins,
                criterion_score.loses, criterion_score.opponents])

    write_csv(
        file_name + 'scores_final.csv',
        ['User Id', 'Answer Id', 'Criterion Id', 'Criterion', 'Score', 'Rounds', 'Wins', 'Loses', 'Opponents'],
        scores
    )

    # replay comparisons for real scores at every step
    comparisons_output = []
    scores = {
        criterion.id: {} for criterion in criteria
    }
    scores['overall'] = {}
    past_comparisons = {
        criterion.id: [] for criterion in criteria
    }
    past_comparisons['overall'] = []

    comparisons = Comparison.query \
        .options(joinedload('comparison_criteria')) \
        .filter_by(
            assignment_id=assignment.id,
            completed=True
        ) \
        .order_by(Comparison.modified, Comparison.user_id) \
        .all()

    round_length = float(len(answers)) / 2
    round_number = 0
    for index, comparison in enumerate(comparisons):
        answer1_id = comparison.answer1_id
        answer2_id = comparison.answer2_id

        # overall
        answer1_score_before = scores['overall'].get(answer1_id, ScoredObject(
            key=answer1_id,
            score=elo.INITIAL,
            variable1=elo.INITIAL,
            variable2=None,
            rounds=0,
            wins=0,
            loses=0,
            opponents=0
        ))
        answer2_score_before = scores['overall'].get(answer2_id, ScoredObject(
            key=answer2_id,
            score=elo.INITIAL,
            variable1=elo.INITIAL,
            variable2=None,
            rounds=0,
            wins=0,
            loses=0,
            opponents=0
        ))

        other_comparisons = []
        for pc in past_comparisons['overall']:
            if pc.key1 in [answer1_id, answer2_id] or pc.key2 in [answer1_id, answer2_id]:
                other_comparisons.append(pc)

        result_1, result_2 = calculate_score_1vs1(
            package_name=ScoringAlgorithm.elo.value,
            key1_scored_object=answer1_score_before,
            key2_scored_object=answer2_score_before,
            winner=comparison.comparison_pair_winner(),
            other_comparison_pairs=[c for c in other_comparisons]
        )
        scores['overall'][result_1.key] = result_1
        scores['overall'][result_2.key] = result_2

        answer1_score_after = scores['overall'][answer1_id]
        answer2_score_after = scores['overall'][answer2_id]

        past_comparisons['overall'].append(comparison.convert_to_comparison_pair())

        winner_id = None
        if comparison.winner == WinningAnswer.answer1:
            winner_id = answer1_id
        elif comparison.winner == WinningAnswer.answer2:
            winner_id = answer2_id
        elif comparison.winner == WinningAnswer.draw:
            winner_id = "draw"

        comparisons_output.append([
            comparison.user_id, None, 'Overall',
            answer1_id, answer1_score_before.score, answer1_score_after.score,
            answer2_id, answer2_score_before.score, answer2_score_after.score,
            winner_id, comparison.modified
        ])

        # each criterion
        comparison_criteria = comparison.comparison_criteria
        comparison_criteria.sort(key=lambda x: x.criterion_id)
        for comparison_criterion in comparison_criteria:
            criterion = next(criterion for criterion in criteria if criterion.id == comparison_criterion.criterion_id)

            answer1_score_before = scores[criterion.id].get(answer1_id, ScoredObject(
                key=answer1_id,
                score=elo.INITIAL,
                variable1=elo.INITIAL,
                variable2=None,
                rounds=0,
                wins=0,
                loses=0,
                opponents=0
            ))
            answer2_score_before = scores[criterion.id].get(answer2_id, ScoredObject(
                key=answer2_id,
                score=elo.INITIAL,
                variable1=elo.INITIAL,
                variable2=None,
                rounds=0,
                wins=0,
                loses=0,
                opponents=0
            ))

            other_comparisons = []
            for pc in past_comparisons[criterion.id]:
                if pc.key1 in [answer1_id, answer2_id] or pc.key2 in [answer1_id, answer2_id]:
                    other_comparisons.append(pc)

            result_1, result_2 = calculate_score_1vs1(
                package_name=ScoringAlgorithm.elo.value,
                key1_scored_object=answer1_score_before,
                key2_scored_object=answer2_score_before,
                winner=comparison_criterion.comparison_pair_winner(),
                other_comparison_pairs=[c for c in other_comparisons]
            )
            scores[criterion.id][result_1.key] = result_1
            scores[criterion.id][result_2.key] = result_2

            answer1_score_after = scores[criterion.id][answer1_id]
            answer2_score_after = scores[criterion.id][answer2_id]

            past_comparisons[criterion.id].append(comparison.convert_to_comparison_pair())

            winner_id = None
            if comparison_criterion.winner == WinningAnswer.answer1:
                winner_id = answer1_id
            elif comparison_criterion.winner == WinningAnswer.answer2:
                winner_id = answer2_id

            comparisons_output.append([
                comparison.user_id, criterion.id, criterion.name,
                answer1_id, answer1_score_before.score, answer1_score_after.score,
                answer2_id, answer2_score_before.score, answer2_score_after.score,
                winner_id, comparison_criterion.modified
            ])

        if (index+1) % round_length < 1:
            round_number += 1

            round_scores = []
            for answer in answers:
                score = scores['overall'].get(answer.id, ScoredObject(
                    key=answer2_id,
                    score=elo.INITIAL,
                    variable1=elo.INITIAL,
                    variable2=None,
                    rounds=0,
                    wins=0,
                    loses=0,
                    opponents=0
                ))

                round_scores.append([answer.user_id, answer.id, None, 'Overall',
                    score.score, score.rounds, score.wins,
                    score.loses, score.opponents])

                comparison_criteria = comparison.comparison_criteria
                comparison_criteria.sort(key=lambda x: x.criterion_id)
                for comparison_criterion in comparison_criteria:
                    criterion = next(criterion for criterion in criteria if criterion.id == comparison_criterion.criterion_id)
                    criterion_score = scores[criterion.id].get(answer.id, ScoredObject(
                        key=answer2_id,
                        score=elo.INITIAL,
                        variable1=elo.INITIAL,
                        variable2=None,
                        rounds=0,
                        wins=0,
                        loses=0,
                        opponents=0
                    ))

                    round_scores.append([answer.user_id, answer.id, criterion.id, criterion.name,
                        criterion_score.score, criterion_score.rounds, criterion_score.wins,
                        criterion_score.loses, criterion_score.opponents])

            write_csv(
                file_name + 'scores_round_' + str(round_number) + '.csv',
                ['User Id', 'Answer Id', 'Criterion Id', 'Criterion', 'Score', 'Rounds', 'Wins', 'Loses', 'Opponents'],
                round_scores
            )

    write_csv(
        file_name + 'comparisons.csv',
        ['User Id', 'Criterion Id', 'Criterion',
         'Answer 1', 'Score 1 Before', 'Score 1 After',
         'Answer 2', 'Score 2 Before', 'Score 2 After',
         'Winner', 'Timestamp'],
        comparisons_output
    )


    query = User.query \
        .join(User.user_courses) \
        .with_entities(User.id, User.student_number) \
        .filter(UserCourse.course_id == assignment.course_id) \
        .order_by(User.id)

    users = query.all()

    write_csv(
        file_name + 'users.csv',
        ['User Id', 'Student #'],
        users
    )

    print('Done.')


def write_csv(filename, headers, data):
    with open(secure_filename(filename), 'wt') as csvfile:
        report_writer = csv.writer(
            csvfile, delimiter=',',
            quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        report_writer.writerow(headers)
        for d in data:
            output = []
            for o in d:
                output.append(o)
            report_writer.writerow(output)
