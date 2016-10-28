import dateutil.parser
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint, abort
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import desc, or_, func, and_
from sqlalchemy.orm import joinedload, undefer_group, load_only

from . import dataformat
from compair.core import db, event
from compair.authorization import allow, require
from compair.models import Assignment, Course, Answer, ComparisonExample
from .util import new_restful_api, get_model_changes

comparison_example_api = Blueprint('comparison_example_api', __name__)
api = new_restful_api(comparison_example_api)

new_comparison_example_parser = RequestParser()
new_comparison_example_parser.add_argument('answer1_id', type=str, required=True)
new_comparison_example_parser.add_argument('answer2_id', type=str, required=True)

existing_comparison_example_parser = new_comparison_example_parser.copy()
existing_comparison_example_parser.add_argument('id', type=str, required=True)

# events
on_comparison_example_modified = event.signal('ASSIGNMENT_MODIFIED')
on_comparison_example_list_get = event.signal('ASSIGNMENT_LIST_GET')
on_comparison_example_create = event.signal('ASSIGNMENT_CREATE')
on_comparison_example_delete = event.signal('ASSIGNMENT_DELETE')

# /id
class ComparisonExampleIdAPI(Resource):
    @login_required
    def post(self, course_uuid, assignment_uuid, comparison_example_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        comparison_example = ComparisonExample.get_active_by_uuid_or_404(comparison_example_uuid)
        require(EDIT, comparison_example)

        params = existing_comparison_example_parser.parse_args()
        answer1_uuid = params.get("answer1_id")
        answer2_uuid = params.get("answer2_id")

        if answer1_uuid:
            answer1 = Answer.get_active_by_uuid_or_404(answer1_uuid)
            answer1.practice = True
            comparison_example.answer1 = answer1
        else:
            return {"error": "Comparison examples must have 2 answers"}, 400

        if answer2_uuid:
            answer2 = Answer.get_active_by_uuid_or_404(answer2_uuid)
            answer2.practice = True
            comparison_example.answer2 = answer2
        else:
            return {"error": "Comparison examples must have 2 answers"}, 400

        on_comparison_example_modified.send(
            self,
            event_name=on_comparison_example_modified.name,
            user=current_user,
            course_id=course.id,
            data=get_model_changes(comparison_example))

        db.session.add(comparison_example)
        db.session.commit()

        return marshal(comparison_example, dataformat.get_comparison_example())

    @login_required
    def delete(self, course_uuid, assignment_uuid, comparison_example_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        comparison_example = ComparisonExample.get_active_by_uuid_or_404(comparison_example_uuid)
        require(DELETE, comparison_example)

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
        require(READ, ComparisonExample(course_id=course.id))

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
        require(CREATE, ComparisonExample(assignment=Assignment(course_id=course.id)))

        new_comparison_example = ComparisonExample(assignment_id=assignment.id)

        params = new_comparison_example_parser.parse_args()
        answer1_uuid = params.get("answer1_id")
        answer2_uuid = params.get("answer2_id")

        if answer1_uuid:
            answer1 = Answer.get_active_by_uuid_or_404(answer1_uuid)
            answer1.practice = True
            new_comparison_example.answer1 = answer1
        else:
            return {"error": "Comparison examples must have 2 answers"}, 400

        if answer2_uuid:
            answer2 = Answer.get_active_by_uuid_or_404(answer2_uuid)
            answer2.practice = True
            new_comparison_example.answer2 = answer2
        else:
            return {"error": "Comparison examples must have 2 answers"}, 400

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