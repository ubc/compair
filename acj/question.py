import datetime

import dateutil.parser
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload, undefer_group, contains_eager

from . import dataformat
from .core import db, event
from .authorization import allow, require
from .models import PostsForQuestions, Courses, Posts, \
    PostsForQuestionsAndSelfEvaluationTypes
from .util import new_restful_api, get_model_changes
from .attachment import add_new_file, delete_file


questions_api = Blueprint('questions_api', __name__)
api = new_restful_api(questions_api)

new_question_parser = RequestParser()
new_question_parser.add_argument('title', type=str, required=True, help="Question title is required.")
new_question_parser.add_argument('post', type=dict, default={})
new_question_parser.add_argument('answer_start', type=str, required=True)
new_question_parser.add_argument('answer_end', type=str, required=True)
new_question_parser.add_argument('judge_start', type=str, default=None)
new_question_parser.add_argument('judge_end', type=str, default=None)
new_question_parser.add_argument('name', type=str, default=None)
new_question_parser.add_argument('alias', type=str, default=None)
new_question_parser.add_argument('can_reply', type=bool, default=False)
new_question_parser.add_argument('num_judgement_req', type=int, required=True)
new_question_parser.add_argument('selfevaltype_id', type=int, default=None)

# existing_question_parser = new_question_parser.copy()
existing_question_parser = RequestParser()
existing_question_parser.add_argument('id', type=int, required=True, help="Question id is required.")
existing_question_parser.add_argument('title', type=str, required=True, help="Question title is required.")
existing_question_parser.add_argument('post', type=dict, default={})
existing_question_parser.add_argument('answer_start', type=str, required=True)
existing_question_parser.add_argument('answer_end', type=str, required=True)
existing_question_parser.add_argument('judge_start', type=str, default=None)
existing_question_parser.add_argument('judge_end', type=str, default=None)
existing_question_parser.add_argument('name', type=str, default=None)
existing_question_parser.add_argument('alias', type=str, default=None)
existing_question_parser.add_argument('uploadedFile', type=bool, default=False)
existing_question_parser.add_argument('can_reply', type=bool, default=False)
existing_question_parser.add_argument('num_judgement_req', type=int, required=True)
existing_question_parser.add_argument('selfevaltype_id', type=int, default=None)

# events
on_question_modified = event.signal('QUESTION_MODIFIED')
on_question_get = event.signal('QUESTION_GET')
on_question_list_get = event.signal('QUESTION_LIST_GET')
on_question_create = event.signal('QUESTION_CREATE')
on_question_delete = event.signal('QUESTION_DELETE')


# /id
class QuestionIdAPI(Resource):
    @login_required
    def get(self, course_id, question_id):
        Courses.query.get_or_404(course_id)
        if not question_id:
            question_id = 1
        question = PostsForQuestions.query.get_or_404(question_id)
        require(READ, question)
        now = datetime.datetime.utcnow()
        if question.answer_start and not allow(MANAGE, question) and not (question.answer_start <= now):
            return {"error": "The question is unavailable!"}, 403
        restrict_users = not allow(MANAGE, question)

        on_question_get.send(
            self,
            event_name=on_question_get.name,
            user=current_user,
            course_id=course_id,
            data={'id': question_id})

        return {
            'question': marshal(question, dataformat.get_posts_for_questions(restrict_users, include_answers=False))
        }

    @login_required
    def post(self, course_id, question_id):
        Courses.query.get_or_404(course_id)
        question = PostsForQuestions.query.get_or_404(question_id)
        require(EDIT, question)
        params = existing_question_parser.parse_args()
        # make sure the question id in the url and the id matches
        if params['id'] != question_id:
            return {"error": "Question id does not match URL."}, 400
        # modify question according to new values, preserve original values if values not passed
        question.post.content = params.get("post").get("content")
        # uploaded = params.get('uploadedFile')
        name = params.get('name')
        question.title = params.get("title", question.title)
        question.answer_start = datetime.datetime.strptime(
            params.get('answer_start', question.answer_start),
            '%Y-%m-%dT%H:%M:%S.%fZ')
        question.answer_end = datetime.datetime.strptime(
            params.get('answer_end', question.answer_end),
            '%Y-%m-%dT%H:%M:%S.%fZ')
        # if nothing in request, assume user don't want judgement date
        question.judge_start = params.get('judge_start', None)
        if question.judge_start is not None:
            question.judge_start = datetime.datetime.strptime(
                question.judge_start,
                '%Y-%m-%dT%H:%M:%S.%fZ')
        question.judge_end = params.get('judge_end', None)
        if question.judge_end is not None:
            question.judge_end = datetime.datetime.strptime(
                params.get('judge_end', question.judge_end),
                '%Y-%m-%dT%H:%M:%S.%fZ')
        question.can_reply = params.get('can_reply', False)
        question.num_judgement_req = params.get('num_judgement_req', question.num_judgement_req)
        selfevaltype_id = params.pop('selfevaltype_id', question.selfevaltype_id)
        db.session.add(question.post)
        db.session.add(question)

        on_question_modified.send(
            self,
            event_name=on_question_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(question))

        db.session.commit()
        if name:
            add_new_file(params.get('alias'), name, course_id, question.id, question.post.id)
        # assume one selfevaluation type per question
        eval_type = PostsForQuestionsAndSelfEvaluationTypes.query.filter_by(questions_id=question.id).first()
        if selfevaltype_id:
            if not eval_type:
                eval_type = PostsForQuestionsAndSelfEvaluationTypes(
                    selfevaltypes_id=selfevaltype_id,
                    questions_id=question.id)
            else:
                eval_type.selfevaltypes_id = selfevaltype_id
            db.session.add(eval_type)
        elif not selfevaltype_id and eval_type:
            db.session.delete(eval_type)
        db.session.commit()

        return marshal(question, dataformat.get_posts_for_questions(include_answers=False))

    @login_required
    def delete(self, course_id, question_id):
        question = PostsForQuestions.query.get_or_404(question_id)
        require(DELETE, question)
        formatted_question = marshal(question, dataformat.get_posts_for_questions(False, False))
        # delete file when question is deleted
        delete_file(question.post.id)
        db.session.delete(question)
        db.session.commit()

        on_question_delete.send(
            self,
            event_name=on_question_delete.name,
            user=current_user,
            course_id=course_id,
            data=formatted_question)

        return {'id': question.id}

api.add_resource(QuestionIdAPI, '/<int:question_id>')


# /
class QuestionRootAPI(Resource):
    # TODO Pagination
    @login_required
    def get(self, course_id):
        course = Courses.query.get_or_404(course_id)
        require(READ, course)
        # Get all questions for this course, default order is most recent first
        post = Posts(courses_id=course_id)
        question = PostsForQuestions(post=post)
        base_query = PostsForQuestions.query. \
            options(joinedload("criteria").joinedload("criterion")). \
            options(joinedload("selfevaltype")). \
            options(undefer_group('counts')). \
            join(Posts). \
            options(contains_eager('post').joinedload("user").joinedload('usertypeforsystem')). \
            options(contains_eager('post').joinedload("files")). \
            filter(Posts.courses_id == course_id). \
            order_by(desc(Posts.created))
        if allow(MANAGE, question):
            questions = base_query.all()
        else:
            now = datetime.datetime.utcnow()
            questions = base_query. \
                filter(or_(PostsForQuestions.answer_start.is_(None), now >= PostsForQuestions.answer_start)).\
                all()

        restrict_users = not allow(MANAGE, question)

        on_question_list_get.send(
            self,
            event_name=on_question_list_get.name,
            user=current_user,
            course_id=course_id)

        return {
            "questions": marshal(questions, dataformat.get_posts_for_questions(restrict_users, include_answers=False))
        }

    @login_required
    def post(self, course_id):
        Courses.query.get_or_404(course_id)
        # check permission first before reading parser arguments
        post = Posts(courses_id=course_id)
        question = PostsForQuestions(post=post)
        require(CREATE, question)
        params = new_question_parser.parse_args()
        post.content = params.get("post").get("content")
        name = params.get('name')
        post.users_id = current_user.id
        question.title = params.get("title")
        question.answer_start = dateutil.parser.parse(params.get('answer_start'))
        question.answer_end = dateutil.parser.parse(params.get('answer_end'))
        question.judge_start = params.get('judge_start', None)
        if question.judge_start is not None:
            question.judge_start = dateutil.parser.parse(params.get('judge_start', None))
        question.judge_end = params.get('judge_end', None)
        if question.judge_end is not None:
            question.judge_end = dateutil.parser.parse(params.get('judge_end', None))
        question.can_reply = params.get('can_reply', False)
        question.num_judgement_req = params.get('num_judgement_req')
        selfevaltype_id = params.pop('selfevaltype_id', None)
        db.session.add(post)
        db.session.add(question)
        db.session.commit()
        if name:
            add_new_file(params.get('alias'), name, course_id, question.id, post.id)
        if selfevaltype_id:
            eval_type = PostsForQuestionsAndSelfEvaluationTypes(
                selfevaltypes_id=selfevaltype_id,
                questions_id=question.id)
            db.session.add(eval_type)
            db.session.commit()

        on_question_create.send(
            self,
            event_name=on_question_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(question, dataformat.get_posts_for_questions(False)))

        return marshal(question, dataformat.get_posts_for_questions(include_answers=False))

api.add_resource(QuestionRootAPI, '')
