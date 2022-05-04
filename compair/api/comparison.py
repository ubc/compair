from __future__ import division
import datetime

from bouncer.constants import READ, CREATE, EDIT, MANAGE
from flask import Blueprint, current_app
from flask_bouncer import can
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require
from compair.models import Answer, Comparison, Course, WinningAnswer, \
    Assignment, UserCourse, CourseRole, AssignmentCriterion, \
    AnswerComment, AnswerCommentType
from .util import new_restful_api

from compair.algorithms import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

# First declare a Flask Blueprint for this module
# Then pack the blueprint into a Flask-Restful API
comparison_api = Blueprint('comparison_api', __name__)
api = new_restful_api(comparison_api)

update_comparison_parser = RequestParser()
update_comparison_parser.add_argument('comparison_criteria', type=list, required=True, nullable=False, location='json')
update_comparison_parser.add_argument('draft', type=bool, default=False)
update_comparison_parser.add_argument('attempt_uuid', default=None)
update_comparison_parser.add_argument('attempt_started', default=None)
update_comparison_parser.add_argument('attempt_ended', default=None)

# events
on_comparison_get = event.signal('COMPARISON_GET')
on_comparison_create = event.signal('COMPARISON_CREATE')
on_comparison_update = event.signal('COMPARISON_UPDATE')

# /
class CompareRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        """
        Get (or create if needed) a comparison set for assignment.
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Comparisons Unavailable",
            message="Assignments and their comparisons can only be seen here by those enrolled in the course. Please double-check your enrollment in this course.")
        require(CREATE, Comparison,
            title="Comparisons Unavailable",
            message="Comparisons can only be seen here by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, assignment)

        comparison_count = assignment.completed_comparison_count_for_user(current_user.id)

        if not assignment.compare_grace:
            abort(403, title="Comparisons Unavailable",
                message="Sorry, the comparison deadline has passed. No comparisons can be done after the deadline.")
        elif not restrict_user and not assignment.educators_can_compare:
            abort(403, title="Comparisons Unavailable",
                message="Only students can currently compare answers for this assignment. To change these settings to include instructors and teaching assistants, edit the assignment.")
        elif restrict_user and comparison_count >= assignment.total_comparisons_required:
            abort(400, title="Comparisons Completed",
                message="More comparisons aren't available, since you've finished your comparisons for this assignment. Good job!")

        # check if user has a comparison they have not completed yet
        comparison = Comparison.query \
            .options(joinedload('comparison_criteria')) \
            .filter_by(
                assignment_id=assignment.id,
                user_id=current_user.id,
                completed=False
            ) \
            .first()

        if comparison:
            on_comparison_get.send(
                self,
                event_name=on_comparison_get.name,
                user=current_user,
                course_id=course.id,
                data=marshal(comparison, dataformat.get_comparison(restrict_user)))
        else:
            # if there isn't an incomplete comparison, assign a new one
            try:
                comparison = Comparison.create_new_comparison(assignment.id, current_user.id,
                    skip_comparison_examples=can(MANAGE, assignment))

                on_comparison_create.send(
                    self,
                    event_name=on_comparison_create.name,
                    user=current_user,
                    course_id=course.id,
                    data=marshal(comparison, dataformat.get_comparison(restrict_user)))

            except InsufficientObjectsForPairException:
                abort(400, title="Comparisons Unavailable", message="Not enough answers are available for you to do comparisons right now. Please check back later for more answers.")
            except UserComparedAllObjectsException:
                abort(400, title="Comparisons Unavailable", message="You have compared all the currently available answer pairs. Please check back later for more answers.")
            except UnknownPairGeneratorException:
                abort(500, title="Comparisons Unavailable", message="Generating scored pairs failed, this really shouldn't happen.")


        # get evaluation comments for answers by current user
        answer_comments = AnswerComment.query \
            .join("answer") \
            .filter(and_(
                # both draft and completed comments are allowed
                AnswerComment.active == True,
                AnswerComment.comment_type == AnswerCommentType.evaluation,
                Answer.id.in_([comparison.answer1_id, comparison.answer2_id]),
                AnswerComment.user_id == current_user.id
            )) \
            .order_by(AnswerComment.draft, AnswerComment.created) \
            .all()

        comparison.answer1_feedback = [c for c in answer_comments if c.answer_id == comparison.answer1_id]
        comparison.answer2_feedback = [c for c in answer_comments if c.answer_id == comparison.answer2_id]

        return {
            'comparison': marshal(comparison, dataformat.get_comparison(restrict_user,
                include_answer_author=False, include_score=False, with_feedback=True)),
            'current': comparison_count+1
        }

    @login_required
    def post(self, course_uuid, assignment_uuid):
        """
        Stores comparison set into the database.
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment,
            title="Comparison Not Saved",
            message="Comparisons can only be saved by those enrolled in the course. Please double-check your enrollment in this course.")
        require(EDIT, Comparison,
            title="Comparison Not Saved",
            message="Comparisons can only be saved by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, assignment)

        if not assignment.compare_grace:
            abort(403, title="Comparison Not Saved",
                message="Sorry, the comparison deadline has passed. No comparisons can be done after the deadline.")
        elif not restrict_user and not assignment.educators_can_compare:
            abort(403, title="Comparison Not Saved",
                message="Only students can save answer comparisons for this assignment. To change these settings to include instructors and teaching assistants, edit the assignment.")

        comparison = Comparison.query \
            .options(joinedload('comparison_criteria')) \
            .filter_by(
                assignment_id=assignment.id,
                user_id=current_user.id,
                completed=False
            ) \
            .first()

        params = update_comparison_parser.parse_args()
        completed = True

        # check if there are any comparisons to update
        if not comparison:
            abort(400, title="Comparison Not Saved", message="There are no comparisons open for evaluation.")

        is_comparison_example = comparison.comparison_example_id != None

        # check if number of comparison criteria submitted matches number of comparison criteria needed
        if len(comparison.comparison_criteria) != len(params['comparison_criteria']):
            abort(400, title="Comparison Not Saved", message="Please double-check that all criteria were evaluated and try saving again.")

        if params.get('draft'):
            completed = False

        # check if each comparison has a criterion Id and a winner id
        for comparison_criterion_update in params['comparison_criteria']:
            # ensure criterion param is present
            if 'criterion_id' not in comparison_criterion_update:
                abort(400, title="Comparison Not Saved", message="Sorry, the assignment is missing criteria. Please reload the page and try again.")

            # set default values for content and winner
            comparison_criterion_update.setdefault('content', None)
            winner = comparison_criterion_update.setdefault('winner', None)

            # if winner isn't set for any comparison criterion, then the comparison isn't complete yet
            if winner == None:
                completed = False

            # check that we're using criteria that were assigned to the course and that we didn't
            # get duplicate criteria in comparison criteria
            known_criterion = False
            for comparison_criterion in comparison.comparison_criteria:
                if comparison_criterion_update['criterion_id'] == comparison_criterion.criterion_uuid:
                    known_criterion = True

                    # check that the winner id matches one of the answer pairs
                    if winner not in [None, WinningAnswer.answer1.value, WinningAnswer.answer2.value]:
                        abort(400, title="Comparison Not Saved", message="Please select an answer from the two answers provided for each criterion and try saving again.")

                    break
            if not known_criterion:
                abort(400, title="Comparison Not Saved", message="You are attempting to submit a comparison of an unknown criterion. Please remove the unknown criterion and try again.")


        # update comparison criterion
        comparison.completed = completed
        comparison.winner = None

        assignment_criteria = assignment.assignment_criteria
        answer1_weight = 0
        answer2_weight = 0

        for comparison_criterion in comparison.comparison_criteria:
            for comparison_criterion_update in params['comparison_criteria']:
                if comparison_criterion_update['criterion_id'] != comparison_criterion.criterion_uuid:
                    continue

                winner = WinningAnswer(comparison_criterion_update['winner']) if comparison_criterion_update['winner'] != None else None

                comparison_criterion.winner = winner
                comparison_criterion.content = comparison_criterion_update['content']

                if completed:
                    weight = next((
                        assignment_criterion.weight for assignment_criterion in assignment_criteria \
                        if assignment_criterion.criterion_uuid == comparison_criterion.criterion_uuid
                    ), 0)
                    if winner == WinningAnswer.answer1:
                        answer1_weight += weight
                    elif winner == WinningAnswer.answer2:
                        answer2_weight += weight

        if completed:
            if answer1_weight > answer2_weight:
                comparison.winner = WinningAnswer.answer1
            elif answer1_weight < answer2_weight:
                comparison.winner = WinningAnswer.answer2
            else:
                comparison.winner = WinningAnswer.draw
        else:
            # ensure that the comparison is 'touched' when saving a draft
            comparison.modified = datetime.datetime.utcnow()

        comparison.update_attempt(
            params.get('attempt_uuid'),
            params.get('attempt_started', None),
            params.get('attempt_ended', None)
        )

        db.session.commit()

        # update answer scores
        if completed and not is_comparison_example:
            current_app.logger.debug("Doing scoring")
            Comparison.update_scores_1vs1(comparison)
            #Comparison.calculate_scores(assignment.id)

        # update course & assignment grade for user if comparison is completed
        if completed:
            assignment.calculate_grade(current_user)
            course.calculate_grade(current_user)

        on_comparison_update.send(
            self,
            event_name=on_comparison_update.name,
            user=current_user,
            course_id=course.id,
            assignment=assignment,
            comparison=comparison,
            is_comparison_example=is_comparison_example,
            data=marshal(comparison, dataformat.get_comparison(restrict_user)))

        return {'comparison': marshal(comparison, dataformat.get_comparison(restrict_user, include_answer_author=False, include_score=False))}

api.add_resource(CompareRootAPI, '')
