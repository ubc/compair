from flask import Blueprint, current_app
from bouncer.constants import READ, EDIT, CREATE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse

from . import dataformat
from .core import event, db
from .authorization import require
from .models import CriteriaAndCourses, Courses, Criteria
from .util import new_restful_api


coursescriteria_api = Blueprint('coursescriteria_api', __name__)
api = new_restful_api(coursescriteria_api)

criteria_api = Blueprint('criteria_api', __name__)
apiC = new_restful_api(criteria_api)

new_criterion_parser = reqparse.RequestParser()
new_criterion_parser.add_argument('name', type=str, required=True)
new_criterion_parser.add_argument('description', type=str)

existing_criterion_parser = reqparse.RequestParser()
existing_criterion_parser.add_argument('id', type=int, required=True)
existing_criterion_parser.add_argument('name', type=str, required=True)
existing_criterion_parser.add_argument('description', type=str)

# events
on_criteria_list_get = event.signal('CRITERIA_LIST_GET')
criteria_post = event.signal('CRITERIA_POST')
criteria_get = event.signal('CRITERIA_GET')
criteria_update = event.signal('CRITERIA_EDIT')

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
	@login_required
	def post(self, course_id):
		course = Courses.query.get_or_404(course_id)
		params = new_criterion_parser.parse_args()
		criterion = addCriteria(params)
		require(CREATE, criterion)
		course_criterion = addCourseCriteria(criterion, course)
		require(CREATE, course_criterion)
		db.session.commit()

		criteria_post.send(
			current_app._get_current_object(),
			event_name = criteria_post.name,
			user=current_user,
			course_id=course_id
		)

		return {'criterion': marshal(course_criterion, dataformat.getCriteriaAndCourses())}
api.add_resource(CriteriaRootAPI, '')

# /criteria/:id
class CriteriaIdAPI(Resource):
	@login_required
	def get(self, criteria_id):
		criterion = Criteria.query.get_or_404(criteria_id)
		require(READ, criterion)

		criteria_get.send(
			current_app._get_current_object(),
			event_name = criteria_get.name,
			user = current_user,
			criterion_id = criterion.id
		)

		return {'criterion': marshal(criterion, dataformat.getCriteria())}
	@login_required
	def post(self, criteria_id):
		criterion = Criteria.query.get_or_404(criteria_id)
		require(EDIT, criterion)
		params = existing_criterion_parser.parse_args()
		criterion.name = params.get('name', criterion.name)
		criterion.description = params.get('description', criterion.description)
		db.session.add(criterion)
		db.session.commit()

		criteria_update.send(
			current_app._get_current_object(),
			event_name = criteria_update.name,
			user=current_user,
			criterion_id=criterion.id
		)

		return {'criterion': marshal(criterion, dataformat.getCriteria())}
apiC.add_resource(CriteriaIdAPI, '/<int:criteria_id>')

def addCriteria(params):
	criterion = Criteria(
		name = params.get("name"),
		description = params.get("description", None),
		users_id = current_user.id
	)
	db.session.add(criterion)
	return criterion

def addCourseCriteria(criterion, course):
	course_criterion = CriteriaAndCourses(
		criterion = criterion,
		courses_id = course.id,
	)
	db.session.add(course_criterion)
	return course_criterion