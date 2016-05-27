from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, abort
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import and_, or_
from sqlalchemy.orm import load_only, joinedload, contains_eager

from . import dataformat
from acj.core import db
from acj.authorization import require, allow, USER_IDENTITY
from acj.core import event
from acj.models import Assignment, Course, AssignmentComment
from .util import new_restful_api, get_model_changes, pagination_parser

assignment_comment_api = Blueprint('assignment_comment_api', __name__)
api = new_restful_api(assignment_comment_api)

new_assignment_comment_parser = RequestParser()
new_assignment_comment_parser.add_argument('content', type=str, required=True)

existing_assignment_comment_parser = new_assignment_comment_parser.copy()
existing_assignment_comment_parser.add_argument('id', type=int, required=True, help="Comment id is required.")

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
    def get(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, assignment)
        restrict_user = not allow(MANAGE, assignment)

        assignment_comments = AssignmentComment.query \
            .filter_by(
                course_id=course_id,
                assignment_id=assignment_id,
                active=True
            ) \
            .order_by(AssignmentComment.created.asc()).all()

        on_assignment_comment_list_get.send(
            self,
            event_name=on_assignment_comment_list_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id})

        return {"objects": marshal(assignment_comments, dataformat.get_assignment_comment(restrict_user))}

    @login_required
    def post(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        require(CREATE, AssignmentComment(course_id=course_id))
        
        new_assignment_comment = AssignmentComment(assignment_id=assignment_id)
        
        params = new_assignment_comment_parser.parse_args()
        
        new_assignment_comment.content = params.get("content")
        if not new_assignment_comment.content:
            return {"error": "The comment content is empty!"}, 400
            
        new_assignment_comment.user_id = current_user.id
        
        db.session.add(new_assignment_comment)

        on_assignment_comment_create.send(
            self,
            event_name=on_assignment_comment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(new_assignment_comment, dataformat.get_assignment_comment(False)))

        db.session.commit()
        return marshal(new_assignment_comment, dataformat.get_assignment_comment())

api.add_resource(AssignmentCommentRootAPI, '')


# / id
class AssignmentCommentIdAPI(Resource):
    @login_required
    
    def get(self, course_id, assignment_id, assignment_comment_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        
        assignment_comment = AssignmentComment.get_active_or_404(assignment_comment_id)
            
        require(READ, assignment_comment)

        on_assignment_comment_get.send(
            self,
            event_name=on_assignment_comment_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'assignment_comment_id': assignment_comment_id})

        return marshal(assignment_comment, dataformat.get_assignment_comment())

    @login_required
    def post(self, course_id, assignment_id, assignment_comment_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        
        assignment_comment = AssignmentComment.get_active_or_404(assignment_comment_id)
            
        require(EDIT, assignment_comment)

        params = existing_assignment_comment_parser.parse_args()
        # make sure the comment id in the rul and the id matches
        if params['id'] != assignment_comment_id:
            return {"error": "Comment id does not match URL."}, 400
            
        # modify comment according to new values, preserve original values if values not passed
        if not params.get("content"):
            return {"error": "The comment content is empty!"}, 400
        
        assignment_comment.content = params.get("content")
        db.session.add(assignment_comment)

        on_assignment_comment_modified.send(
            self,
            event_name=on_assignment_comment_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(assignment_comment))

        db.session.commit()
        return marshal(assignment_comment, dataformat.get_assignment_comment())

    @login_required
    def delete(self, course_id, assignment_id, assignment_comment_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        
        assignment_comment = AssignmentComment.get_active_or_404(assignment_comment_id)
            
        require(DELETE, assignment_comment)
        data = marshal(assignment_comment, dataformat.get_assignment_comment(False))
        assignment_comment.active = False
        db.session.commit()

        on_assignment_comment_delete.send(
            self,
            event_name=on_assignment_comment_delete.name,
            user=current_user,
            course_id=course_id,
            data=data)

        return {'id': assignment_comment.id}
        
api.add_resource(AssignmentCommentIdAPI, '/<int:assignment_comment_id>')

