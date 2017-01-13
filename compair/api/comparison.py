from __future__ import division
import operator
import random

from bouncer.constants import READ, CREATE, MANAGE
from flask import Blueprint, current_app
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from . import dataformat
from compair.core import db, event
from compair.authorization import require, allow
from compair.models import Answer, Comparison, Course, WinningAnswer, \
    Assignment, UserCourse, CourseRole, AssignmentCriterion
from .util import new_restful_api

from compair.algorithms import InsufficientObjectsForPairException, \
    UserComparedAllObjectsException, UnknownPairGeneratorException

# First declare a Flask Blueprint for this module
# Then pack the blueprint into a Flask-Restful API
comparison_api = Blueprint('comparison_api', __name__)
api = new_restful_api(comparison_api)

update_comparison_parser = RequestParser()
update_comparison_parser.add_argument('comparison_criteria', type=list, required=True, location='json')
update_comparison_parser.add_argument('draft', type=bool, default=False)

# events
on_comparison_get = event.signal('COMPARISON_GET')
on_comparison_create = event.signal('COMPARISON_CREATE')
on_comparison_update = event.signal('COMPARISON_UPDATE')

#messages
comparison_deadline_message = 'Assignment comparison deadline has passed.'
educators_can_not_compare_message = 'Only students can compare answers in this assignment.'

# /
class CompareRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        """
        Get (or create if needed) a comparison set for assignment.
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment)
        require(CREATE, Comparison)
        restrict_user = not allow(MANAGE, assignment)

        if not assignment.compare_grace:
            return {'error': comparison_deadline_message}, 403
        elif not restrict_user and not assignment.educators_can_compare:
            return {'error': educators_can_not_compare_message}, 403

        # check if user has a comparison they have not completed yet
        new_pair = False
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
                    skip_comparison_examples=allow(MANAGE, assignment))
                new_pair = True

                on_comparison_create.send(
                    self,
                    event_name=on_comparison_create.name,
                    user=current_user,
                    course_id=course.id,
                    data=marshal(comparison, dataformat.get_comparison(restrict_user)))

            except InsufficientObjectsForPairException:
                return {"error": "Not enough answers are available for a comparison."}, 400
            except UserComparedAllObjectsException:
                return {"error": "You have compared all the currently available answers."}, 400
            except UnknownPairGeneratorException:
                return {"error": "Generating scored pairs failed, this really shouldn't happen."}, 500

        comparison_count = assignment.completed_comparison_count_for_user(current_user.id)

        return {
            'comparison': marshal(comparison, dataformat.get_comparison(restrict_user)),
            'new_pair': new_pair,
            'current': comparison_count+1
        }

    @login_required
    def post(self, course_uuid, assignment_uuid):
        """
        Stores comparison set into the database.
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment)
        require(CREATE, Comparison)
        restrict_user = not allow(MANAGE, assignment)

        if not assignment.compare_grace:
            return {'error': comparison_deadline_message}, 403
        elif not restrict_user and not assignment.educators_can_compare:
            return {'error': educators_can_not_compare_message}, 403

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
            return {"error": "There are no comparisons open for evaluation."}, 400

        is_comparison_example = comparison.comparison_example_id != None

        # check if number of comparison criteria submitted matches number of comparison criteria needed
        if len(comparison.comparison_criteria) != len(params['comparison_criteria']):
            return {"error": "Not all criteria were evaluated."}, 400

        if params.get('draft'):
            completed = False

        # check if each comparison has a criterion Id and a winner id
        for comparison_criterion_update in params['comparison_criteria']:
            # ensure criterion param is present
            if 'criterion_id' not in comparison_criterion_update:
                return {"error": "Missing criterion_id in evaluation."}, 400

            # set default values for cotnent and winner
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
                        return {"error": "Selected answer is invalid."}, 400

                    break
            if not known_criterion:
                return {"error": "Unknown criterion submitted!"}, 400


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

        return {'comparison': marshal(comparison, dataformat.get_comparison(restrict_user))}

api.add_resource(CompareRootAPI, '')
