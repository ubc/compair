"""
    Report Generator
"""
import csv

from flask.ext.script import Manager
from sqlalchemy import and_
from sqlalchemy.orm import aliased

from acj.models import Score, Answer, Criterion, Comparison, \
    Course, User, UserCourse

manager = Manager(usage="Generate Reports")


@manager.option('-c', '--course', dest='course_id', help='Specify a course ID to generate report from.')
def create(course_id):
    """Creates report"""
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
        join(Answer). \
        join(Score.criterion). \
        filter(Answer.draft == False). \
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
            join(Comparison.answer_winner).join(Answer). \
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
            join(User.UserCourse). \
            filter(UserCourse.course_id == course_id)

    users = query.all()

    write_csv(
            course_name + 'users.csv',
            ['User Id', 'Student #'],
            users
    )

    print('Done.')


def write_csv(filename, headers, data):
    with open(filename, 'wb') as csvfile:
        report_writer = csv.writer(
            csvfile, delimiter=',',
            quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        report_writer.writerow(headers)
        for d in data:
            report_writer.writerow(d)
