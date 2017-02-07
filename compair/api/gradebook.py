from __future__ import division

import copy

from bouncer.constants import MANAGE
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from flask_restful import Resource
from sqlalchemy import func, and_
from sqlalchemy.orm import undefer, joinedload

from compair.authorization import require
from compair.models import Course, Assignment, CourseRole, User, UserCourse, Comparison, \
    AnswerComment, Answer, AnswerScore, AnswerCommentType, PairingAlgorithm, AssignmentGrade
from .util import new_restful_api
from compair.core import event



# First declare a Flask Blueprint for this module
gradebook_api = Blueprint('gradebook_api', __name__)
# Then pack the blueprint into a Flask-Restful API
api = new_restful_api(gradebook_api)

# events
on_gradebook_get = event.signal('GRADEBOOK_GET')

# declare an API URL
# /
class GradebookAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(
            assignment_uuid,
            joinedloads=['assignment_criteria']
        )
        require(MANAGE, assignment)

        # get all students in this course
        students = User.query \
            .with_entities(User.id, User.uuid, User.displayname, User.firstname, User.lastname, AssignmentGrade.grade) \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .outerjoin(AssignmentGrade, and_(
                 AssignmentGrade.user_id == User.id,
                 AssignmentGrade.assignment_id == assignment.id
            )) \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            )) \
            .all()
        student_ids = [student.id for student in students]

        # get students comparisons counts for this assignment
        comparisons = User.query \
            .with_entities(User.id, func.count(Comparison.id).label('compare_count')) \
            .join("comparisons") \
            .filter(and_(
                Comparison.assignment_id == assignment.id,
                Comparison.completed == True,
                User.id.in_(student_ids)
            )) \
            .group_by(User.id) \
            .all()

        # we want only the count for comparisons by current students in the course
        num_comparisons_per_student = {user_id: compare_count for (user_id, compare_count) in comparisons}

        # find out the scores that students get
        answer_scores = Answer.query \
            .with_entities(Answer.user_id, Answer.flagged, AnswerScore.normalized_score) \
            .outerjoin(AnswerScore, and_(
                 Answer.id == AnswerScore.answer_id
            )) \
            .filter(and_(
                Answer.assignment_id == assignment.id,
                Answer.draft == False,
                Answer.practice == False,
                Answer.user_id.in_(student_ids)
            )) \
            .all()

        # process the results into dicts
        include_scores = assignment.pairing_algorithm != PairingAlgorithm.random
        scores_by_user_id = {student_id: 'No Answer' for student_id in student_ids}
        flagged_by_user_id = {}
        num_answers_per_student = {}

        for (user_id, flagged, score ) in answer_scores:
            flagged_by_user_id[user_id] = 'Yes' if flagged else 'No'
            num_answers_per_student[user_id] = 1
            if include_scores:
                scores_by_user_id[user_id] = round(score, 3) if score != None else 'Not Evaluated'

        include_self_evaluation = False
        num_self_evaluation_per_student = {student_id: 0 for student_id in student_ids}
        if assignment.enable_self_evaluation:
            include_self_evaluation = True

            self_evaluation_counts = AnswerComment.query \
                .with_entities(AnswerComment.user_id, func.count('*').label('comment_count')) \
                .join(Answer, and_(
                    Answer.id == AnswerComment.answer_id,
                    Answer.assignment_id == assignment.id
                )) \
                .filter(and_(
                    AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                    AnswerComment.draft == False,
                    AnswerComment.user_id.in_(student_ids)
                )) \
                .group_by(AnswerComment.user_id) \
                .all()

            for self_evaluation_count in self_evaluation_counts:
                num_self_evaluation_per_student[self_evaluation_count.user_id] = self_evaluation_count.comment_count

        # {'gradebook':[{user1}. {user2}, ...]}
        # user id, username, first name, last name, answer submitted, comparisons submitted
        gradebook = []
        for student in students:
            entry = {
                'user_id': student.uuid,
                'displayname': student.displayname,
                'firstname': student.firstname,
                'lastname': student.lastname,
                'num_answers': num_answers_per_student.get(student.id, 0),
                'num_comparisons': num_comparisons_per_student.get(student.id, 0),
                'grade': student.grade * 100 if student.grade else 0,
                'flagged': flagged_by_user_id.get(student.id, 'No Answer')
            }
            if include_scores:
                entry['score'] = scores_by_user_id.get(student.id, 'No Answer')
            if include_self_evaluation:
                entry['num_self_evaluation'] = num_self_evaluation_per_student[student.id]
            gradebook.append(entry)

        ret = {
            'gradebook': gradebook,
            'total_comparisons_required': assignment.total_comparisons_required,
            'include_scores': include_scores,
            'include_self_evaluation': include_self_evaluation
        }

        on_gradebook_get.send(
            self,
            event_name=on_gradebook_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return jsonify(ret)


api.add_resource(GradebookAPI, '')
