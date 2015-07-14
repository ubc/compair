from __future__ import division

import copy

from bouncer.constants import MANAGE
from flask import Blueprint, jsonify
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource
from sqlalchemy import func, and_
from sqlalchemy.orm import load_only, undefer, joinedload

from .authorization import require
from .models import Courses, PostsForQuestions, UserTypesForCourse, Users, CoursesAndUsers, Judgements, \
    AnswerPairings, PostsForAnswersAndPostsForComments, PostsForAnswers, Posts, Scores, \
    PostsForComments
from .util import new_restful_api
from .core import event



# First declare a Flask Blueprint for this module
gradebook_api = Blueprint('gradebook_api', __name__)
# Then pack the blueprint into a Flask-Restful API
api = new_restful_api(gradebook_api)

# events
on_gradebook_get = event.signal('GRADEBOOK_GET')


def normalize_score(score, max_score, ndigits=0):
    return round(score / max_score, ndigits) if max_score is not 0 else 0


# declare an API URL
# /
class GradebookAPI(Resource):
    @login_required
    def get(self, course_id, question_id):
        Courses.query.options(load_only('id')).get_or_404(course_id)
        question = PostsForQuestions.query.\
            options(undefer('criteria_count')).\
            options(joinedload('_criteria')).\
            get_or_404(question_id)
        require(MANAGE, question)

        # get all students in this course
        # student_type = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first()
        students = Users.query. \
            with_entities(Users.id, Users.displayname, Users.firstname, Users.lastname). \
            join(CoursesAndUsers). \
            join(UserTypesForCourse). \
            filter(
                CoursesAndUsers.courses_id == course_id,
                CoursesAndUsers.usertypesforcourse_id == UserTypesForCourse.id,
                UserTypesForCourse.name == UserTypesForCourse.TYPE_STUDENT). \
            all()

        student_ids = [student.id for student in students]
        # get students judgements counts for this question
        judgements = Users.query. \
            with_entities(Users.id, func.count(Judgements.id).label('judgement_count')). \
            outerjoin(Judgements). \
            outerjoin(AnswerPairings, and_(
                AnswerPairings.id == Judgements.answerpairings_id,
                AnswerPairings.questions_id == question_id)). \
            filter(Users.id.in_(student_ids)).\
            group_by(Users.id).all()

        # we want only the count for judgements by current students in the course
        num_judgements_per_student = {user_id: int(judgement_count/question.criteria_count)
                                      for (user_id, judgement_count) in judgements}

        # count number of answers each student has submitted
        answers = Users.query. \
            with_entities(Users.id, func.count(PostsForAnswers.id).label('answer_count')). \
            outerjoin(Posts). \
            outerjoin(PostsForAnswers, and_(
                PostsForAnswers.posts_id == Posts.id,
                PostsForAnswers.questions_id == question_id)). \
            filter(Users.id.in_(student_ids)). \
            group_by(Users.id).all()

        num_answers_per_student = dict(answers)

        # find out the scores that students get
        criteria_ids = [c.id for c in question.criteria]
        scores_by_user = Users.query. \
            with_entities(Users.id, PostsForAnswers.flagged, Scores.criteriaandquestions_id, Scores.normalized_score). \
            outerjoin(Posts). \
            join(PostsForAnswers, and_(
                PostsForAnswers.posts_id == Posts.id,
                PostsForAnswers.questions_id == question_id)). \
            outerjoin(Scores, and_(
                PostsForAnswers.id == Scores.answers_id,
                Scores.criteriaandquestions_id.in_(criteria_ids))). \
            filter(Users.id.in_(student_ids)). \
            all()

        # process the results into dicts
        scores_by_user_id = {}
        flagged_by_user_id = {}
        init_scores = {c.id: 'Not Evaluated' for c in question.criteria}
        for score in scores_by_user:
            scores_by_user_id[score[0]] = copy.deepcopy(init_scores)
            if score[2] is not None:
                # scores_by_user_id[score[0]][score[2]] = normalize_score(score[3], max_scores.get(score[2], 0), 3)
                scores_by_user_id[score[0]][score[2]] = score[3]
            flagged_by_user_id[score[0]] = 'Yes' if score[1] else 'No'

        include_self_eval = False
        num_selfeval_per_student = {}
        if question.selfevaltype_id:
            include_self_eval = True
            # assuming self-evaluation with no comparison
            stmt = Posts.query. \
                with_entities(Posts.users_id, func.count('*').label('comment_count')). \
                join(PostsForComments). \
                join(PostsForAnswersAndPostsForComments, and_(
                    PostsForAnswersAndPostsForComments.comments_id == PostsForComments.id,
                    PostsForAnswersAndPostsForComments.selfeval)). \
                join(PostsForAnswers, and_(
                    PostsForAnswers.id == PostsForAnswersAndPostsForComments.answers_id,
                    PostsForAnswers.questions_id == question_id)) .\
                group_by(Posts.users_id).subquery()

            comments_by_user_id = Users.query. \
                with_entities(Users.id, stmt.c.comment_count). \
                outerjoin(stmt, Users.id == stmt.c.users_id). \
                filter(Users.id.in_(student_ids)). \
                order_by(Users.id). \
                all()

            num_selfeval_per_student = dict(comments_by_user_id)
            num_selfeval_per_student.update((k, 0) for k, v in num_selfeval_per_student.items() if v is None)

        # {'gradebook':[{user1}. {user2}, ...]}
        # user id, username, first name, last name, answer submitted, judgements submitted
        gradebook = []
        no_answer = {c.id: 'No Answer' for c in question.criteria}
        for student in students:
            entry = {
                'userid': student.id,
                'displayname': student.displayname,
                'firstname': student.firstname,
                'lastname': student.lastname,
                'num_answers': num_answers_per_student[student.id],
                'num_judgements': num_judgements_per_student[student.id],
                'scores': scores_by_user_id.get(student.id, no_answer),
                'flagged': flagged_by_user_id.get(student.id, 'No Answer')
            }
            if include_self_eval:
                entry['num_selfeval'] = num_selfeval_per_student[student.id]
            gradebook.append(entry)

        ret = {
            'gradebook': gradebook,
            'num_judgements_required': question.num_judgement_req,
            'include_self_eval': include_self_eval
        }

        on_gradebook_get.send(
            self,
            event_name=on_gradebook_get.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id})

        return jsonify(ret)


api.add_resource(GradebookAPI, '')
