from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal

from . import dataformat
from .core import event
from .models import CriteriaAndCourses, Courses
from .util import new_restful_api


criteria_api = Blueprint('criteria_api', __name__)
api = new_restful_api(criteria_api)

# events
on_criteria_list_get = event.signal('CRITERIA_LIST_GET')

# /
class CriteriaRootAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		course_criteria = CriteriaAndCourses.query.filter_by(course=course)\
			.order_by(CriteriaAndCourses.id).all()

		on_criteria_list_get.send(
			current_app._get_current_object(),
			event_name=on_criteria_list_get.name,
			user=current_user,
			course_id=course_id)

		return {"objects": marshal(course_criteria, dataformat.getCriteriaAndCourses())}
api.add_resource(CriteriaRootAPI, '')