from flask import Blueprint, current_app
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse
from sqlalchemy import or_

from . import dataformat
from .core import event, db
from .authorization import require, allow
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
		course_criteria = criteriaInCourse(course_id)

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

# /id
class CourseCriteriaIdAPI(Resource):
	@login_required
	def delete(self, course_id, criteria_id):
		course_criterion = CriteriaAndCourses.query.filter_by(criteria_id=criteria_id)\
			.filter_by(courses_id=course_id).first_or_404()
		require(DELETE, course_criterion)
		course_criterion.active = False
		db.session.add(course_criterion)
		db.session.commit()
		return {'criterionId': criteria_id}
	@login_required
	def post(self, course_id, criteria_id):
		course = Courses.query.get_or_404(course_id)
		criterion = Criteria.query.get_or_404(criteria_id)
		course_criterion = CriteriaAndCourses.query.filter_by(criteria_id=criteria_id)\
			.filter_by(courses_id=course_id).first()
		if course_criterion:
			course_criterion.active = True
			db.session.add(course_criterion)
		else:
			course_criterion = addCourseCriteria(criterion, course)
		require(CREATE, course_criterion)
		db.session.commit()
		return {'criterion': marshal(course_criterion, dataformat.getCriteriaAndCourses())}
api.add_resource(CourseCriteriaIdAPI, '/<int:criteria_id>')

#/criteria - public + authored
class CriteriaAPI(Resource):
	@login_required
	def get(self):
		if allow(MANAGE, Criteria):
			criteria = Criteria.query.all()
		else:
			criteria = Criteria.query.filter(or_(Criteria.users_id==current_user.id, Criteria.public==True)).all()
		return {'criteria': marshal(criteria, dataformat.getCriteria())}
apiC.add_resource(CriteriaAPI, '')

# /criteria/:id
class CriteriaIdAPI(Resource):
	@login_required
	def get(self, criteria_id):
		criterion = Criteria.query.get_or_404(criteria_id)
		require(READ, criterion)

		criteria_get.send(
			current_app._get_current_object(),
			event_name = criteria_get.name,
			user = current_user
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
			user=current_user
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

def criteriaInCourse(course_id):
	course_criteria = CriteriaAndCourses.query.filter_by(courses_id=course_id)\
		.filter_by(active=True).order_by(CriteriaAndCourses.id).all()
	return course_criteria