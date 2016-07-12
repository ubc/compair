import datetime

import dateutil.parser
from bouncer.constants import MANAGE, READ, CREATE, EDIT
from flask import Blueprint, current_app
from flask.ext.restful import Resource, marshal_with, marshal, reqparse, abort
from flask_login import login_required, current_user
from sqlalchemy import exc, func

from . import dataformat
from acj.authorization import require
from acj.core import db, event
from acj.models import Course, CourseRole, UserCourse, Answer
from .util import pagination, new_restful_api, get_model_changes

course_api = Blueprint('course_api', __name__)
api = new_restful_api(course_api)

new_course_parser = reqparse.RequestParser()
new_course_parser.add_argument('name', type=str, required=True, help='Course name is required.')
new_course_parser.add_argument('year', type=int, required=True, help='Course year is required.')
new_course_parser.add_argument('term', type=str, required=True, help='Course term/semester is required.')
new_course_parser.add_argument('description', type=str)
new_course_parser.add_argument('start_date', type=str, default=None)
new_course_parser.add_argument('end_date', type=str, default=None)

existing_course_parser = new_course_parser.copy()
existing_course_parser.add_argument('id', type=int, required=True, help='Course id is required.')

# events
on_course_modified = event.signal('COURSE_MODIFIED')
on_course_get = event.signal('COURSE_GET')
on_course_list_get = event.signal('COURSE_LIST_GET')
on_course_create = event.signal('COURSE_CREATE')


class CourseListAPI(Resource):
    @login_required
    @pagination(Course)
    @marshal_with(dataformat.get_course())
    def get(self, objects):
        """
        Get a list of courses
        """
        require(MANAGE, Course)
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
        require(CREATE, Course)
        params = new_course_parser.parse_args()

        new_course = Course(
            name=params.get("name"),
            year=params.get("year"),
            term=params.get("term"),
            description=params.get("description", None),
            start_date=params.get('start_date', None),
            end_date=params.get('end_date', None)
        )
        if new_course.start_date is not None:
            new_course.start_date = datetime.datetime.strptime(
                new_course.start_date,
                '%Y-%m-%dT%H:%M:%S.%fZ')
        if new_course.end_date is not None:
            new_course.end_date = datetime.datetime.strptime(
                new_course.end_date,
                '%Y-%m-%dT%H:%M:%S.%fZ')

        try:
            # create the course
            db.session.add(new_course)
            # also need to enrol the user as an instructor
            new_user_course = UserCourse(
                course=new_course,
                user_id=current_user.id,
                course_role=CourseRole.instructor
            )
            db.session.add(new_user_course)

            db.session.commit()

            on_course_create.send(
                self,
                event_name=on_course_create.name,
                user=current_user,
                data=marshal(new_course, dataformat.get_course()))

        except exc.SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error("Failed to add new course. " + str(e))
            raise
        return marshal(new_course, dataformat.get_course())


api.add_resource(CourseListAPI, '')


class CourseAPI(Resource):
    @login_required
    def get(self, course_id):
        """
        Get a course by course id
        """
        course = Course.get_active_or_404(course_id)
        require(READ, course)
        on_course_get.send(
            self,
            event_name=on_course_get.name,
            user=current_user,
            data={'id': course_id})
        return marshal(course, dataformat.get_course())

    @login_required
    def post(self, course_id):
        """
        Update a course

        :param course_id:
        :return:
        """
        course = Course.get_active_or_404(course_id)
        require(EDIT, course)
        params = existing_course_parser.parse_args()
        # make sure the course id in the url and the course id in the params match
        if params['id'] != course_id:
            return {"error": "Course id does not match URL."}, 400
        # modify course according to new values, preserve original values if values not passed
        course.name = params.get("name", course.name)
        course.year = params.get("year", course.year)
        course.term = params.get("term", course.term)
        course.description = params.get("description", course.description)

        course.start_date = params.get("start_date", None)
        if course.start_date is not None:
            course.start_date = datetime.datetime.strptime(
                course.start_date,
                '%Y-%m-%dT%H:%M:%S.%fZ')

        course.end_date = params.get("end_date", None)
        if course.end_date is not None:
            course.end_date = datetime.datetime.strptime(
                course.end_date,
                '%Y-%m-%dT%H:%M:%S.%fZ')

        db.session.commit()

        on_course_modified.send(
            self,
            event_name=on_course_modified.name,
            user=current_user,
            data=get_model_changes(course))

        return marshal(course, dataformat.get_course())

api.add_resource(CourseAPI, '/<int:course_id>')