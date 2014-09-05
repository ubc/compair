from flask import Blueprint
from flask.ext.login import login_required
from flask.ext.restful import Resource, marshal
import pprint
from acj import dataformat
from acj.models import CriteriaAndCourses, Courses
from acj.util import new_restful_api

criteria_api = Blueprint('criteria_api', __name__)
api = new_restful_api(criteria_api)

# /
class CriteriaRootAPI(Resource):
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		course_criteria = CriteriaAndCourses.query.filter_by(course=course)\
			.order_by(CriteriaAndCourses.id).all()
		return {"objects": marshal(course_criteria, dataformat.getCriteriaAndCourses())}
api.add_resource(CriteriaRootAPI, '')