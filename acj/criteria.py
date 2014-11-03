from flask import Blueprint, current_app
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse
from sqlalchemy import or_, and_

from . import dataformat
from .core import event, db
from .authorization import require, allow
from .models import CriteriaAndCourses, Courses, Criteria, PostsForQuestions, CriteriaAndPostsForQuestions, \
				Judgements, Posts
from .util import new_restful_api


coursescriteria_api = Blueprint('coursescriteria_api', __name__)
api = new_restful_api(coursescriteria_api)

criteria_api = Blueprint('criteria_api', __name__)
apiC = new_restful_api(criteria_api)

questionscriteria_api = Blueprint('questionscriteria_api', __name__)
apiQ = new_restful_api(questionscriteria_api)

new_criterion_parser = reqparse.RequestParser()
new_criterion_parser.add_argument('name', type=str, required=True)
new_criterion_parser.add_argument('description', type=str)
new_criterion_parser.add_argument('default', type=bool, default=True)

existing_criterion_parser = reqparse.RequestParser()
existing_criterion_parser.add_argument('id', type=int, required=True)
existing_criterion_parser.add_argument('name', type=str, required=True)
existing_criterion_parser.add_argument('description', type=str)
existing_criterion_parser.add_argument('default', type=bool, default=True)

# events
on_criteria_list_get = event.signal('CRITERIA_LIST_GET')
criteria_post = event.signal('CRITERIA_POST')
criteria_get = event.signal('CRITERIA_GET')
criteria_update = event.signal('CRITERIA_EDIT')

accessible_criteria = event.signal('ACCESSIBLE_CRITERIA_GET')
criteria_create = event.signal('CRITERIA_CREATE')
default_criteria_get = event.signal('DEFAULT_CRITERIA_GET')

on_course_criteria_delete = event.signal('COURSE_CRITERIA_DELETE')
on_course_criteria_update = event.signal('COURSE_CRITERIA_UPDATE')

on_question_criteria_create = event.signal('QUESTION_CRITERIA_CREATE')
on_question_criteria_delete = event.signal('QUESTION_CRITERIA_DELETE')

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

		question_criterion = CriteriaAndPostsForQuestions.query\
			.filter_by(criteria_id=criteria_id, active=True)\
			.join(PostsForQuestions, Posts).filter_by(courses_id=course_id).first()
		if question_criterion:
			msg = 'The criterion cannot be removed from the course, ' + \
				  'because the criterion is currently used in a question.'
			return {'error': msg}, 403

		require(DELETE, course_criterion)
		course_criterion.active = False
		db.session.add(course_criterion)

		on_course_criteria_delete.send(
			current_app._get_current_object(),
			event_name=on_course_criteria_delete.name,
			user=current_user,
			course_id=course_id,
			data={'criteria_id': criteria_id}
		)

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

		on_course_criteria_update.send(
			current_app._get_current_object(),
			event_name=on_course_criteria_update.name,
			user=current_user,
			course_id=course_id,
			data={'criteria_id': criteria_id})

		db.session.commit()
		return {'criterion': marshal(course_criterion, dataformat.getCriteriaAndCourses())}
api.add_resource(CourseCriteriaIdAPI, '/<int:criteria_id>')

#/criteria - public + authored/default
# default = want criterion available to all of the author's courses
class CriteriaAPI(Resource):
	@login_required
	def get(self):
		if allow(MANAGE, Criteria):
			criteria = Criteria.query.all()
		else:
			criteria = Criteria.query.filter(or_(and_(Criteria.users_id==current_user.id, Criteria.default==True), Criteria.public==True)).all()

		accessible_criteria.send(
			current_app._get_current_object(),
			event_name=accessible_criteria.name,
			user=current_user)

		return {'criteria': marshal(criteria, dataformat.getCriteria())}
	@login_required
	def post(self):
		params = new_criterion_parser.parse_args()
		criterion = addCriteria(params)
		require(CREATE, criterion)

		criteria_create.send(
			current_app._get_current_object(),
			event_name=criteria_create.name,
			user=current_user,
			data={'criterion': marshal(criterion, dataformat.getCriteria())}
		)

		db.session.commit()
		return marshal(criterion, dataformat.getCriteria())
apiC.add_resource(CriteriaAPI, '')

# /default - get default criteria - eg. first criterion
class DefaultCriteria(Resource):
	@login_required
	def get(self):
		default = Criteria.query.first()

		default_criteria_get.send(
			current_app._get_current_object(),
			event_name=default_criteria_get.name,
			data={'criteria': marshal(default, dataformat.getCriteria())}
		)

		return marshal(default, dataformat.getCriteria())
apiC.add_resource(DefaultCriteria, '/default')

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
		criterion.default = params.get('default', criterion.default)
		db.session.add(criterion)
		db.session.commit()

		criteria_update.send(
			current_app._get_current_object(),
			event_name = criteria_update.name,
			user=current_user
		)

		return {'criterion': marshal(criterion, dataformat.getCriteria())}
apiC.add_resource(CriteriaIdAPI, '/<int:criteria_id>')

# /criteria_id
class QuestionCriteriaAPI(Resource):
	@login_required
	def post(self, course_id, question_id, criteria_id):
		Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		Criteria.query.get_or_404(criteria_id)

		criteria_question = CriteriaAndPostsForQuestions(question=question)
		require(CREATE, criteria_question)

		criteria_question = CriteriaAndPostsForQuestions.query.filter_by(criteria_id=criteria_id).\
			filter_by(postsforquestions_id=question_id).first()
		if criteria_question:
			criteria_question.active = True
		else:
			criteria_question = CriteriaAndPostsForQuestions()
			criteria_question.criteria_id = criteria_id
			criteria_question.postsforquestions_id = question_id

		db.session.add(criteria_question)

		on_question_criteria_create.send(
			current_app._get_current_object(),
			event_name=on_question_criteria_create.name,
			user=current_user,
			course_id=course_id,
			data={'question_id': question_id, 'criteria_id': criteria_id})

		db.session.commit()

		return {'criterion': marshal(criteria_question, dataformat.getCriteriaAndPostsForQuestions())}

	@login_required
	def delete(self, course_id, question_id, criteria_id):
		Courses.query.get_or_404(course_id)

		criteria_question = CriteriaAndPostsForQuestions.query.filter_by(criteria_id=criteria_id).\
			filter_by(postsforquestions_id=question_id).first_or_404()

		require(DELETE, criteria_question)

		judgement = Judgements.query.filter_by(criteriaandpostsforquestions_id=criteria_question.id).first()
		# if a judgement has already been made - don't remove from question
		if judgement:
			msg = 'The criterion cannot be removed from the question, ' + \
				  'because the criterion is already used in an evaluation.'
			return {"error": msg}, 403

		criteria_question.active = False
		db.session.add(criteria_question)

		on_question_criteria_delete.send(
			current_app._get_current_object(),
			event_name=on_question_criteria_delete.name,
			user=current_user,
			course_id=course_id,
			data={'question_id':question_id, 'criteria_id':criteria_id}
		)

		db.session.commit()

		return {'criterion': marshal(criteria_question, dataformat.getCriteriaAndPostsForQuestions())}
apiQ.add_resource(QuestionCriteriaAPI, '/<int:criteria_id>')

def addCriteria(params):
	criterion = Criteria(
		name = params.get("name"),
		description = params.get("description", None),
		users_id = current_user.id,
		default = params.get("default")
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