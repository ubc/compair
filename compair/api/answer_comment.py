from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask_bouncer import can
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import and_, or_

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require
from compair.models import User, Answer, Assignment, Course, AnswerComment, \
    CourseRole, SystemRole, AnswerCommentType
from .util import new_restful_api, get_model_changes, pagination_parser

answer_comment_api = Blueprint('answer_comment_api', __name__)
api = new_restful_api(answer_comment_api)

new_answer_comment_parser = RequestParser()
new_answer_comment_parser.add_argument('user_id', default=None)
new_answer_comment_parser.add_argument('content')
new_answer_comment_parser.add_argument('comment_type', required=True, nullable=False)
new_answer_comment_parser.add_argument('draft', type=bool, default=False)
new_answer_comment_parser.add_argument('evaluation_number', type=int, default=None)
new_answer_comment_parser.add_argument('attempt_uuid', default=None)
new_answer_comment_parser.add_argument('attempt_started', default=None)
new_answer_comment_parser.add_argument('attempt_ended', default=None)

existing_answer_comment_parser = new_answer_comment_parser.copy()
existing_answer_comment_parser.add_argument('id', required=True, help="Comment id is required.")

answer_comment_list_parser = pagination_parser.copy()
answer_comment_list_parser.add_argument('self_evaluation', required=False, default='true')
answer_comment_list_parser.add_argument('evaluation', required=False, default='true')
answer_comment_list_parser.add_argument('draft', required=False, default='false')
answer_comment_list_parser.add_argument('ids', required=False, default=None)
answer_comment_list_parser.add_argument('answer_ids', required=False, default=None)
answer_comment_list_parser.add_argument('assignment_id', required=False, default=None)
answer_comment_list_parser.add_argument('user_ids', required=False, default=None)

# events
on_answer_comment_modified = event.signal('ANSWER_COMMENT_MODIFIED')
on_answer_comment_get = event.signal('ANSWER_COMMENT_GET')
on_answer_comment_list_get = event.signal('ANSWER_COMMENT_LIST_GET')
on_answer_comment_create = event.signal('ANSWER_COMMENT_CREATE')
on_answer_comment_delete = event.signal('ANSWER_COMMENT_DELETE')

class AnswerCommentListAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid, **kwargs):
        """
        :query string ids: a comma separated comment uuids to query
        :query string answer_ids: a comma separated answer uuids for answer filter
        :query string assignment_id: filter the answer comments with a assignment uuid
        :query string user_ids: a comma separated user uuids that own the comments
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
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        restrict_user = not can(MANAGE, assignment)

        params = answer_comment_list_parser.parse_args()
        answer_uuids = []
        if 'answer_uuid' in kwargs:
            answer_uuids.append(kwargs['answer_uuid'])
        elif 'answer_ids' in params and params['answer_ids']:
            answer_uuids.extend(params['answer_ids'].split(','))

        if not answer_uuids and not params['ids'] and not params['assignment_id'] and not params['user_ids']:
            abort(404, title="Feedback Unavailable", message="There was a problem getting the feedback for this answer. Please try again.")

        conditions = []

        answers = Answer.query \
            .filter(
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.draft == False,
                Answer.uuid.in_(answer_uuids)
            ) \
            .all() if answer_uuids else []
        if answer_uuids and not answers:
            # non-existing answer ids.
            abort(404, title="Feedback Unavailable", message="There was a problem getting the feedback for this answer. Please try again.")

        group = current_user.get_course_group(course.id)
        course_role = current_user.get_course_role(course.id)

        # build query condition for each answer
        for answer in answers:
            clauses = [AnswerComment.answer_id == answer.id]

            # student can only see the comments for themselves or public ones.
            # since the owner of the answer can access all comments. We only filter
            # on non-owners
            answer_owner = answer.user_id == current_user.id or (group and group.id == answer.group_id)
            if course_role == CourseRole.student and not answer_owner:
                # public comments or comments owned by current user
                clauses.append(or_(
                    AnswerComment.comment_type == AnswerCommentType.public,
                    AnswerComment.user_id == current_user.id
                ))

            conditions.append(and_(*clauses))

        query = AnswerComment.query \
            .filter(
                AnswerComment.assignment_id == assignment.id,
                AnswerComment.active==True,
                or_(*conditions)
            )

        if params['ids']:
            query = query.filter(AnswerComment.uuid.in_(params['ids'].split(',')))

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

        if params['user_ids']:
            user_ids = params['user_ids'].split(',')
            query = query \
                .join(User, AnswerComment.user_id == User.id) \
                .filter(User.uuid.in_(user_ids))

        answer_comments = query.order_by(AnswerComment.created.desc()).all()

        # checking the permission
        for answer_comment in answer_comments:
            require(READ, answer_comment.answer,
                title="Feedback Unavailable",
                message="Sorry, your role in this course does not allow you to view feedback for this answer.")

        on_answer_comment_list_get.send(
            self,
            event_name=on_answer_comment_list_get.name,
            user=current_user,
            data={'answer_ids': ','.join([str(answer.id) for answer in answers])})

        return marshal(answer_comments, dataformat.get_answer_comment(restrict_user))

    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid):
        """
        Create comment for an answer
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        require(CREATE, AnswerComment(course_id=course.id),
            title="Feedback Not Saved",
            message="Sorry, your role in this course does not allow you to save feedback for this answer.")

        restrict_user = not can(MANAGE, assignment)

        restrict_user = not can(MANAGE, assignment)

        answer_comment = AnswerComment(answer_id=answer.id)

        params = new_answer_comment_parser.parse_args()
        answer_comment.draft = params.get('draft')
        answer_comment.content = params.get("content")
        # require content not empty if not a draft
        if not answer_comment.content and not answer_comment.draft:
            abort(400, title="Feedback Not Saved", message="Please provide content in the text editor and try saving again.")

        if params.get('user_id') and current_user.system_role == SystemRole.sys_admin:
            user = User.get_by_uuid_or_404(params.get('user_id'))
            answer_comment.user_id = user.id
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
            abort(400, title="Feedback Not Saved", message="This feedback type is not recognized. Please contact support for assistance.")
        answer_comment.comment_type = AnswerCommentType(comment_type)

        if answer_comment.comment_type == AnswerCommentType.self_evaluation and not assignment.self_eval_grace and not can(MANAGE, assignment):
            abort(403, title="Self-Evaluation Not Saved", message="Sorry, the self-evaluation deadline has passed and therefore cannot be submitted.")

        answer_comment.update_attempt(
            params.get('attempt_uuid'),
            params.get('attempt_started', None),
            params.get('attempt_ended', None)
        )

        db.session.add(answer_comment)
        db.session.commit()

        # update course & assignment grade for user if self-evaluation is completed
        if not answer_comment.draft and answer_comment.comment_type == AnswerCommentType.self_evaluation:
            assignment.calculate_grade(answer_comment.user)
            course.calculate_grade(answer_comment.user)

        on_answer_comment_create.send(
            self,
            event_name=on_answer_comment_create.name,
            user=current_user,
            course_id=course.id,
            answer_comment=answer_comment,
            evaluation_number=params.get("evaluation_number"),
            data=marshal(answer_comment, dataformat.get_answer_comment(restrict_user)))

        return marshal(answer_comment, dataformat.get_answer_comment(restrict_user))

api.add_resource(
    AnswerCommentListAPI,
    '/answers/<answer_uuid>/comments', '/answer_comments',
    endpoint='answer_comments')


class AnswerCommentAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        """
        Get an answer comment
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        answer_comment = AnswerComment.get_active_by_uuid_or_404(answer_comment_uuid)
        require(READ, answer_comment,
            title="Feedback Unavailable",
            message="Sorry, your role in this course does not allow you to view this feedback.")

        restrict_user = not can(MANAGE, assignment)

        restrict_user = not can(MANAGE, assignment)

        on_answer_comment_get.send(
            self,
            event_name=on_answer_comment_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id, 'answer_id': answer.id, 'answer_comment_id': answer_comment.id})

        return marshal(answer_comment, dataformat.get_answer_comment(restrict_user))

    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        """
        Update an answer comment
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        answer_comment = AnswerComment.get_active_by_uuid_or_404(answer_comment_uuid)
        require(EDIT, answer_comment,
            title="Feedback Not Saved",
            message="Sorry, your role in this course does not allow you to save feedback for this answer.")

        restrict_user = not can(MANAGE, assignment)

        restrict_user = not can(MANAGE, assignment)

        was_draft = answer_comment.draft

        params = existing_answer_comment_parser.parse_args()
        # make sure the answer comment id in the url and the id matches
        if params['id'] != answer_comment_uuid:
            abort(400, title="Feedback Not Saved", message="The feedback's ID does not match the URL, which is required in order to save the feedback.")

        # modify answer comment according to new values, preserve original values if values not passed
        answer_comment.content = params.get("content")

        comment_types = [
            AnswerCommentType.public.value,
            AnswerCommentType.private.value,
            AnswerCommentType.evaluation.value,
            AnswerCommentType.self_evaluation.value
        ]

        eval_comment_types = [
            AnswerCommentType.evaluation.value,
            AnswerCommentType.self_evaluation.value
        ]

        comment_type = params.get("comment_type", AnswerCommentType.private.value)
        if comment_type not in comment_types:
            abort(400, title="Feedback Not Saved", message="This feedback type is not recognized. Please contact support for assistance.")

        # do not allow changing a self-eval into a comment or vise-versa
        if (answer_comment.comment_type.value in eval_comment_types or comment_type in eval_comment_types) and answer_comment.comment_type.value != comment_type:
            abort(400, title="Feedback Not Saved", message="Feedback type cannot be changed. Please contact support for assistance.")

        answer_comment.comment_type = AnswerCommentType(comment_type)

        if answer_comment.comment_type == AnswerCommentType.self_evaluation and not assignment.self_eval_grace and not can(MANAGE, assignment):
            abort(403, title="Self-Evaluation Not Saved", message="Sorry, the self-evaluation deadline has passed and therefore cannot be submitted.")

        # only update draft param if currently a draft
        if answer_comment.draft:
            answer_comment.draft = params.get('draft', answer_comment.draft)

        # require content not empty if not a draft
        if not answer_comment.content and not answer_comment.draft:
            abort(400, title="Feedback Not Saved", message="Please provide content in the text editor and try saving again.")

        answer_comment.update_attempt(
            params.get('attempt_uuid'),
            params.get('attempt_started', None),
            params.get('attempt_ended', None)
        )

        model_changes = get_model_changes(answer_comment)
        db.session.add(answer_comment)
        db.session.commit()

        on_answer_comment_modified.send(
            self,
            event_name=on_answer_comment_modified.name,
            user=current_user,
            course_id=course.id,
            answer_comment=answer_comment,
            evaluation_number=params.get("evaluation_number"),
            was_draft=was_draft,
            data=model_changes)

        # update course & assignment grade for user if self-evaluation is completed
        if not answer_comment.draft and answer_comment.comment_type == AnswerCommentType.self_evaluation:
            assignment.calculate_grade(answer_comment.user)
            course.calculate_grade(answer_comment.user)

        return marshal(answer_comment, dataformat.get_answer_comment(restrict_user))

    @login_required
    def delete(self, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        """
        Delete an answer comment
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer_comment = AnswerComment.get_active_by_uuid_or_404(answer_comment_uuid)
        require(DELETE, answer_comment,
            title="Feedback Not Deleted",
            message="Sorry, your role in this course does not allow you to delete feedback for this answer.")

        data = marshal(answer_comment, dataformat.get_answer_comment(False))
        answer_comment.active = False
        db.session.commit()

        # update course & assignment grade for user if self-evaluation is completed
        if not answer_comment.draft and answer_comment.comment_type == AnswerCommentType.self_evaluation:
            assignment.calculate_grade(answer_comment.user)
            course.calculate_grade(answer_comment.user)

        on_answer_comment_delete.send(
            self,
            event_name=on_answer_comment_delete.name,
            user=current_user,
            course_id=course.id,
            answer_comment=answer_comment,
            data=data)

        return {'id': answer_comment.uuid}

api.add_resource(AnswerCommentAPI, '/answers/<answer_uuid>/comments/<answer_comment_uuid>')
