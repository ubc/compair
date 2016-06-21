from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import or_, and_

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from acj.models import Course, Criterion, Assignment, AssignmentCriterion, Comparison
from .util import new_restful_api

assignment_criterion_api = Blueprint('assignment_criterion_api', __name__)
api = new_restful_api(assignment_criterion_api)

# events
on_assignment_criterion_create = event.signal('ASSIGNMENT_CRITERION_CREATE')
on_assignment_criterion_delete = event.signal('ASSIGNMENT_CRITERION_DELETE')
on_assignment_criterion_get = event.signal('ASSIGNMENT_CRITERION_GET')

# /
class AssignmentCriterionRootAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        course = Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, course)

        criteria = Criterion.query \
            .join(AssignmentCriterion) \
            .filter(and_(
                AssignmentCriterion.assignment_id == assignment.id,
                AssignmentCriterion.active == True,
                Criterion.active == True)
            ) \
            .all()

        assignment_criteria = AssignmentCriterion.query \
            .filter_by(assignment_id=assignment.id, active=True) \
            .order_by(AssignmentCriterion.id) \
            .all()

        on_assignment_criterion_get.send(
            self,
            event_name=on_assignment_criterion_get.name,
            user=current_user
        )

        return {'objects': marshal(criteria, dataformat.get_criterion()) }


api.add_resource(AssignmentCriterionRootAPI, '')


# /criterion_id
class AssignmentCriteriaAPI(Resource):
    @login_required
    def post(self, course_id, assignment_id, criterion_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        Criterion.get_active_or_404(criterion_id)

        assignment = Assignment(course_id=course_id)
        assignment_criterion = AssignmentCriterion(assignment=assignment)
        require(CREATE, assignment_criterion)

        assignment_criterion = AssignmentCriterion.query \
            .filter_by(criterion_id=criterion_id) \
            .filter_by(assignment_id=assignment_id) \
            .first()

        if assignment_criterion:
            assignment_criterion.active = True
        else:
            assignment_criterion = AssignmentCriterion(
                criterion_id=criterion_id,
                assignment_id=assignment_id
            )

        db.session.add(assignment_criterion)

        on_assignment_criterion_create.send(
            self,
            event_name=on_assignment_criterion_create.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'criterion_id': criterion_id})

        db.session.commit()

        return marshal(assignment_criterion.criterion, dataformat.get_criterion())

    @login_required
    def delete(self, course_id, assignment_id, criterion_id):
        Course.get_active_or_404(course_id)

        assignment_criterion = AssignmentCriterion.query. \
            filter_by(
                criterion_id=criterion_id,
                assignment_id=assignment_id,
                active=True
            ). \
            first_or_404()

        require(DELETE, assignment_criterion)

        comparison = Comparison.query \
            .filter_by(
                criterion_id=criterion_id,
                assignment_id=assignment_id,
            ) \
            .first()

        # if a comparison has already been made - don't remove from assignment
        if comparison:
            msg = \
                'The criterion cannot be removed from the assignment, ' + \
                'because the criterion is already used in an evaluation.'
            return {"error": msg}, 403

        assignment_criterion.active = False
        db.session.add(assignment_criterion)

        on_assignment_criterion_delete.send(
            self,
            event_name=on_assignment_criterion_delete.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'criterion_id': criterion_id}
        )

        db.session.commit()

        return marshal(assignment_criterion.criterion, dataformat.get_criterion())


api.add_resource(AssignmentCriteriaAPI, '/<int:criterion_id>')