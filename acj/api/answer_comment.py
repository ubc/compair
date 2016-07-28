from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, abort
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import and_, or_

from . import dataformat
from acj.core import db, event
from acj.authorization import require, allow, USER_IDENTITY
from acj.models import Answer, Assignment, Course, AnswerComment, CourseRole, SystemRole, AnswerCommentType
from .util import new_restful_api, get_model_changes, pagination_parser

answer_comment_api = Blueprint('answer_comment_api', __name__)
api = new_restful_api(answer_comment_api)

new_answer_comment_parser = RequestParser()
new_answer_comment_parser.add_argument('user_id', type=int, default=None)
new_answer_comment_parser.add_argument('content', type=str)
new_answer_comment_parser.add_argument('comment_type', type=str, required=True)
new_answer_comment_parser.add_argument('draft', type=bool, default=False)

existing_answer_comment_parser = RequestParser()
existing_answer_comment_parser.add_argument('id', type=int, required=True, help="Comment id is required.")
existing_answer_comment_parser.add_argument('content', type=str)
existing_answer_comment_parser.add_argument('comment_type', type=str, required=True)
existing_answer_comment_parser.add_argument('draft', type=bool, default=False)

answer_comment_list_parser = pagination_parser.copy()
answer_comment_list_parser.add_argument('self_evaluation', type=str, required=False, default='true')
answer_comment_list_parser.add_argument('evaluation', type=str, required=False, default='true')
answer_comment_list_parser.add_argument('draft', type=str, required=False, default='false')
answer_comment_list_parser.add_argument('ids', type=str, required=False, default=None)
answer_comment_list_parser.add_argument('answer_ids', type=str, required=False, default=None)
answer_comment_list_parser.add_argument('assignment_id', type=int, required=False, default=None)
answer_comment_list_parser.add_argument('user_ids', type=str, required=False, default=None)

# events
on_answer_comment_modified = event.signal('ANSWER_COMMENT_MODIFIED')
on_answer_comment_get = event.signal('ANSWER_COMMENT_GET')
on_answer_comment_list_get = event.signal('ANSWER_COMMENT_LIST_GET')
on_answer_comment_create = event.signal('ANSWER_COMMENT_CREATE')
on_answer_comment_delete = event.signal('ANSWER_COMMENT_DELETE')

class AnswerCommentListAPI(Resource):
    @login_required
    def get(self, **kwargs):
        """
        **Example request**:

        .. sourcecode:: http

            GET /api/answer/123/comments HTTP/1.1
            Host: example.com
            Accept: application/json

        .. sourcecode:: http

            GET /api/answer_comments?ids=1,2,3&self_evaluation=only HTTP/1.1
            Host: example.com
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json
            [{
                'id': 1
                'content': 'comment text',
                'created': '',
                'user_id': 1,
                'user_displayname': 'John',
                'user_fullname': 'John Smith',
                'user_avatar': '12k3jjh24k32jhjksaf',
                'comment_type': 'self_evaluation',
                'course_id': 1,
            }]

        :query string ids: a comma separated comment IDs to query
        :query string answer_ids: a comma separated answer IDs for answer filter
        :query int assignment_id: filter the answer comments with a assignment
        :query string user_ids: a comma separated user IDs that own the comments
        :query string self_evaluation: indicate whether the result should include self-evaluation comments or self-evaluation only.
                Possible values: true, false or only. Default true.
        :query string evaluation: indicate whether the result should include evaluation comments or evaluation only.
                Possible values: true, false or only. Default true.
        :query string draft: indicate whether the result should include drafts for current user or not.
                Possible values: true, false or only. Default false.
        :reqheader Accept: the response content type depends on :mailheader:`Accept` header
        :resheader Content-Type: this depends on :mailheader:`Accept` header of request
        :statuscode 200: no error
        :statuscode 404: answers don't exist

        """
        params = answer_comment_list_parser.parse_args()
        answer_ids = []
        if 'answer_id' in kwargs:
            answer_ids.append(kwargs['answer_id'])
        elif 'answer_ids' in params and params['answer_ids']:
            answer_ids.extend(params['answer_ids'].split(','))

        if not answer_ids and not params['ids'] and not params['assignment_id'] and not params['user_ids']:
            abort(404)

        conditions = []

        answers = Answer.query. \
            filter_by(active=True). \
            filter_by(draft=False). \
            filter(Answer.id.in_(answer_ids)).all() if answer_ids else []
        if answer_ids and not answers:
            # non-existing answer ids. we return empty result
            abort(404)

        # build query condition for each answer
        for answer in answers:
            clauses = [AnswerComment.answer_id == answer.id]

            # student can only see the comments for themselves or public ones.
            # since the owner of the answer can access all comments. We only filter
            # on non-owners
            if current_user.get_course_role(answer.course_id) == CourseRole.student \
                    and answer.user_id != current_user.id:
                # public comments or comments owned by current user
                clauses.append(or_(
                    AnswerComment.comment_type == AnswerCommentType.public,
                    AnswerComment.user_id == current_user.id
                ))

            conditions.append(and_(*clauses))

        query = AnswerComment.query. \
            filter(AnswerComment.active==True) .\
            filter(or_(*conditions))

        if params['ids']:
            query = query.filter(AnswerComment.id.in_(params['ids'].split(',')))

        if params['self_evaluation'] == 'false':
            # do not include self-evaluation
            query = query.filter(AnswerComment.comment_type != AnswerCommentType.self_evaluation)
        elif params['self_evaluation'] == 'only':
            # only self_evaluation
            query = query.filter(AnswerComment.comment_type == AnswerCommentType.self_evaluation)

        if params['evaluation'] == 'false':
            # do not include evalulation comments
            query = query.filter(AnswerComment.comment_type != AnswerCommentType.evaluation)
        elif params['evaluation'] == 'only':
            # only evaluation
            query = query.filter(AnswerComment.comment_type == AnswerCommentType.evaluation)

        if params['draft'] == 'true':
            # with draft (current_user)
            query = query.filter(or_(
                AnswerComment.draft == False,
                and_(
                    AnswerComment.draft == True,
                    AnswerComment.user_id == current_user.id
                )
            ))
        elif params['draft'] == 'only':
            # only draft (current_user)
            query = query.filter(and_(
                AnswerComment.draft == True,
                AnswerComment.user_id == current_user.id
            ))
        else:
            # do not include draft. Default
            query = query.filter(AnswerComment.draft == False)

        if params['assignment_id']:
            query = query.join(AnswerComment.answer). \
                filter_by(assignment_id=params['assignment_id'])

        if params['user_ids']:
            user_ids = params['user_ids'].split(',')
            query = query.filter(AnswerComment.user_id.in_(user_ids))

        answer_comments = query.order_by(AnswerComment.created.desc()).all()

        # checking the permission
        for answer_comment in answer_comments:
            require(READ, answer_comment.answer)

        on_answer_comment_list_get.send(
            self,
            event_name=on_answer_comment_list_get.name,
            user=current_user,
            data={'answer_ids': ','.join([str(answer_id) for answer_id in answer_ids])})

        return marshal(answer_comments, dataformat.get_answer_comment(not allow(READ, USER_IDENTITY)))

    @login_required
    def post(self, course_id, assignment_id, answer_id):
        """
        Create comment for an answer
        """
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        Answer.get_active_or_404(answer_id)
        require(CREATE, AnswerComment(course_id=course_id))

        answer_comment = AnswerComment(answer_id=answer_id)

        params = new_answer_comment_parser.parse_args()
        answer_comment.draft = params.get('draft')
        answer_comment.content = params.get("content")
        # require content not empty if not a draft
        if not answer_comment.content and not answer_comment.draft:
            return {"error": "The comment content is empty!"}, 400

        if params.get('user_id') and current_user.system_role == SystemRole.sys_admin:
            answer_comment.user_id = params.get('user_id')
        else:
            answer_comment.user_id = current_user.id

        comment_types = [
            AnswerCommentType.public.value,
            AnswerCommentType.private.value,
            AnswerCommentType.evaluation.value,
            AnswerCommentType.self_evaluation.value
        ]

        comment_type = params.get("comment_type")
        if comment_type not in comment_types:
            abort(400)
        answer_comment.comment_type = AnswerCommentType(comment_type)

        db.session.add(answer_comment)
        db.session.commit()

        on_answer_comment_create.send(
            self,
            event_name=on_answer_comment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(answer_comment, dataformat.get_answer_comment(False)))

        return marshal(answer_comment, dataformat.get_answer_comment())

api.add_resource(
    AnswerCommentListAPI,
    '/answers/<int:answer_id>/comments', '/answer_comments',
    endpoint='answer_comments')


class AnswerCommentAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id, answer_id, answer_comment_id):
        """
        Get an answer comment
        """
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        Answer.get_active_or_404(answer_id)

        answer_comment = AnswerComment.get_active_or_404(answer_comment_id)
        require(READ, answer_comment)

        on_answer_comment_get.send(
            self,
            event_name=on_answer_comment_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'answer_id': answer_id, 'answer_comment_id': answer_comment_id})

        return marshal(answer_comment, dataformat.get_answer_comment())

    @login_required
    def post(self, course_id, assignment_id, answer_id, answer_comment_id):
        """
        Create an answer comment
        """
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        Answer.get_active_or_404(answer_id)

        answer_comment = AnswerComment.get_active_or_404(answer_comment_id)
        require(EDIT, answer_comment)

        params = existing_answer_comment_parser.parse_args()
        # make sure the answer comment id in the url and the id matches
        if params['id'] != answer_comment_id:
            return {"error": "Comment id does not match URL."}, 400

        # modify answer comment according to new values, preserve original values if values not passed
        answer_comment.content = params.get("content")

        comment_types = [
            AnswerCommentType.public.value,
            AnswerCommentType.private.value,
            AnswerCommentType.evaluation.value,
            AnswerCommentType.self_evaluation.value
        ]

        comment_type = params.get("comment_type", AnswerCommentType.private.value)
        if comment_type not in comment_types:
            abort(400)

        answer_comment.comment_type = AnswerCommentType(comment_type)
        # only update draft param if currently a draft
        if answer_comment.draft:
            answer_comment.draft = params.get('draft', answer_comment.draft)

        # require content not empty if not a draft
        if not answer_comment.content and not answer_comment.draft:
            return {"error": "The comment content is empty!"}, 400

        db.session.add(answer_comment)

        on_answer_comment_modified.send(
            self,
            event_name=on_answer_comment_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(answer_comment))

        db.session.commit()
        return marshal(answer_comment, dataformat.get_answer_comment())

    @login_required
    def delete(self, course_id, assignment_id, answer_id, answer_comment_id):
        """
        Delete an answer comment
        """
        answer_comment = AnswerComment.get_active_or_404(answer_comment_id)
        require(DELETE, answer_comment)

        data = marshal(answer_comment, dataformat.get_answer_comment(False))
        answer_comment.active = False
        db.session.commit()

        on_answer_comment_delete.send(
            self,
            event_name=on_answer_comment_delete.name,
            user=current_user,
            course_id=course_id,
            data=data)

        return {'id': answer_comment.id}

api.add_resource(AnswerCommentAPI, '/answers/<int:answer_id>/comments/<int:answer_comment_id>')
