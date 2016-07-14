import datetime

import dateutil.parser
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import desc, or_, func, and_
from sqlalchemy.orm import joinedload, undefer_group, load_only

from . import dataformat
from acj.core import db, event
from acj.authorization import allow, require
from acj.models import Assignment, Course, AssignmentCriterion, Answer, Comparison, \
    AnswerComment, AnswerCommentType
from .util import new_restful_api, get_model_changes
from .file import add_new_file, delete_file


assignment_api = Blueprint('assignment_api', __name__)
api = new_restful_api(assignment_api)

new_assignment_parser = RequestParser()
new_assignment_parser.add_argument('name', type=str, required=True, help="Assignment name is required.")
new_assignment_parser.add_argument('description', type=str, default=None)
new_assignment_parser.add_argument('answer_start', type=str, required=True)
new_assignment_parser.add_argument('answer_end', type=str, required=True)
new_assignment_parser.add_argument('compare_start', type=str, default=None)
new_assignment_parser.add_argument('compare_end', type=str, default=None)
new_assignment_parser.add_argument('file_name', type=str, default=None)
new_assignment_parser.add_argument('file_alias', type=str, default=None)
new_assignment_parser.add_argument('students_can_reply', type=bool, default=False)
new_assignment_parser.add_argument('number_of_comparisons', type=int, required=True)
new_assignment_parser.add_argument('enable_self_evaluation', type=int, default=None)
# has to add location parameter, otherwise MultiDict will screw up the list
new_assignment_parser.add_argument('criteria', type=list, default=[], location='json')

existing_assignment_parser = new_assignment_parser.copy()
existing_assignment_parser.add_argument('id', type=int, required=True, help="Assignment id is required.")

# events
on_assignment_modified = event.signal('ASSIGNMENT_MODIFIED')
on_assignment_get = event.signal('ASSIGNMENT_GET')
on_assignment_list_get = event.signal('ASSIGNMENT_LIST_GET')
on_assignment_create = event.signal('ASSIGNMENT_CREATE')
on_assignment_delete = event.signal('ASSIGNMENT_DELETE')
on_assignment_list_get_status = event.signal('ASSIGNMENT_LIST_GET_STATUS')
on_assignment_get_status = event.signal('ASSIGNMENT_GET_STATUS')

# /id
class AssignmentIdAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, assignment)
        now = datetime.datetime.utcnow()
        if assignment.answer_start and not allow(MANAGE, assignment) and not (assignment.answer_start <= now):
            return {"error": "The assignment is unavailable!"}, 403
        restrict_user = not allow(MANAGE, assignment)

        on_assignment_get.send(
            self,
            event_name=on_assignment_get.name,
            user=current_user,
            course_id=course_id,
            data={'id': assignment_id})

        return marshal(assignment, dataformat.get_assignment(restrict_user))

    @login_required
    def post(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(EDIT, assignment)
        params = existing_assignment_parser.parse_args()

        # make sure the assignment id in the url and the id matches
        if params['id'] != assignment_id:
            return {"error": "Assignment id does not match URL."}, 400
        # modify assignment according to new values, preserve original values if values not passed
        assignment.name = params.get("name", assignment.name)
        assignment.description = params.get("description", assignment.description)
        assignment.answer_start = datetime.datetime.strptime(
            params.get('answer_start', assignment.answer_start),
            '%Y-%m-%dT%H:%M:%S.%fZ')
        assignment.answer_end = datetime.datetime.strptime(
            params.get('answer_end', assignment.answer_end),
            '%Y-%m-%dT%H:%M:%S.%fZ')
        # if nothing in request, assume user don't want comparison date
        assignment.compare_start = params.get('compare_start', None)
        if assignment.compare_start is not None:
            assignment.compare_start = datetime.datetime.strptime(
                assignment.compare_start,
                '%Y-%m-%dT%H:%M:%S.%fZ')
        assignment.compare_end = params.get('compare_end', None)
        if assignment.compare_end is not None:
            assignment.compare_end = datetime.datetime.strptime(
                params.get('compare_end', assignment.compare_end),
                '%Y-%m-%dT%H:%M:%S.%fZ')
        assignment.students_can_reply = params.get('students_can_reply', False)
        assignment.number_of_comparisons = params.get(
            'number_of_comparisons', assignment.number_of_comparisons)
        assignment.enable_self_evaluation = params.get(
            'enable_self_evaluation', assignment.enable_self_evaluation)

        criterion_ids = [c['id'] for c in params.criteria]
        if assignment.compared:
            active_ids = [c.id for c in assignment.criteria]
            if set(criterion_ids) != set(active_ids):
                msg = 'The criteria cannot be changed in the assignment ' + \
                      'because they have already been used in an evaluation.'
                return {"error": msg}, 403
        else:
            existing_ids = [c.criterion_id for c in assignment.assignment_criteria]
            # assignment not comapred yet, can change criteria
            if len(criterion_ids) == 0:
                msg = 'You must add at least one criterion to the assignment '
                return {"error": msg}, 403
            # disable old ones
            for c in assignment.assignment_criteria:
                c.active = c.criterion_id in criterion_ids
            # add the new ones
            for criterion_id in criterion_ids:
                if criterion_id not in existing_ids:
                    assignment_criterion = AssignmentCriterion(
                        assignment_id=assignment_id, criterion_id=criterion_id)
                    assignment.assignment_criteria.append(assignment_criterion)

        on_assignment_modified.send(
            self,
            event_name=on_assignment_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(assignment))

        db.session.commit()

        file_name = params.get("file_name")
        if file_name:
            assignment.file_id = add_new_file(params.get('file_alias'), file_name,
                Assignment.__name__, assignment.id)

            db.session.commit()

        return marshal(assignment, dataformat.get_assignment())

    @login_required
    def delete(self, course_id, assignment_id):
        assignment = Assignment.get_active_or_404(assignment_id)
        require(DELETE, assignment)
        formatted_assignment = marshal(assignment, dataformat.get_assignment(False))
        # delete file when assignment is deleted
        delete_file(assignment.file_id)
        assignment.active = False
        assignment.file_id = None
        db.session.add(assignment)
        db.session.commit()

        on_assignment_delete.send(
            self,
            event_name=on_assignment_delete.name,
            user=current_user,
            course_id=course_id,
            data=formatted_assignment)

        return {'id': assignment.id}

api.add_resource(AssignmentIdAPI, '/<int:assignment_id>')


# /
class AssignmentRootAPI(Resource):
    # TODO Pagination
    @login_required
    def get(self, course_id):
        course = Course.get_active_or_404(course_id)
        require(READ, course)
        # Get all assignments for this course, default order is most recent first
        assignment = Assignment(course_id=course_id)
        base_query = Assignment.query \
            .options(joinedload("assignment_criteria").joinedload("criterion")) \
            .options(undefer_group('counts')) \
            .filter(
                Assignment.course_id == course_id,
                Assignment.active == True
            ) \
            .order_by(desc(Assignment.created))

        if allow(MANAGE, assignment):
            assignments = base_query.all()
        else:
            now = datetime.datetime.utcnow()
            assignments = base_query \
                .filter(or_(
                    Assignment.answer_start.is_(None),
                    now >= Assignment.answer_start
                ))\
                .all()

        restrict_user = not allow(MANAGE, assignment)

        on_assignment_list_get.send(
            self,
            event_name=on_assignment_list_get.name,
            user=current_user,
            course_id=course_id)

        return {
            "objects": marshal(assignments, dataformat.get_assignment(restrict_user))
        }

    @login_required
    def post(self, course_id):
        Course.get_active_or_404(course_id)
        # check permission first before reading parser arguments
        new_assignment = Assignment(course_id=course_id)
        require(CREATE, new_assignment)
        params = new_assignment_parser.parse_args()

        new_assignment.user_id = current_user.id
        new_assignment.name = params.get("name")
        new_assignment.description = params.get("description")
        new_assignment.answer_start = dateutil.parser.parse(params.get('answer_start'))
        new_assignment.answer_end = dateutil.parser.parse(params.get('answer_end'))

        new_assignment.compare_start = params.get('compare_start', None)
        if new_assignment.compare_start is not None:
            new_assignment.compare_start = dateutil.parser.parse(params.get('compare_start', None))

        new_assignment.compare_end = params.get('compare_end', None)
        if new_assignment.compare_end is not None:
            new_assignment.compare_end = dateutil.parser.parse(params.get('compare_end', None))

        new_assignment.students_can_reply = params.get('students_can_reply', False)
        new_assignment.number_of_comparisons = params.get('number_of_comparisons')
        new_assignment.enable_self_evaluation = params.get('enable_self_evaluation')

        criterion_ids = [c['id'] for c in params.criteria]
        if len(criterion_ids) == 0:
            msg = 'You must add at least one criterion to the assignment '
            return {"error": msg}, 403
        for c in criterion_ids:
            assignment_criterion = AssignmentCriterion(assignment=new_assignment, criterion_id=c)
            db.session.add(assignment_criterion)

        db.session.add(new_assignment)
        db.session.commit()

        file_name = params.get("file_name")
        if file_name:
            new_assignment.file_id = add_new_file(params.get('file_alias'), file_name,
                Assignment.__name__, new_assignment.id)

            db.session.add(new_assignment)
            db.session.commit()

        on_assignment_create.send(
            self,
            event_name=on_assignment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(new_assignment, dataformat.get_assignment(False)))

        return marshal(new_assignment, dataformat.get_assignment())

api.add_resource(AssignmentRootAPI, '')


# /id/status
class AssignmentIdStatusAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, assignment)

        answer_count = Answer.query \
            .filter_by(
                user_id=current_user.id,
                assignment_id=assignment_id,
                active=True,
                draft=False
            ) \
            .count()

        drafts = Answer.query \
            .options(load_only('id')) \
            .filter_by(
                user_id=current_user.id,
                assignment_id=assignment_id,
                active=True,
                draft=True
            ) \
            .all()

        comparison_count = assignment.completed_comparison_count_for_user(current_user.id)
        comparison_availble = Comparison.comparison_avialble_for_user(course_id, assignment_id, current_user.id)

        status = {
            'answers': {
                'answered': answer_count > 0,
                'count': answer_count,
                'has_draft': len(drafts) > 0,
                'draft_ids': [draft.id for draft in drafts]
            },
            'comparisons': {
                'available': comparison_availble,
                'count': comparison_count,
                'left': max(0, assignment.total_comparisons_required - comparison_count)
            }
        }

        if assignment.enable_self_evaluation:
            self_evaluations = AnswerComment.query \
                .join("answer") \
                .filter(and_(
                    AnswerComment.user_id == current_user.id,
                    AnswerComment.active == True,
                    AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                    AnswerComment.draft == False,
                    Answer.assignment_id == assignment_id,
                    Answer.active == True,
                    Answer.draft == False
                )) \
                .count()
            status['comparisons']['self_evaluation_completed'] = self_evaluations > 0

        on_assignment_get_status.send(
            self,
            event_name=on_assignment_get.name,
            user=current_user,
            course_id=course_id,
            data=status)

        return {"status": status}

api.add_resource(AssignmentIdStatusAPI, '/<int:assignment_id>/status')



# /status
class AssignmentRootStatusAPI(Resource):
    @login_required
    def get(self, course_id):
        course = Course.get_active_or_404(course_id)
        require(READ, course)

        assignments = course.assignments \
            .filter_by(active=True) \
            .all()
        assignment_ids = [assignment.id for assignment in assignments]

        answer_counts = Answer.query \
            .with_entities(
                Answer.assignment_id,
                func.count(Answer.assignment_id).label('answer_count')
            ) \
            .filter_by(
                user_id=current_user.id,
                active=True,
                draft=False
            ) \
            .filter(Answer.assignment_id.in_(assignment_ids)) \
            .group_by(Answer.assignment_id) \
            .all()

        # get self evaluation status for assignments with self evaluations enabled
        self_evaluations = AnswerComment.query \
            .join("answer") \
            .with_entities(
                Answer.assignment_id,
                func.count(Answer.assignment_id).label('self_evaluation_count')
            ) \
            .filter(and_(
                AnswerComment.user_id == current_user.id,
                AnswerComment.active == True,
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.draft == False,
                Answer.active == True,
                Answer.draft == False,
                Answer.assignment_id.in_(assignment_ids)
            )) \
            .group_by(Answer.assignment_id) \
            .all()

        drafts = Answer.query \
            .options(load_only('id', 'assignment_id')) \
            .filter_by(
                user_id=current_user.id,
                active=True,
                draft=True
            ) \
            .all()

        statuses = {}
        for assignment in assignments:
            answer_count = next(
                (result.answer_count for result in answer_counts if result.assignment_id == assignment.id),
                0
            )
            assignment_drafts = [draft for draft in drafts if draft.assignment_id == assignment.id]
            comparison_count = assignment.completed_comparison_count_for_user(current_user.id)
            comparison_availble = Comparison.comparison_avialble_for_user(course_id, assignment.id, current_user.id)

            statuses[assignment.id] = {
                'answers': {
                    'answered': answer_count > 0,
                    'count': answer_count,
                    'has_draft': len(assignment_drafts) > 0,
                    'draft_ids': [draft.id for draft in assignment_drafts]
                },
                'comparisons': {
                    'available': comparison_availble,
                    'count': comparison_count,
                    'left': max(0, assignment.total_comparisons_required - comparison_count)
                }
            }

            if assignment.enable_self_evaluation:
                self_evaluation_count = next(
                    (result.self_evaluation_count for result in self_evaluations if result.assignment_id == assignment.id),
                    0
                )
                statuses[assignment.id]['comparisons']['self_evaluation_completed'] = self_evaluation_count > 0

        on_assignment_list_get_status.send(
            self,
            event_name=on_assignment_get.name,
            user=current_user,
            course_id=course_id,
            data=statuses)

        return {"statuses": statuses}

api.add_resource(AssignmentRootStatusAPI, '/status')