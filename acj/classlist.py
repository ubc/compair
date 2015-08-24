import os
import uuid
import csv
import string

from bouncer.constants import EDIT, READ
from flask import Blueprint, request, current_app, make_response
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, abort
from six import StringIO
from sqlalchemy import and_
from sqlalchemy.orm import joinedload, contains_eager
from werkzeug.utils import secure_filename

from flask.ext.restful.reqparse import RequestParser

from . import dataformat
from .core import db
from .authorization import allow, require
from .core import event
from .models import CoursesAndUsers, Courses, Users, UserTypesForSystem, UserTypesForCourse, GroupsAndUsers
from .util import new_restful_api
from .attachment import random_generator, allowed_file

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

new_course_user_parser = RequestParser()
new_course_user_parser.add_argument('course_role_id', type=int)
new_course_user_parser.add_argument('course_role', type=str)

# upload file column name to index number
USERNAME = 0
STUDENTNO = 1
FIRSTNAME = 2
LASTNAME = 3
EMAIL = 4
DISPLAYNAME = 5
PASSWORD = 6

# events
on_classlist_get = event.signal('CLASSLIST_GET')
on_classlist_upload = event.signal('CLASSLIST_UPLOAD')
on_classlist_enrol = event.signal('CLASSLIST_ENROL')
on_classlist_unenrol = event.signal('CLASSLIST_UNENROL')
on_classlist_instructor_label = event.signal('CLASSLIST_INSTRUCTOR_LABEL_GET')
on_classlist_instructor = event.signal('CLASSLIST_INSTRUCTOR_GET')
on_classlist_student = event.signal('CLASSLIST_STUDENT_GET')


def display_name_generator(role="student"):
    return "".join([role, '_', random_generator(8, string.digits)])


def import_users(course_id, users):
    invalids = []  # invalid entries - eg. invalid # of columns
    # store unique user identifiers - eg. student number - throws error if duplicate in file
    exist_usernames = []
    exist_studentnos = []
    count = 0  # store number of successful enrolments

    # constants
    letters_digits = string.ascii_letters + string.digits
    normal_user = UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_NORMAL).first().id
    student = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first().id
    dropped = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id

    usernames = [u[USERNAME] for u in users if len(u) > USERNAME]
    usernames_system = Users.query.filter(Users.username.in_(usernames)).all()
    usernames_system = {u.username: u for u in usernames_system}

    student_no = [u[STUDENTNO] for u in users if len(u) > STUDENTNO]
    if len(student_no) > 0:
        studentno_system = Users.query.filter(Users.student_no.in_(student_no)).all()
        studentno_system = {u.student_no: u.username for u in studentno_system}
    else:
        studentno_system = {}

    # create / update users in file
    for user in users:
        length = len(user)
        if length < 1:
            continue  # skip empty row

        # TEMP USER
        temp = Users()
        temp.username = user[USERNAME].lower() if length > USERNAME and user[USERNAME] else None

        # VALIDATION
        # validate username
        if not temp.username:
            invalids.append({'user': temp, 'message': 'The username is required.'})
            continue
        elif temp.username in exist_usernames:
            invalids.append({'user': temp, 'message': 'This username already exists in the file.'})
            continue

        u = usernames_system.get(temp.username, None)
        if not u:
            u = temp
        else:
            # user exists in the system, skip user creation
            exist_usernames.append(u.username)
            usernames_system.setdefault(u.username, u)
            exist_studentnos.append(u.student_no)
            studentno_system.setdefault(u.student_no, u.username)
            continue

        u.student_no = user[STUDENTNO] if length > STUDENTNO and user[STUDENTNO] else None
        u.firstname = user[FIRSTNAME] if length > FIRSTNAME and user[FIRSTNAME] else None
        u.lastname = user[LASTNAME] if length > LASTNAME and user[LASTNAME] else None
        u.email = user[EMAIL] if length > EMAIL and user[EMAIL] else None
        u.password = user[PASSWORD] if length > PASSWORD and user[PASSWORD] else random_generator(16, letters_digits)

        # validate student number (if not None)
        if u.student_no:
            # invalid if already showed up in file
            if u.student_no in exist_studentnos:
                invalids.append({'user': u, 'message': 'This student number already exists in the file.'})
                continue
            # invalid if student number already exists in the system
            elif u.student_no in studentno_system:
                invalids.append({'user': u, 'message': 'This student number already exists in the system.'})
                continue

        u.usertypesforsystem_id = normal_user
        displayname = user[DISPLAYNAME] if length > DISPLAYNAME and user[DISPLAYNAME] else None
        u.displayname = displayname if displayname else display_name_generator()

        exist_usernames.append(u.username)
        usernames_system.setdefault(u.username, u)
        exist_studentnos.append(u.student_no)
        studentno_system.setdefault(u.student_no, u.username)
        db.session.add(u)
    db.session.commit()

    enroled = CoursesAndUsers.query.filter_by(courses_id=course_id).all()
    enroled = {e.users_id: e for e in enroled}
    students = CoursesAndUsers.query.filter_by(courses_id=course_id, usertypesforcourse_id=student).all()
    students = {s.users_id: s for s in students}

    # enrol valid users in file
    to_enrol = Users.query.filter(Users.username.in_(exist_usernames)).all()
    for user in to_enrol:
        enrol = enroled.get(user.id, CoursesAndUsers(courses_id=course_id, users_id=user.id))
        enrol.usertypesforcourse_id = student
        db.session.add(enrol)
        if user.id in students:
            del students[user.id]
        count += 1
    db.session.commit()

    # unenrol users not in file anymore
    for users_id in students:
        enrolment = students.get(users_id)
        # skip users that are already dropped
        if enrolment.usertypesforcourse_id == dropped:
            continue
        enrolment.usertypesforcourse_id = dropped
        db.session.add(enrolment)
    db.session.commit()

    on_classlist_upload.send(
        current_app._get_current_object(),
        event_name=on_classlist_upload.name,
        user=current_user,
        course_id=course_id
    )

    return {
        'success': count,
        'invalids': marshal(invalids, dataformat.get_import_users_results(False))
    }


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    fieldnames = ['username', 'student_no', 'firstname', 'lastname', 'email', 'displayname']
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data['objects'])
    response = make_response(csv_buffer.getvalue(), code)
    response.headers.extend(headers or {})
    response.headers['Content-Disposition'] = 'attachment;filename=classlist.csv'
    return response


# /
class ClasslistRootAPI(Resource):
    # TODO Pagination
    @login_required
    def get(self, course_id):
        course = Courses.exists_or_404(course_id)
        # only users that can edit the course can view enrolment
        require(EDIT, course)
        restrict_users = not allow(READ, CoursesAndUsers(courses_id=course_id))

        # expire current_user from the session. When loading classlist from database, if the
        # user is already in the session, e.g. instructor for the course, the User.coursesandusers
        # is not loaded from the query below, but from session. In this case, if user has more
        # than one course, User.coursesandusers will return multiple row. Thus violating the
        # course_role constrain.
        db.session.expire(current_user)

        class_list = Users.query. \
            join(CoursesAndUsers). \
            join(UserTypesForCourse, and_(
                CoursesAndUsers.usertypesforcourse_id == UserTypesForCourse.id,
                UserTypesForCourse.name.notlike(UserTypesForCourse.TYPE_DROPPED))). \
            options(joinedload('usertypeforsystem')). \
            options(contains_eager('coursesandusers').contains_eager('usertypeforcourse')). \
            filter(CoursesAndUsers.courses_id == course_id). \
            order_by(Users.firstname).all()

        on_classlist_get.send(
            self,
            event_name=on_classlist_get.name,
            user=current_user,
            course_id=course_id)

        return {'objects': marshal(class_list, dataformat.get_users_in_course(restrict_users=restrict_users))}

    @login_required
    def post(self, course_id):
        Courses.query.get_or_404(course_id)
        coursesandusers = CoursesAndUsers(courses_id=course_id)
        require(EDIT, coursesandusers)
        uploaded_file = request.files['file']
        results = {'success': 0, 'invalids': []}
        if uploaded_file and allowed_file(uploaded_file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
            unique = str(uuid.uuid4())
            filename = unique + secure_filename(uploaded_file.filename)
            tmp_name = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(tmp_name)
            current_app.logger.debug("Importing for course " + str(course_id) + " with " + filename)
            with open(tmp_name, 'rU') as csvfile:
                spamreader = csv.reader(csvfile)
                users = []
                for row in spamreader:
                    if row:
                        users.append(row)
                if len(users) > 0:
                    results = import_users(course_id, users)
                on_classlist_upload.send(
                    self,
                    event_name=on_classlist_upload.name,
                    user=current_user,
                    course_id=course_id)
            os.remove(tmp_name)
            current_app.logger.debug("Class Import for course " + str(course_id) + " is successful. Removed file.")
            return results
        else:
            return {'error': 'Wrong file type'}, 400


api.add_resource(ClasslistRootAPI, '')


# /:userId/enrol
class EnrolAPI(Resource):
    @login_required
    def post(self, course_id, user_id):
        """
        Enrol or update a user enrolment in the course

        The payload for the request has to contain either course_role_id or course_role. e.g.
        {"course_role_id":3} or {"couse_role":"Student"}

        :param course_id:
        :param user_id:
        :return:
        """
        course = Courses.query.get_or_404(course_id)
        user = Users.query.get_or_404(user_id)
        coursesandusers = CoursesAndUsers.query.filter_by(users_id=user.id, courses_id=course.id).first()
        if not coursesandusers:
            coursesandusers = CoursesAndUsers(courses_id=course.id)
        require(EDIT, coursesandusers)

        params = new_course_user_parser.parse_args()
        role_id = params.get('course_role_id')
        role_name = params.get('course_role')

        if role_id:
            user_type = UserTypesForCourse.query.get_or_404(role_id)
        else:
            user_type = UserTypesForCourse.query.filter_by(name=role_name).one()

        if not user_type:
            abort(404)

        if coursesandusers.usertypesforcourse_id != user_type.id:
            coursesandusers.users_id = user.id
            coursesandusers.usertypesforcourse_id = user_type.id
            db.session.add(coursesandusers)
            db.session.commit()

        result = {
            'user_id': user.id,
            'fullname': user.fullname,
            'course_role': user_type.name
        }

        on_classlist_enrol.send(
            self,
            event_name=on_classlist_enrol.name,
            user=current_user,
            course_id=course_id,
            data={'user_id': user_id})

        return result

    @login_required
    def delete(self, course_id, user_id):
        course = Courses.query.get_or_404(course_id)
        user = Users.query.get_or_404(user_id)
        coursesandusers = CoursesAndUsers.query.filter_by(users_id=user.id, courses_id=course.id).first_or_404()
        require(EDIT, coursesandusers)
        drop = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first()
        coursesandusers.usertypesforcourse_id = drop.id
        result = {
            'user': {'id': user.id, 'fullname': user.fullname},
            'usertypesforcourse': {'id': drop.id, 'name': drop.name}}
        db.session.add(coursesandusers)

        on_classlist_unenrol.send(
            self,
            event_name=on_classlist_unenrol.name,
            user=current_user,
            course_id=course_id,
            data={'user_id': user_id})

        db.session.commit()
        return result


api.add_resource(EnrolAPI, '/<int:user_id>')


# /instructors/labels - return list of TAs and Instructors labels
class TeachersAPI(Resource):
    @login_required
    def get(self, course_id):
        course = Courses.query.get_or_404(course_id)
        require(READ, course)
        instructors = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter(
            UserTypesForCourse.name.in_([UserTypesForCourse.TYPE_TA, UserTypesForCourse.TYPE_INSTRUCTOR])).all()
        instructor_ids = {u.users_id: u.usertypeforcourse.name for u in instructors}

        on_classlist_instructor_label.send(
            self,
            event_name=on_classlist_instructor_label.name,
            user=current_user,
            course_id=course_id)

        return {'instructors': instructor_ids}


api.add_resource(TeachersAPI, '/instructors/labels')


# /students - return list of Students in the course
class StudentsAPI(Resource):
    @login_required
    def get(self, course_id):
        course = Courses.query.get_or_404(course_id)
        require(READ, course)
        students = Users.query. \
            options(joinedload(Users.groups).joinedload(GroupsAndUsers.group)). \
            join(CoursesAndUsers).filter_by(courses_id=course_id). \
            join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_STUDENT). \
            all()

        coursesandusers = CoursesAndUsers(courses_id=course_id)
        if allow(READ, coursesandusers):
            users = [
                {'user': {
                    'id': u.id,
                    'name': u.fullname if u.fullname else u.displayname,
                    'groups': [g.group.name for g in u.groups]
                }}
                for u in students]
        else:
            users = []
            for u in students:
                name = u.displayname
                if u.id == current_user.id:
                    name += ' (You)'
                users.append({'user': {'id': u.id, 'name': name}})

        on_classlist_student.send(
            self,
            event_name=on_classlist_student.name,
            user=current_user,
            course_id=course_id
        )

        return {'students': users}


api.add_resource(StudentsAPI, '/students')
