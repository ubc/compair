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
on_assignment_criterion_get = event.signal('ASSIGNMENT_CRITERION_GET')

# /
class AssignmentCriterionRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
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