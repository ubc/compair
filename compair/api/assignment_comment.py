from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import and_, or_

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require, allow
from compair.models import Assignment, Course, AssignmentComment
from .util import new_restful_api, get_model_changes, pagination_parser

assignment_comment_api = Blueprint('assignment_comment_api', __name__)
api = new_restful_api(assignment_comment_api)

new_assignment_comment_parser = RequestParser()
new_assignment_comment_parser.add_argument('content', required=True)

existing_assignment_comment_parser = new_assignment_comment_parser.copy()
existing_assignment_comment_parser.add_argument('id', required=True, help="Comment id is required.")

# events
on_assignment_comment_modified = event.signal('ASSIGNMENT_COMMENT_MODIFIED')
on_assignment_comment_get = event.signal('ASSIGNMENT_COMMENT_GET')
on_assignment_comment_list_get = event.signal('ASSIGNMENT_COMMENT_LIST_GET')
on_assignment_comment_create = event.signal('ASSIGNMENT_COMMENT_CREATE')
on_assignment_comment_delete = event.signal('ASSIGNMENT_COMMENT_DELETE')


# /
class AssignmentCommentRootAPI(Resource):
    # TODO pagination
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Help Comments Unavailable",
            message="Help comments can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not allow(MANAGE, assignment)

        assignment_comments = AssignmentComment.query \
            .filter_by(
                course_id=course.id,
                assignment_id=assignment.id,
                active=True
            ) \
            .order_by(AssignmentComment.created.asc()).all()

        on_assignment_comment_list_get.send(
            self,
            event_name=on_assignment_comment_list_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {"objects": marshal(assignment_comments, dataformat.get_assignment_comment(restrict_user))}

    @login_required
    def post(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(CREATE, AssignmentComment(course_id=course.id),
            title="Help Comment Not Saved",
            message="Help comments can be left only by those enrolled in the course. Please double-check your enrollment in this course.")

        new_assignment_comment = AssignmentComment(assignment_id=assignment.id)

        params = new_assignment_comment_parser.parse_args()

        new_assignment_comment.content = params.get("content")
        if not new_assignment_comment.content:
            abort(400, title="Help Comment Not Saved", message="Please provide content in the text editor to leave this comment.")

        new_assignment_comment.user_id = current_user.id

        db.session.add(new_assignment_comment)
        db.session.commit()

        on_assignment_comment_create.send(
            self,
            event_name=on_assignment_comment_create.name,
            user=current_user,
            course_id=course.id,
            assignment_comment=new_assignment_comment,
            data=marshal(new_assignment_comment, dataformat.get_assignment_comment(False)))

        return marshal(new_assignment_comment, dataformat.get_assignment_comment())

api.add_resource(AssignmentCommentRootAPI, '')


# / id
class AssignmentCommentIdAPI(Resource):
    @login_required

    def get(self, course_uuid, assignment_uuid, assignment_comment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        assignment_comment = AssignmentComment.get_active_by_uuid_or_404(assignment_comment_uuid)
        require(READ, assignment_comment,
            title="Help Comment Unavailable",
            message="Your role in this course does not allow you to view help comments.")

        on_assignment_comment_get.send(
            self,
            event_name=on_assignment_comment_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id, 'assignment_comment_id': assignment_comment.id})

        return marshal(assignment_comment, dataformat.get_assignment_comment())

    @login_required
    def post(self, course_uuid, assignment_uuid, assignment_comment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        assignment_comment = AssignmentComment.get_active_by_uuid_or_404(assignment_comment_uuid)
        require(EDIT, assignment_comment,
            title="Help Comment Not Updated",
            message="Your role in this course does not allow you to update help comments.")

        params = existing_assignment_comment_parser.parse_args()
        # make sure the comment id in the rul and the id matches
        if params['id'] != assignment_comment_uuid:
            abort(400, title="Help Comment Not Updated", message="The comment's ID does not match the URL, which is required in order to update the comment.")

        # modify comment according to new values, preserve original values if values not passed
        if not params.get("content"):
            abort(400, title="Help Comment Not Updated", message="Please provide content in the text editor to update this comment.")

        assignment_comment.content = params.get("content")
        db.session.add(assignment_comment)

        on_assignment_comment_modified.send(
            self,
            event_name=on_assignment_comment_modified.name,
            user=current_user,
            course_id=course.id,
            assignment_comment=assignment_comment,
            data=get_model_changes(assignment_comment))

        db.session.commit()
        return marshal(assignment_comment, dataformat.get_assignment_comment())

    @login_required
    def delete(self, course_uuid, assignment_uuid, assignment_comment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        assignment_comment = AssignmentComment.get_active_by_uuid_or_404(assignment_comment_uuid)
        require(DELETE, assignment_comment,
            title="Help Comment Not Deleted",
            message="Your role in this course does not allow you to delete help comments.")

        data = marshal(assignment_comment, dataformat.get_assignment_comment(False))
        assignment_comment.active = False
        db.session.commit()

        on_assignment_comment_delete.send(
            self,
            event_name=on_assignment_comment_delete.name,
            user=current_user,
            course_id=course.id,
            assignment_comment=assignment_comment,
            data=data)

        return {'id': assignment_comment.uuid}

api.add_resource(AssignmentCommentIdAPI, '/<assignment_comment_uuid>')

