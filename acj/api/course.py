from bouncer.constants import MANAGE, READ, CREATE, EDIT
from flask import Blueprint, current_app
from flask.ext.restful import Resource, marshal_with, marshal, reqparse, abort
from flask_login import login_required, current_user
from sqlalchemy import exc
from sqlalchemy.orm import joinedload, contains_eager, subqueryload

from . import dataformat
from acj.authorization import require
from acj.core import db, event
from acj.models import Courses, UserTypesForCourse, CoursesAndUsers, CriteriaAndCourses
from .util import pagination, new_restful_api, get_model_changes

courses_api = Blueprint('courses_api', __name__)
api = new_restful_api(courses_api)

new_course_parser = reqparse.RequestParser()
new_course_parser.add_argument('name', type=str, required=True, help='Course name is required.')
new_course_parser.add_argument('description', type=str)
new_course_parser.add_argument('enable_student_create_questions', type=bool, default=False)
new_course_parser.add_argument('enable_student_create_tags', type=bool, default=False)
# has to add location parameter, otherwise MultiDict will screw up the list
new_course_parser.add_argument('criteria', type=list, default=[], location='json')

existing_course_parser = new_course_parser.copy()
existing_course_parser.add_argument('id', type=int, required=True, help='Course id is required.')

# events
on_course_modified = event.signal('COURSE_MODIFIED')
on_course_get = event.signal('COURSE_GET')
on_course_list_get = event.signal('COURSE_LIST_GET')
on_course_create = event.signal('COURSE_CREATE')


class CourseListAPI(Resource):
    @login_required
    @pagination(Courses)
    @marshal_with(dataformat.get_courses())
    def get(self, objects):
        """
        Get a list of courses
        """
        require(MANAGE, Courses)
        on_course_list_get.send(
            self,
            event_name=on_course_list_get.name,
            user=current_user)
        return objects

    @login_required
    def post(self):
        """
        Create new course
        """
        require(CREATE, Courses)
        params = new_course_parser.parse_args()
        criteria_ids = [c['id'] for c in params.criteria]

        new_course = Courses(
            name=params.get("name"),
            description=params.get("description", None),
            enable_student_create_questions=params.get("enable_student_create_questions", False),
            enable_student_create_tags=params.get("enable_student_create_tags", False)
        )
        try:
            # create the course
            db.session.add(new_course)
            # also need to enrol the user as an instructor
            instructor_role = UserTypesForCourse.query \
                .filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).first()
            new_courseanduser = CoursesAndUsers(
                course=new_course, users_id=current_user.id, usertypeforcourse=instructor_role)
            db.session.add(new_courseanduser)

            for c in criteria_ids:
                course_assoc = CriteriaAndCourses(course=new_course, criteria_id=c)
                db.session.add(course_assoc)

            db.session.commit()

            on_course_create.send(
                self,
                event_name=on_course_create.name,
                user=current_user,
                data=marshal(new_course, dataformat.get_courses()))

        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to add new course. Duplicate.")
            return {"error": "A course with the same name already exists."}, 400
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error("Failed to add new course. " + str(e))
            raise
        return marshal(new_course, dataformat.get_courses())


api.add_resource(CourseListAPI, '/courses')


class CourseAPI(Resource):
    @login_required
    def get(self, course_id):
        """
        Get a course by course id
        """
        course = Courses.query.\
            options(joinedload("criteriaandcourses").joinedload("criterion")).\
            get_or_404(course_id)
        require(READ, course)
        on_course_get.send(
            self,
            event_name=on_course_get.name,
            user=current_user,
            data={'id': course_id})
        return marshal(course, dataformat.get_courses())

    @login_required
    def post(self, course_id):
        """
        Update a course

        :param course_id:
        :return:
        """
        course = Courses.query. \
            outerjoin(CriteriaAndCourses, Courses.id == CriteriaAndCourses.courses_id). \
            options(contains_eager('criteriaandcourses')). \
            filter(Courses.id == course_id).all()
        if not course:
            abort(404)
        course = course[0]
        require(EDIT, course)
        params = existing_course_parser.parse_args()
        criteria_ids = [c['id'] for c in params.criteria]
        # make sure the course id in the url and the course id in the params match
        if params['id'] != course_id:
            return {"error": "Course id does not match URL."}, 400
        # modify course according to new values, preserve original values if values not passed
        course.name = params.get("name", course.name)
        course.description = params.get("description", course.description)
        course.enable_student_create_questions = params.get(
            "enable_student_create_questions",
            course.enable_student_create_questions)
        course.enable_student_create_tags = params.get(
            "enable_student_create_tags",
            course.enable_student_create_tags)
        # remove the ones that are not in the list
        for c in course.criteriaandcourses:
            if c.criteria_id not in criteria_ids:
                # inactive if being used
                if c.in_question:
                    c.active = False
                else:
                    db.session.delete(c)
        # add the new ones
        existing_ids = [c.criteria_id for c in course.criteriaandcourses]
        for criteria_id in criteria_ids:
            if criteria_id not in existing_ids:
                assoc = CriteriaAndCourses(courses_id=course_id, criteria_id=criteria_id)
                course.criteriaandcourses.append(assoc)
        db.session.commit()

        on_course_modified.send(
            self,
            event_name=on_course_modified.name,
            user=current_user,
            data=get_model_changes(course))

        return marshal(course, dataformat.get_courses())

api.add_resource(CourseAPI, '/courses/<int:course_id>')
