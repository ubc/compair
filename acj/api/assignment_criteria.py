from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import or_, and_
from sqlalchemy.orm import load_only, contains_eager

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from acj.models import Course, Criteria, Assignment, AssignmentCriteria, Comparison
from .util import new_restful_api

assignment_criteria_api = Blueprint('assignment_criteria_api', __name__)
api = new_restful_api(assignment_criteria_api)

# events
on_assignment_criteria_create = event.signal('ASSIGNMENT_CRITERIA_CREATE')
on_assignment_criteria_delete = event.signal('ASSIGNMENT_CRITERIA_DELETE')
on_assignment_criteria_get = event.signal('ASSIGNMENT_CRITERIA_GET')

# /
class AssignmentCriteriaRootAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        course = Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, course)

        assignment_criteria = AssignmentCriteria.query \
            .filter_by(assignment_id=assignment.id, active=True) \
            .order_by(AssignmentCriteria.id).all()

        on_assignment_criteria_get.send(
            self,
            event_name=on_assignment_criteria_get.name,
            user=current_user
        )

        return marshal(assignment_criteria, dataformat.get_assignment_criteria())


api.add_resource(AssignmentCriteriaRootAPI, '')


# /criteria_id
class AssignmentCriteriaAPI(Resource):
    @login_required
    def post(self, course_id, assignment_id, criteria_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        Criteria.get_active_or_404(criteria_id)

        assignment = Assignment(course_id=course_id)
        assignment_criteria = AssignmentCriteria(assignment=assignment)
        require(CREATE, assignment_criteria)

        assignment_criteria = AssignmentCriteria.query.filter_by(criteria_id=criteria_id). \
            filter_by(assignment_id=assignment_id).first()
        if assignment_criteria:
            assignment_criteria.active = True
        else:
            assignment_criteria = AssignmentCriteria(
                criteria_id=criteria_id,
                assignment_id=assignment_id
            )

        db.session.add(assignment_criteria)

        on_assignment_criteria_create.send(
            self,
            event_name=on_assignment_criteria_create.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'criteria_id': criteria_id})

        db.session.commit()

        return marshal(assignment_criteria, dataformat.get_assignment_criteria())

    @login_required
    def delete(self, course_id, assignment_id, criteria_id):
        Course.get_active_or_404(course_id)

        assignment_criteria = AssignmentCriteria.query. \
            filter_by(
                criteria_id=criteria_id,
                assignment_id=assignment_id,
                active=True
            ). \
            first_or_404()

        require(DELETE, assignment_criteria)

        comparison = Comparison.query \
            .filter_by(
                criteria_id=criteria_id,
                assignment_id=assignment_id,
            ) \
            .first()
        # if a comparison has already been made - don't remove from assignment
        if comparison:
            msg = \
                'The criterion cannot be removed from the assignment, ' + \
                'because the criterion is already used in an evaluation.'
            return {"error": msg}, 403

        assignment_criteria.active = False
        db.session.add(assignment_criteria)

        on_assignment_criteria_delete.send(
            self,
            event_name=on_assignment_criteria_delete.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'criteria_id': criteria_id}
        )

        db.session.commit()

        return marshal(assignment_criteria, dataformat.get_assignment_criteria())


api.add_resource(AssignmentCriteriaAPI, '/<int:criteria_id>')