from __future__ import division

import copy

from bouncer.constants import MANAGE
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from flask_restful import Resource, marshal_with, marshal, reqparse
from sqlalchemy import func, and_
from sqlalchemy.orm import undefer, joinedload
from flask_restplus import abort

from . import dataformat
from compair.authorization import require
from compair.models import Course, Assignment, CourseRole, User, UserCourse, Comparison, \
    AnswerComment, Answer, File, AnswerScore, AnswerCommentType, PairingAlgorithm, AssignmentGrade
from .util import new_restful_api
from compair.core import event

gradebook_api = Blueprint('gradebook_api', __name__)
api = new_restful_api(gradebook_api)

# events
on_gradebook_get = event.signal('GRADEBOOK_GET')


# /
class GradebookAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(
            assignment_uuid,
            joinedloads=['assignment_criteria']
        )
        require(MANAGE, assignment,
            title="Failed to Retrieve Grade Book",
            message="You do not have permission to view grade book for this assignment since you are not the course's instructor.")

        # get all students in this course
        students = User.query \
            .with_entities(User, AssignmentGrade.grade) \
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
        student_ids = [student.id for (student, grade) in students]

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
            .with_entities(Answer.user_id, Answer.flagged, File, AnswerScore.normalized_score) \
            .outerjoin(File, and_(
                 Answer.file_id == File.id
            )) \
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
        file_by_user_id = {}

        for (user_id, flagged, file_attachment, score) in answer_scores:
            flagged_by_user_id[user_id] = 'Yes' if flagged else 'No'
            num_answers_per_student[user_id] = 1
            if include_scores:
                scores_by_user_id[user_id] = round(score, 3) if score != None else 'Not Evaluated'
            if file_attachment != None:
                file_by_user_id[user_id] = file_attachment

        include_self_evaluation = False
        num_self_evaluation_per_student = {}
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
                    AnswerComment.active == True,
                    AnswerComment.user_id.in_(student_ids)
                )) \
                .group_by(AnswerComment.user_id) \
                .all()

            for (user_id, comment_count) in self_evaluation_counts:
                num_self_evaluation_per_student[user_id] = comment_count

        # {'gradebook':[{user1}. {user2}, ...]}
        # user id, username, first name, last name, answer submitted, comparisons submitted
        gradebook = []
        for (student, grade) in students:
            entry = {
                'user': student,
                'num_answers': num_answers_per_student.get(student.id, 0),
                'num_comparisons': num_comparisons_per_student.get(student.id, 0),
                'grade': grade * 100 if grade else 0,
                'flagged': flagged_by_user_id.get(student.id, 'No Answer'),
                'file': file_by_user_id.get(student.id, None),
            }
            if include_scores:
                entry['score'] = scores_by_user_id.get(student.id, 'No Answer')
            if include_self_evaluation:
                entry['num_self_evaluation'] = num_self_evaluation_per_student.get(student.id, 0)
            gradebook.append(entry)

        on_gradebook_get.send(
            self,
            event_name=on_gradebook_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {
            'gradebook': marshal(gradebook, dataformat.get_gradebook(
                include_scores=include_scores, include_self_evaluation=include_self_evaluation)),
            'total_comparisons_required': assignment.total_comparisons_required,
            'include_scores': include_scores,
            'include_self_evaluation': include_self_evaluation
        }


api.add_resource(GradebookAPI, '')
