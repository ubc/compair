import datetime

import dateutil.parser
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask_login import login_required, current_user, current_app
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import desc, or_, func, and_
from sqlalchemy.orm import joinedload, undefer_group, load_only
from six import text_type

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import allow, require, is_user_access_restricted
from compair.models import Assignment, Course, Criterion, AssignmentCriterion, Answer, Comparison, \
    AnswerComment, AnswerCommentType, PairingAlgorithm, Criterion, File, User, UserCourse, CourseRole
from .util import new_restful_api, get_model_changes, pagination_parser

assignment_api = Blueprint('assignment_api', __name__)
api = new_restful_api(assignment_api)

def non_blank_text(value):
    if value is None:
        return None
    else:
        return None if text_type(value).strip() == "" else text_type(value)

new_assignment_parser = RequestParser()
new_assignment_parser.add_argument('name', required=True, help="Assignment name is required.")
new_assignment_parser.add_argument('description', default=None)
new_assignment_parser.add_argument('peer_feedback_prompt', type=non_blank_text, default=None)
new_assignment_parser.add_argument('answer_start', required=True)
new_assignment_parser.add_argument('answer_end', required=True)
new_assignment_parser.add_argument('compare_start', default=None)
new_assignment_parser.add_argument('compare_end', default=None)
new_assignment_parser.add_argument('file_id', default=None)
new_assignment_parser.add_argument('students_can_reply', type=bool, default=False)
new_assignment_parser.add_argument('number_of_comparisons', type=int, required=True)
new_assignment_parser.add_argument('enable_self_evaluation', type=int, default=None)
new_assignment_parser.add_argument('pairing_algorithm', default=None)
new_assignment_parser.add_argument('rank_display_limit', type=int, default=None)
new_assignment_parser.add_argument('educators_can_compare', type=bool, default=False)
# has to add location parameter, otherwise MultiDict will screw up the list
new_assignment_parser.add_argument('criteria', type=list, default=[], location='json')
new_assignment_parser.add_argument('answer_grade_weight', type=int, default=1)
new_assignment_parser.add_argument('comparison_grade_weight', type=int, default=1)
new_assignment_parser.add_argument('self_evaluation_grade_weight', type=int, default=1)

existing_assignment_parser = new_assignment_parser.copy()
existing_assignment_parser.add_argument('id', required=True, help="Assignment id is required.")

assignment_users_comparison_list_parser = pagination_parser.copy()
assignment_users_comparison_list_parser.add_argument('group', required=False, default=None)
assignment_users_comparison_list_parser.add_argument('author', required=False, default=None)

# events
on_assignment_modified = event.signal('ASSIGNMENT_MODIFIED')
on_assignment_get = event.signal('ASSIGNMENT_GET')
on_assignment_list_get = event.signal('ASSIGNMENT_LIST_GET')
on_assignment_create = event.signal('ASSIGNMENT_CREATE')
on_assignment_delete = event.signal('ASSIGNMENT_DELETE')
on_assignment_list_get_status = event.signal('ASSIGNMENT_LIST_GET_STATUS')
on_assignment_get_status = event.signal('ASSIGNMENT_GET_STATUS')
on_assignment_user_comparisons_get = event.signal('ASSIGNMENT_USER_COMPARISONS_GET')
on_assignment_users_comparisons_get = event.signal('ASSIGNMENT_USERS_COMPARISONS_GET')

def check_valid_pairing_algorithm(pairing_algorithm):
    pairing_algorithms = [
        PairingAlgorithm.adaptive.value,
        PairingAlgorithm.random.value,
        PairingAlgorithm.adaptive_min_delta.value
    ]
    if pairing_algorithm not in pairing_algorithms:
        abort(400, title="Assignment Not Saved", message="'"+pairing_algorithm+"' is not a valid answer pairing algorithm. Please select one of the pairing algorithm options listed.")

# /id
class AssignmentIdAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Assignment Unavailable",
            message="Assignments can be saved only by those enrolled in the course. Please double-check your enrollment in this course.")

        now = datetime.datetime.utcnow()
        if assignment.answer_start and not allow(MANAGE, assignment) and not (assignment.answer_start <= now):
            abort(403, title="Assignment Unavailable", message="This assignment is not yet open to students. Please check back after the start date the instructor has set.")
        restrict_user = not allow(MANAGE, assignment)

        on_assignment_get.send(
            self,
            event_name=on_assignment_get.name,
            user=current_user,
            course_id=course.id,
            data={'id': assignment.id})

        return marshal(assignment, dataformat.get_assignment(restrict_user))

    @login_required
    def post(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        assignment_criteria = assignment.assignment_criteria
        require(EDIT, assignment,
            title="Assignment Not Saved",
            message="Sorry, your role in this course does not allow you to save assignments.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS:
                abort(400, title="Assignment Not Saved", message="Sorry, you cannot edit the default demo assignments.")

        params = existing_assignment_parser.parse_args()

        # make sure the assignment id in the url and the id matches
        if params['id'] != assignment_uuid:
            abort(400, title="Assignment Not Saved", message="The assignment's ID does not match the URL, which is required in order to update the assignment.")

        # make sure that file attachment exists
        file_uuid = params.get('file_id')
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            assignment.file_id = attachment.id
        else:
            assignment.file_id = None

        # modify assignment according to new values, preserve original values if values not passed
        assignment.name = params.get("name", assignment.name)
        assignment.description = params.get("description", assignment.description)
        assignment.peer_feedback_prompt = params.get("peer_feedback_prompt", assignment.peer_feedback_prompt)
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

        # validate answer + comparison period start & end times
        valid, error_message = Assignment.validate_periods(course.start_date, course.end_date,
             assignment.answer_start, assignment.answer_end, assignment.compare_start, assignment.compare_end)
        if not valid:
            abort(400, title="Assignment Not Saved", message=error_message)

        assignment.students_can_reply = params.get('students_can_reply', False)
        assignment.number_of_comparisons = params.get(
            'number_of_comparisons', assignment.number_of_comparisons)
        assignment.enable_self_evaluation = params.get(
            'enable_self_evaluation', assignment.enable_self_evaluation)

        assignment.answer_grade_weight = params.get(
            'answer_grade_weight', assignment.answer_grade_weight)
        assignment.comparison_grade_weight = params.get(
            'comparison_grade_weight', assignment.comparison_grade_weight)
        assignment.self_evaluation_grade_weight = params.get(
            'self_evaluation_grade_weight', assignment.self_evaluation_grade_weight)

        pairing_algorithm = params.get("pairing_algorithm")
        check_valid_pairing_algorithm(pairing_algorithm)
        if not assignment.compared:
            assignment.pairing_algorithm = PairingAlgorithm(pairing_algorithm)
        elif assignment.pairing_algorithm != PairingAlgorithm(pairing_algorithm):
            msg = 'The answer pair selection algorithm cannot be changed for this assignment ' + \
                    'because it has already been used in one or more comparisons.'
            abort(403, title="Assignment Not Saved", message=msg)

        assignment.educators_can_compare = params.get("educators_can_compare")

        assignment.rank_display_limit = params.get("rank_display_limit", None)
        if assignment.rank_display_limit != None and assignment.rank_display_limit <= 0:
            assignment.rank_display_limit = None

        criterion_uuids = [c.get('id') for c in params.criteria]
        criterion_data = {c.get('id'): c.get('weight', 1) for c in params.criteria}
        if assignment.compared:
            active_uuids = [c.uuid for c in assignment.criteria]
            active_data = {c.uuid: c.weight for c in assignment.criteria}
            if set(criterion_uuids) != set(active_uuids):
                msg = 'The criteria cannot be changed for this assignment ' + \
                      'because they have already been used in one or more comparisons.'
                abort(403, title="Assignment Not Saved", message=msg)

            for criterion in assignment.criteria:
                if criterion_data.get(criterion.uuid) != criterion.weight:
                    msg = 'The criteria weights cannot be changed for this assignment ' + \
                        'because they have already been used in one or more comparisons.'
                    abort(403, title="Assignment Not Saved", message=msg)
        else:
            # assignment not compared yet, can change criteria
            if len(criterion_uuids) == 0:
                msg = "Please add at least one criterion to the assignment and save again."
                abort(403, title="Assignment Not Saved", message=msg)

            existing_uuids = [c.criterion_uuid for c in assignment_criteria]
            # disable old ones
            for c in assignment_criteria:
                c.active = c.criterion_uuid in criterion_uuids
                if c.active:
                    c.weight = criterion_data.get(c.criterion_uuid)

            # add the new ones
            new_uuids = []
            for criterion_uuid in criterion_uuids:
                if criterion_uuid not in existing_uuids:
                    new_uuids.append(criterion_uuid)

            if len(new_uuids) > 0:
                new_criteria = Criterion.query.filter(Criterion.uuid.in_(new_uuids)).all()
                for criterion in new_criteria:
                    assignment_criteria.append(AssignmentCriterion(
                        criterion=criterion,
                        weight=criterion_data.get(criterion.uuid)
                    ))

        # ensure criteria are in order
        for index, criterion_uuid in enumerate(criterion_uuids):
            assignment_criterion = next(assignment_criterion \
                for assignment_criterion in assignment_criteria \
                if assignment_criterion.criterion_uuid == criterion_uuid)

            assignment_criteria.remove(assignment_criterion)
            assignment_criteria.insert(index, assignment_criterion)

        model_changes = get_model_changes(assignment)

        on_assignment_modified.send(
            self,
            event_name=on_assignment_modified.name,
            user=current_user,
            course_id=course.id,
            assignment=assignment,
            data=model_changes)

        db.session.commit()

        # need to reorder after update
        assignment_criteria.reorder()

        # update assignment and course grades if needed
        if model_changes and (model_changes.get('answer_grade_weight') or
                 model_changes.get('comparison_grade_weight') or
                 model_changes.get('self_evaluation_grade_weight') or
                 model_changes.get('enable_self_evaluation')):
            assignment.calculate_grades()
            course.calculate_grades()

        return marshal(assignment, dataformat.get_assignment())

    @login_required
    def delete(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(DELETE, assignment,
            title="Assignment Not Deleted",
            message="Sorry, your role in this course does not allow you to delete assignments.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS:
                abort(400, title="Assignment Not Deleted", message="Sorry, you cannot remove the default demo assignments.")

        formatted_assignment = marshal(assignment, dataformat.get_assignment(False))
        # delete file when assignment is deleted
        assignment.active = False
        db.session.commit()

        # update course grades
        course.calculate_grades()

        on_assignment_delete.send(
            self,
            event_name=on_assignment_delete.name,
            user=current_user,
            course_id=course.id,
            assignment=assignment,
            data=formatted_assignment)

        return {'id': assignment.uuid}

api.add_resource(AssignmentIdAPI, '/<assignment_uuid>')


# /
class AssignmentRootAPI(Resource):
    # TODO Pagination
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course,
            title="Assignments Unavailable",
            message="Assignments can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        assignment = Assignment(course_id=course.id)
        restrict_user = not allow(MANAGE, assignment)

        # Get all assignments for this course, order by answer_start date, created date
        base_query = Assignment.query \
            .options(joinedload("assignment_criteria").joinedload("criterion")) \
            .options(undefer_group('counts')) \
            .filter(
                Assignment.course_id == course.id,
                Assignment.active == True
            ) \
            .order_by(desc(Assignment.answer_start), desc(Assignment.created))

        if restrict_user:
            now = datetime.datetime.utcnow()
            assignments = base_query \
                .filter(or_(
                    Assignment.answer_start.is_(None),
                    now >= Assignment.answer_start
                ))\
                .all()
        else:
            assignments = base_query.all()

        on_assignment_list_get.send(
            self,
            event_name=on_assignment_list_get.name,
            user=current_user,
            course_id=course.id)

        return {
            "objects": marshal(assignments, dataformat.get_assignment(restrict_user))
        }

    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        # check permission first before reading parser arguments
        new_assignment = Assignment(course_id=course.id)
        require(CREATE, new_assignment,
            title="Assignment Not Saved",
            message="Sorry, your role in this course does not allow you to save assignments.")

        params = new_assignment_parser.parse_args()

        new_assignment.user_id = current_user.id
        new_assignment.name = params.get("name")
        new_assignment.description = params.get("description")
        new_assignment.peer_feedback_prompt = params.get("peer_feedback_prompt")
        new_assignment.answer_start = dateutil.parser.parse(params.get('answer_start'))
        new_assignment.answer_end = dateutil.parser.parse(params.get('answer_end'))
        new_assignment.educators_can_compare = params.get("educators_can_compare")
        new_assignment.rank_display_limit = params.get("rank_display_limit", None)
        if new_assignment.rank_display_limit != None and new_assignment.rank_display_limit <= 0:
            new_assignment.rank_display_limit = None

        # make sure that file attachment exists
        file_uuid = params.get('file_id')
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            new_assignment.file_id = attachment.id
        else:
            new_assignment.file_id = None

        new_assignment.compare_start = params.get('compare_start', None)
        if new_assignment.compare_start is not None:
            new_assignment.compare_start = dateutil.parser.parse(params.get('compare_start', None))

        new_assignment.compare_end = params.get('compare_end', None)
        if new_assignment.compare_end is not None:
            new_assignment.compare_end = dateutil.parser.parse(params.get('compare_end', None))

        # validate answer + comparison period start & end times
        valid, error_message = Assignment.validate_periods(course.start_date, course.end_date,
             new_assignment.answer_start, new_assignment.answer_end,
             new_assignment.compare_start, new_assignment.compare_end)
        if not valid:
            abort(400, title="Assignment Not Saved", message=error_message)

        new_assignment.students_can_reply = params.get('students_can_reply', False)
        new_assignment.number_of_comparisons = params.get('number_of_comparisons')
        new_assignment.enable_self_evaluation = params.get('enable_self_evaluation')

        new_assignment.answer_grade_weight = params.get('answer_grade_weight')
        new_assignment.comparison_grade_weight = params.get('comparison_grade_weight')
        new_assignment.self_evaluation_grade_weight = params.get('self_evaluation_grade_weight')

        pairing_algorithm = params.get("pairing_algorithm", PairingAlgorithm.random)
        check_valid_pairing_algorithm(pairing_algorithm)
        new_assignment.pairing_algorithm = PairingAlgorithm(pairing_algorithm)

        criterion_uuids = [c.get('id') for c in params.criteria]
        criterion_data = {c.get('id'): c.get('weight', 1) for c in params.criteria}
        if len(criterion_data) == 0:
            msg = "Please add at least one criterion to the assignment and save again."
            abort(400, title="Assignment Not Saved", message=msg)

        criteria = Criterion.query \
            .filter(Criterion.uuid.in_(criterion_uuids)) \
            .all()

        if len(criterion_uuids) != len(criteria):
            abort(400, title="Assignment Not Saved", message="Please double-check the criteria you selected and save agaiin.")

        # add criteria to assignment in order
        for criterion_uuid in criterion_uuids:
            criterion = next(criterion for criterion in criteria if criterion.uuid == criterion_uuid)
            new_assignment.assignment_criteria.append(AssignmentCriterion(
                criterion=criterion,
                weight=criterion_data.get(criterion.uuid)
            ))

        db.session.add(new_assignment)
        db.session.commit()

        # need to reorder after insert
        new_assignment.assignment_criteria.reorder()

        # update course grades
        course.calculate_grades()

        on_assignment_create.send(
            self,
            event_name=on_assignment_create.name,
            user=current_user,
            course_id=course.id,
            assignment=new_assignment,
            data=marshal(new_assignment, dataformat.get_assignment(False)))

        return marshal(new_assignment, dataformat.get_assignment())

api.add_resource(AssignmentRootAPI, '')


# /id/status
class AssignmentIdStatusAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Assignment Status Unavailable",
            message="Assignment status can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

        answer_count = Answer.query \
            .filter_by(
                user_id=current_user.id,
                assignment_id=assignment.id,
                active=True,
                practice=False,
                draft=False
            ) \
            .count()

        feedback_count = AnswerComment.query \
            .join("answer") \
            .filter(and_(
                AnswerComment.active == True,
                AnswerComment.draft == False,
                Answer.user_id == current_user.id,
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False
            )) \
            .count()

        drafts = Answer.query \
            .options(load_only('id')) \
            .filter_by(
                user_id=current_user.id,
                assignment_id=assignment.id,
                active=True,
                practice=False,
                draft=True,
                saved=True
            ) \
            .all()

        comparison_count = assignment.completed_comparison_count_for_user(current_user.id)
        other_student_answers = assignment.student_answer_count - answer_count
        comparison_available = comparison_count < other_student_answers * (other_student_answers - 1) / 2

        status = {
            'answers': {
                'answered': answer_count > 0,
                'feedback': feedback_count,
                'count': answer_count,
                'has_draft': len(drafts) > 0,
                'draft_ids': [draft.uuid for draft in drafts]
            },
            'comparisons': {
                'available': comparison_available,
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
                    Answer.assignment_id == assignment.id,
                    Answer.active == True,
                    Answer.practice == False,
                    Answer.draft == False
                )) \
                .count()
            status['comparisons']['self_evaluation_completed'] = self_evaluations > 0

        on_assignment_get_status.send(
            self,
            event_name=on_assignment_get_status.name,
            user=current_user,
            course_id=course.id,
            data=status)

        return {"status": status}

api.add_resource(AssignmentIdStatusAPI, '/<assignment_uuid>/status')



# /status
class AssignmentRootStatusAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course,
            title="Assignment Status Unavailable",
            message="Assignment status can be seen only by those enrolled in the course. Please double-check your enrollment in this course.")

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
                practice=False,
                draft=False
            ) \
            .filter(Answer.assignment_id.in_(assignment_ids)) \
            .group_by(Answer.assignment_id) \
            .all()


        feedback_counts = AnswerComment.query \
            .join("answer") \
            .with_entities(
                Answer.assignment_id,
                func.count(Answer.assignment_id).label('feedback_count')
            ) \
            .filter(and_(
                AnswerComment.active == True,
                AnswerComment.draft == False,
                Answer.user_id == current_user.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                Answer.assignment_id.in_(assignment_ids)
            )) \
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
                Answer.practice == False,
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
                practice=False,
                draft=True,
                saved=True
            ) \
            .all()

        statuses = {}
        for assignment in assignments:
            answer_count = next(
                (result.answer_count for result in answer_counts if result.assignment_id == assignment.id),
                0
            )
            feedback_count = next(
                (result.feedback_count for result in feedback_counts if result.assignment_id == assignment.id),
                0
            )
            assignment_drafts = [draft for draft in drafts if draft.assignment_id == assignment.id]
            comparison_count = assignment.completed_comparison_count_for_user(current_user.id)
            other_student_answers = assignment.student_answer_count - answer_count
            comparison_available = comparison_count < other_student_answers * (other_student_answers - 1) / 2

            statuses[assignment.uuid] = {
                'answers': {
                    'answered': answer_count > 0,
                    'feedback': feedback_count,
                    'count': answer_count,
                    'has_draft': len(assignment_drafts) > 0,
                    'draft_ids': [draft.uuid for draft in assignment_drafts]
                },
                'comparisons': {
                    'available': comparison_available,
                    'count': comparison_count,
                    'left': max(0, assignment.total_comparisons_required - comparison_count)
                }
            }

            if assignment.enable_self_evaluation:
                self_evaluation_count = next(
                    (result.self_evaluation_count for result in self_evaluations if result.assignment_id == assignment.id),
                    0
                )
                statuses[assignment.uuid]['comparisons']['self_evaluation_completed'] = self_evaluation_count > 0

        on_assignment_list_get_status.send(
            self,
            event_name=on_assignment_list_get_status.name,
            user=current_user,
            course_id=course.id,
            data=statuses)

        return {"statuses": statuses}

api.add_resource(AssignmentRootStatusAPI, '/status')


# /user/comparisons
class AssignmentUserComparisonsAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Comparisons Unavailable",
            message="Sorry, your role in this course does not allow you to view comparisons for this assignment.")

        restrict_user = is_user_access_restricted(current_user)

        # get comparisons for current user
        comparisons = Comparison.query \
            .filter(and_(
                Comparison.completed == True,
                Comparison.assignment_id == assignment.id,
                Comparison.user_id == current_user.id
            )) \
            .all()

        # get all self-evaluations and evaluation comments for current user
        answer_comments = AnswerComment.query \
            .join("answer") \
            .filter(and_(
                AnswerComment.active == True,
                AnswerComment.comment_type.in_([AnswerCommentType.self_evaluation, AnswerCommentType.evaluation]),
                AnswerComment.draft == False,
                Answer.active == True,
                Answer.draft == False,
                Answer.assignment_id == assignment.id,
                AnswerComment.user_id == current_user.id
            )) \
            .all()

        # add comparison answer evaluation comments to comparison object
        for comparison in comparisons:
            comparison.answer1_feedback = [comment for comment in answer_comments if
                comment.user_id == comparison.user_id and
                comment.answer_id == comparison.answer1_id and
                comment.comment_type == AnswerCommentType.evaluation
            ]

            comparison.answer2_feedback = [comment for comment in answer_comments if
                comment.user_id == comparison.user_id and
                comment.answer_id == comparison.answer2_id and
                comment.comment_type == AnswerCommentType.evaluation
            ]

        on_assignment_user_comparisons_get.send(
            self,
            event_name=on_assignment_user_comparisons_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id}
        )

        comparison_set = {
            'comparisons': [comparison for comparison in comparisons if
                comparison.user_id == current_user.id
            ],
            'self_evaluations': [comment for comment in answer_comments if
                comment.user_id == current_user.id and
                comment.comment_type == AnswerCommentType.self_evaluation
            ]
        }

        return marshal(comparison_set, dataformat.get_comparison_set(restrict_user, with_user=False))

api.add_resource(AssignmentUserComparisonsAPI, '/<assignment_uuid>/user/comparisons')

# /users/comparisons
class AssignmentUsersComparisonsAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, Comparison(course_id=course.id),
            title="Comparisons Unavailable",
            message="Sorry, your role in this course does not allow you to view all comparisons for this assignment.")

        restrict_user = is_user_access_restricted(current_user)
        params = assignment_users_comparison_list_parser.parse_args()

        # only get users who have at least made one comparison
        # each paginated item is a user (with a set of comparisons and self-evaluations)
        user_query = User.query \
            .join(UserCourse, and_(
                User.id == UserCourse.user_id,
                UserCourse.course_id == course.id
            )) \
            .join(Comparison, and_(
                Comparison.user_id == User.id,
                Comparison.assignment_id == assignment.id
            )) \
            .filter(and_(
                UserCourse.course_role != CourseRole.dropped,
                Comparison.completed == True
            )) \
            .group_by(User) \
            .order_by(User.firstname, User.lastname)

        self_evaluation_total = AnswerComment.query \
            .join("answer") \
            .with_entities(
                func.count(Answer.assignment_id).label('self_evaluation_count')
            ) \
            .filter(and_(
                AnswerComment.active == True,
                AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                AnswerComment.draft == False,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                Answer.assignment_id == assignment.id
            ))

        comparison_total = Comparison.query \
            .with_entities(
                func.count(Comparison.assignment_id).label('comparison_count')
            ) \
            .filter(and_(
                Comparison.completed == True,
                Comparison.assignment_id == assignment.id
            ))

        if params['author']:
            user = User.get_by_uuid_or_404(params['author'])

            user_query = user_query.filter(User.id == user.id)
            self_evaluation_total = self_evaluation_total.filter(AnswerComment.user_id == user.id)
            comparison_total = comparison_total.filter(Comparison.user_id == user.id)
        elif params['group']:
            user_query = user_query.filter(UserCourse.group_name == params['group'])

            self_evaluation_total = self_evaluation_total \
                .join(UserCourse, and_(
                    AnswerComment.user_id == UserCourse.user_id,
                    UserCourse.course_id == course.id
                )) \
                .filter(UserCourse.group_name == params['group'])

            comparison_total = comparison_total \
                .join(UserCourse, and_(
                    Comparison.user_id == UserCourse.user_id,
                    UserCourse.course_id == course.id
                )) \
                .filter(UserCourse.group_name == params['group'])

        page = user_query.paginate(params['page'], params['perPage'])
        self_evaluation_total = self_evaluation_total.scalar()
        comparison_total = comparison_total.scalar()

        comparison_sets = []
        if page.total:
            user_ids = [user.id for user in page.items]

            # get all comparisons that group of users created
            comparisons = Comparison.query \
                .filter(and_(
                    Comparison.completed == True,
                    Comparison.assignment_id == assignment.id,
                    Comparison.user_id.in_(user_ids)
                )) \
                .all()

            # retrieve the answer comments
            user_comparison_answers = {}
            for comparison in comparisons:
                user_answers = user_comparison_answers.setdefault(comparison.user_id, set())
                user_answers.add(comparison.answer1_id)
                user_answers.add(comparison.answer2_id)

            conditions = []
            for user_id, answer_set in user_comparison_answers.items():
                conditions.append(and_(
                        AnswerComment.comment_type == AnswerCommentType.evaluation,
                        AnswerComment.user_id == user_id,
                        AnswerComment.answer_id.in_(list(answer_set)),
                        AnswerComment.assignment_id == assignment.id
                ))
                conditions.append(and_(
                    AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                    AnswerComment.user_id == user_id,
                    AnswerComment.assignment_id == assignment.id
                ))

            answer_comments = AnswerComment.query \
                .filter(or_(*conditions)) \
                .filter_by(draft=False) \
                .all()

            # add comparison answer evaluation comments to comparison object
            for comparison in comparisons:
                comparison.answer1_feedback = [comment for comment in answer_comments if
                    comment.user_id == comparison.user_id and
                    comment.answer_id == comparison.answer1_id and
                    comment.comment_type == AnswerCommentType.evaluation
                ]

                comparison.answer2_feedback = [comment for comment in answer_comments if
                    comment.user_id == comparison.user_id and
                    comment.answer_id == comparison.answer2_id and
                    comment.comment_type == AnswerCommentType.evaluation
                ]

            for user in page.items:
                comparison_sets.append({
                    'user': user,
                    'comparisons': [comparison for comparison in comparisons if
                        comparison.user_id == user.id
                    ],
                    'self_evaluations': [comment for comment in answer_comments if
                        comment.user_id == user.id and
                        comment.comment_type == AnswerCommentType.self_evaluation
                    ]
                })


        on_assignment_users_comparisons_get.send(
            self,
            event_name=on_assignment_users_comparisons_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id}
        )

        return {"objects": marshal(comparison_sets, dataformat.get_comparison_set(restrict_user, with_user=True)),
                "comparison_total": comparison_total, "self_evaluation_total": self_evaluation_total,
                "page": page.page, "pages": page.pages, "total": page.total, "per_page": page.per_page}

api.add_resource(AssignmentUsersComparisonsAPI, '/<assignment_uuid>/users/comparisons')