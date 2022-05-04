from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import desc, or_, func, and_
from sqlalchemy.orm import joinedload, undefer_group, load_only

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require
from compair.models import Assignment, Course, Answer, ComparisonExample
from .util import new_restful_api, get_model_changes

comparison_example_api = Blueprint('comparison_example_api', __name__)
api = new_restful_api(comparison_example_api)

new_comparison_example_parser = RequestParser()
new_comparison_example_parser.add_argument('answer1_id', required=True, nullable=False)
new_comparison_example_parser.add_argument('answer2_id', required=True, nullable=False)

existing_comparison_example_parser = new_comparison_example_parser.copy()
existing_comparison_example_parser.add_argument('id', required=True, nullable=False)

# events
on_comparison_example_modified = event.signal('COMPARISON_EXAMPLE_MODIFIED')
on_comparison_example_list_get = event.signal('COMPARISON_EXAMPLE_LIST_GET')
on_comparison_example_create = event.signal('COMPARISON_EXAMPLE_CREATE')
on_comparison_example_delete = event.signal('COMPARISON_EXAMPLE_DELETE')

# /id
class ComparisonExampleIdAPI(Resource):
    @login_required
    def post(self, course_uuid, assignment_uuid, comparison_example_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        comparison_example = ComparisonExample.get_active_by_uuid_or_404(comparison_example_uuid)
        require(EDIT, comparison_example,
            title="Comparison Example Not Saved",
            message="Sorry, your role in this course does not allow you to save practice answers.")

        params = existing_comparison_example_parser.parse_args()
        answer1_uuid = params.get("answer1_id")
        answer2_uuid = params.get("answer2_id")

        if answer1_uuid:
            answer1 = Answer.get_active_by_uuid_or_404(answer1_uuid)
            answer1.practice = True
            comparison_example.answer1 = answer1
        else:
            abort(400, title="Comparison Example Not Saved",
                message="Please add two answers with content to the practice answers and try again.")

        if answer2_uuid:
            answer2 = Answer.get_active_by_uuid_or_404(answer2_uuid)
            answer2.practice = True
            comparison_example.answer2 = answer2
        else:
            abort(400, title="Comparison Example Not Saved",
                message="Please add two answers with content to the practice answers and try again.")

        model_changes = get_model_changes(comparison_example)
        db.session.add(comparison_example)
        db.session.commit()

        on_comparison_example_modified.send(
            self,
            event_name=on_comparison_example_modified.name,
            user=current_user,
            course_id=course.id,
            data=model_changes)

        return marshal(comparison_example, dataformat.get_comparison_example())

    @login_required
    def delete(self, course_uuid, assignment_uuid, comparison_example_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        comparison_example = ComparisonExample.get_active_by_uuid_or_404(comparison_example_uuid)
        require(DELETE, comparison_example,
            title="Comparison Example Not Deleted",
            message="Sorry, your role in this course does not allow you to delete practice answers.")

        formatted_comparison_example = marshal(comparison_example,
            dataformat.get_comparison_example(with_answers=False))

        comparison_example.active = False
        db.session.add(comparison_example)
        db.session.commit()

        on_comparison_example_delete.send(
            self,
            event_name=on_comparison_example_delete.name,
            user=current_user,
            course_id=course.id,
            data=formatted_comparison_example)

        return {'id': comparison_example.uuid}

api.add_resource(ComparisonExampleIdAPI, '/<comparison_example_uuid>')


# /
class ComparisonExampleRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, ComparisonExample(course_id=course.id),
            title="Comparison Example Unavailable",
            message="Sorry, your role in this course does not allow you to view practice answers.")

        # Get all comparison examples for this assignment
        comparison_examples = ComparisonExample.query \
            .filter_by(
                active=True,
                assignment_id=assignment.id
            ) \
            .all()

        on_comparison_example_list_get.send(
            self,
            event_name=on_comparison_example_list_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return { "objects": marshal(comparison_examples, dataformat.get_comparison_example()) }

    @login_required
    def post(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(CREATE, ComparisonExample(assignment=Assignment(course_id=course.id)),
            title="Comparison Example Not Saved",
            message="Sorry, your role in this course does not allow you to save practice answers.")

        new_comparison_example = ComparisonExample(assignment_id=assignment.id)

        params = new_comparison_example_parser.parse_args()
        answer1_uuid = params.get("answer1_id")
        answer2_uuid = params.get("answer2_id")

        if answer1_uuid:
            answer1 = Answer.get_active_by_uuid_or_404(answer1_uuid)
            answer1.practice = True
            new_comparison_example.answer1 = answer1
        else:
            abort(400, title="Comparison Example Not Saved",
                message="Please add two answers with content to the practice answers and try again.")

        if answer2_uuid:
            answer2 = Answer.get_active_by_uuid_or_404(answer2_uuid)
            answer2.practice = True
            new_comparison_example.answer2 = answer2
        else:
            abort(400, title="Comparison Example Not Saved",
                message="Please add two answers with content to the practice answers and try again.")

        on_comparison_example_create.send(
            self,
            event_name=on_comparison_example_create.name,
            user=current_user,
            course_id=course.id,
            data=marshal(new_comparison_example, dataformat.get_comparison_example(with_answers=False)))

        db.session.add(new_comparison_example)
        db.session.commit()

        return marshal(new_comparison_example, dataformat.get_comparison_example())

api.add_resource(ComparisonExampleRootAPI, '')
