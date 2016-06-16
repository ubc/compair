import csv
import os
import time

from bouncer.constants import MANAGE
from flask import Blueprint, Flask, current_app, abort
from flask.ext.login import login_required, current_user

from flask.ext.restful import Resource, reqparse

from sqlalchemy import func

from acj.authorization import require
from acj.core import event
from acj.models import CourseRole, Assignment, UserCourse, Course, Answer, \
    AnswerComment, AssignmentCriteria, Comparison, AnswerCommentType
from .util import new_restful_api

report_api = Blueprint('report_api', __name__)
api = new_restful_api(report_api)

# TODO put in config file
UPLOAD_FOLDER = os.getcwd() + '/acj/static/report'
app = Flask(__name__)
app.config['PERMANENT_REPORT_UPLOAD_FOLDER'] = UPLOAD_FOLDER

report_parser = reqparse.RequestParser()
report_parser.add_argument('group_name', type=str)
# may change 'type' to int
report_parser.add_argument('type', type=str, required=True)
report_parser.add_argument('assignment', type=int)

# events
on_export_report = event.signal('EXPORT_REPORT')
# should we have a different event for each type of report?


def name_generator(course, report_name, group_name, file_type="csv"):
    date = time.strftime("%Y-%m-%d--%H-%M-%S")
    group_name_output = ""
    if group_name:
        group_name_output = group_name + '-'
    # return report_name + "_" + course.name + "_" + random_generator(4) + "." + file_type
    return course.name + "-" + group_name_output + report_name + "--" + date + "." + file_type


class ReportRootAPI(Resource):
    @login_required
    def post(self, course_id):
        course = Course.get_active_or_404(course_id)
        assignment = Assignment(course_id=course.id)
        require(MANAGE, assignment)

        params = report_parser.parse_args()
        group_name = params.get('group_name', None)
        report_type = params.get('type')

        assignments = []
        assignment_id = params.get('assignment', None)
        if assignment_id:
            assignment = Assignment.get_active_or_404(assignment_id)
            assignments = [assignment]
        else:
            assignments = Assignment.query \
                .filter_by(
                    course_id=course_id,
                    active=True
                ) \
                .all()

        if group_name:
            # ensure that group_name is valid
            group_exists = UserCourse.query \
                .filter(
                    UserCourse.group_name == group_name,
                    UserCourse.course_id == course_id,
                    UserCourse.course_role != CourseRole.dropped
                ) \
                .first()
            if group_exists == None:
                abort(404)

        if report_type == "participation_stat":
            data = participation_stat_report(course_id, assignments, group_name, assignment_id is None)

            title = [
                'Assignment', 'Username', 'Last Name', 'First Name', 'Answer Submitted', 'Answer ID',
                'Evaluations Submitted', 'Evaluations Required', 'Evaluation Requirements Met',
                'Replies Submitted']
            titles = [title]

        elif report_type == "participation":
            user_titles = ['Last Name', 'First Name', 'Student No']
            data = participation_report(course_id, assignments, group_name)

            title_row1 = [""] * len(user_titles)
            title_row2 = user_titles

            for assignment in assignments:
                assignment_criteria = AssignmentCriteria.query \
                    .filter_by(
                        assignment_id=assignment.id,
                        active=True
                    ) \
                    .all()

                title_row1 += [assignment.name] + [""] * len(assignment_criteria)
                for criteria in assignment_criteria:
                    title_row2.append('Percentage Score for "' + criteria.criteria.name + '"')
                title_row2.append("Evaluations Submitted (" + str(assignment.number_of_comparisons) + ' required)')
                if assignment.enable_self_evaluation:
                    title_row1 += [""]
                    title_row2.append("Self Evaluation Submitted")
            titles = [title_row1, title_row2]

        else:
            return {'error': 'The requested report type cannot be found'}, 400

        name = name_generator(course, report_type, group_name)
        tmp_name = os.path.join(current_app.config['REPORT_FOLDER'], name)

        report = open(tmp_name, 'wb')
        out = csv.writer(report)
        for t in titles:
            out.writerow(t)
        for s in data:
            out.writerow(s)
        report.close()

        on_export_report.send(
            self,
            event_name=on_export_report.name,
            user=current_user,
            course_id=course_id,
            data={'type': report_type, 'filename': name})

        return {'file': 'report/' + name}


api.add_resource(ReportRootAPI, '')


def participation_stat_report(course_id, assignments, group_name, overall):
    report = []

    user_course_students = UserCourse.query \
        .filter_by(
            course_id=course_id,
            course_role=CourseRole.student
        )
    if group_name:
        user_course_students = user_course_students.filter_by(group_name=group_name)
    user_course_students = user_course_students.all()

    total_req = 0
    total = {}

    for assignment in assignments:
        # ANSWERS: assume max one answer per user
        answers = Answer.query \
            .filter_by(active=True) \
            .filter_by(assignment_id=assignment.id) \
            .all()
        answers = {a.user_id: a.id for a in answers}

        # EVALUATIONS
        evaluations = Comparison.query \
            .with_entities(Comparison.user_id, func.count(Comparison.id)) \
            .filter_by(assignment_id=assignment.id) \
            .group_by(Comparison.user_id) \
            .all()
        evaluations = {user_id: count for (user_id, count) in evaluations}

        # COMMENTS
        comments = AnswerComment.query \
            .join(Answer) \
            .filter(Answer.assignment_id == assignment.id) \
            .with_entities(AnswerComment.user_id, func.count(AnswerComment.id)) \
            .group_by(AnswerComment.user_id) \
            .all()
        comments = {user_id: count for (user_id, count) in comments}

        total_req += assignment.number_of_comparisons  # for overall required
        criteria_count = len(assignment.assignment_criteria)

        for user_course_student in user_course_students:
            user = user_course_student.user
            temp = [assignment.name, user.username, user.lastname, user.firstname]

            # OVERALL
            total.setdefault(user.id, {
                'total_answers': 0,
                'total_evaluations': 0,
                'total_comments': 0
            })

            submitted = 1 if user.id in answers else 0
            answer_id = answers[user.id] if submitted else 'N/A'
            total[user.id]['total_answers'] += submitted
            temp.extend([submitted, answer_id])

            evaluation_submitted = evaluations[user.id] if user.id in evaluations else 0
            evaluation_submitted /= criteria_count if criteria_count else 0
            evaluation_req_met = 'Yes' if evaluation_submitted >= assignment.number_of_comparisons else 'No'
            total[user.id]['total_evaluations'] += evaluation_submitted
            temp.extend([evaluation_submitted, assignment.number_of_comparisons, evaluation_req_met])

            comment_count = comments[user.id] if user.id in comments else 0
            total[user.id]['total_comments'] += comment_count
            temp.append(comment_count)

            report.append(temp)

    if overall:
        for user_course_student in user_course_students:
            user = user_course_student.user
            sum_submission = total.setdefault(user.id, {
                'total_answers': 0,
                'total_evaluations': 0,
                'total_comments': 0
            })
            # assume a user can only at most do the required number
            req_met = 'Yes' if sum_submission['total_evaluations'] >= total_req else 'No'
            temp = [
                '(Overall in Course)', user.id, user.lastname, user.firstname,
                sum_submission['total_answers'], '(Overall in Course)',
                sum_submission['total_evaluations'], total_req, req_met,
                sum_submission['total_comments']]
            report.append(temp)
    return report


def participation_report(course_id, assignments, group_name):
    report = []

    classlist = UserCourse.query \
        .filter_by(
            course_id=course_id,
            course_role=CourseRole.student
        )
    if group_name:
        classlist = classlist.filter_by(group_name=group_name)
    classlist = classlist.all()

    assignment_ids = [assignment.id for assignment in assignments]
    user_ids = [u.user.id for u in classlist]

    # ANSWERS - scores
    answers = Answer.query \
        .filter(Answer.assignment_id.in_(assignment_ids)) \
        .filter(Answer.user_id.in_(user_ids)) \
        .all()

    scores = {}  # structure - user_id/assignment_id/criteria_id/normalized_score
    for answer in answers:
        user_object = scores.setdefault(answer.user_id, {})
        assignment_object = user_object.setdefault(answer.assignment_id, {})
        for s in answer.scores:
            assignment_object[s.criteria_id] = s.normalized_score

    # COMPARISONS
    comparisons_counts = Comparison.query \
        .filter(Comparison.user_id.in_(user_ids)) \
        .filter(Comparison.assignment_id.in_(assignment_ids)) \
        .with_entities(Comparison.assignment_id, Comparison.user_id, func.count(Comparison.id)) \
        .group_by(Comparison.assignment_id, Comparison.user_id) \
        .all()

    comparisons = {}  # structure - user_id/assignment_id/count
    for (assignment_id, user_id, count) in comparisons_counts:
        comparisons.setdefault(user_id, {}).setdefault(assignment_id, 0)
        comparisons[user_id][assignment_id] = count

    # CRITERIA
    assignment_criteria = AssignmentCriteria.query \
        .filter(AssignmentCriteria.assignment_id.in_(assignment_ids)) \
        .filter_by(active=True) \
        .order_by(AssignmentCriteria.id) \
        .all()

    criteria = {}  # structure - assignment_id/criterion_id
    for assignment_criterion in assignment_criteria:
        criteria.setdefault(assignment_criterion.assignment_id, [])
        criteria[assignment_criterion.assignment_id] \
            .append(assignment_criterion.criteria_id)

    # SELF-EVALUATION - assuming no comparions
    self_evaluation = AnswerComment.query \
        .filter_by(comment_type=AnswerCommentType.self_evaluation) \
        .join(Answer) \
        .filter(Answer.assignment_id.in_(assignment_ids)) \
        .filter(AnswerComment.user_id.in_(user_ids)) \
        .with_entities(Answer.assignment_id, AnswerComment.user_id, func.count(AnswerComment.id)) \
        .group_by(Answer.assignment_id, AnswerComment.user_id) \
        .all()

    comments = {}  # structure - user_id/assignment_id/count
    for (assignment_id, user_id, count) in self_evaluation:
        comments.setdefault(user_id, {}).setdefault(assignment_id, 0)
        comments[user_id][assignment_id] = count

    for user_courses in classlist:
        user = user_courses.user
        temp = [user.lastname, user.firstname, user.student_number]

        for assignment in assignments:
            for criterion in criteria[assignment.id]:
                if user.id not in scores or assignment.id not in scores[user.id]:
                    score = 'No Answer'
                elif criterion not in scores[user.id][assignment.id]:
                    score = 'Not Evaluated'
                else:
                    score = scores[user.id][assignment.id][criterion]
                temp.append(score)
            if user.id not in comparisons or assignment.id not in comparisons[user.id]:
                compared = 0
            else:
                compared = comparisons[user.id][assignment.id] / len(criteria[assignment.id])
            temp.append(str(compared))
            # self-evaluation
            if assignment.enable_self_evaluation:
                if user.id not in comments or assignment.id not in comments[user.id]:
                    temp.append(0)
                else:
                    temp.append(comments[user.id][assignment.id])
        report.append(temp)

    return report
