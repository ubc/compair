import os
import uuid
import csv
import string

from bouncer.constants import EDIT, READ, MANAGE
from flask import Blueprint, request, current_app, make_response
from flask_login import login_required, current_user
from flask_restful import Resource, marshal, abort
from six import StringIO
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from flask_restful.reqparse import RequestParser

from . import dataformat
from acj.core import db, event
from acj.authorization import allow, require, USER_IDENTITY
from acj.models import UserCourse, Course, User, SystemRole, CourseRole, \
    ThirdPartyType, ThirdPartyUser
from acj.tasks.user_password import set_passwords
from .util import new_restful_api
from .file import random_generator, allowed_file

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

new_course_user_parser = RequestParser()
new_course_user_parser.add_argument('course_role', type=str)

update_users_course_role_parser = RequestParser()
update_users_course_role_parser.add_argument('ids', type=list, required=True, default=[], location='json')
update_users_course_role_parser.add_argument('course_role', default=CourseRole.dropped.value, type=str)


import_classlist_parser = RequestParser()
import_classlist_parser.add_argument('import_type', default=None, type=str, required=False)

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
on_classlist_update_users_course_roles = event.signal('CLASSLIST_UPDATE_USERS_COURSE_ROLES')


def display_name_generator(role="student"):
    return "".join([role, '_', random_generator(8, string.digits)])

def _get_existing_users_by_identifier(import_type, users):
    usernames = [u[USERNAME] for u in users if len(u) > USERNAME]
    if len(usernames) == 0:
        return {}

    if import_type == ThirdPartyType.cwl.value:
        # CWL login
        third_party_users = ThirdPartyUser.query \
            .options(joinedload('user')) \
            .filter(ThirdPartyUser.unique_identifier.in_(usernames)) \
            .all()
        return {
            third_party_user.unique_identifier: third_party_user.user for third_party_user in third_party_users
        }
    else:
        # ComPAIR login
        users = User.query \
            .filter(User.username.in_(usernames)) \
            .all()
        return {
            u.username: u for u in users
        }

def _get_existing_users_by_student_number(users):
    student_number = [u[STUDENTNO] for u in users if len(u) > STUDENTNO]
    if len(student_number) == 0:
        return {}

    users = User.query \
        .filter(User.student_number.in_(student_number)) \
        .all()
    return {
        u.student_number: u for u in users
    }

def import_users(import_type, course, users):
    invalids = []  # invalid entries - eg. invalid # of columns
    count = 0  # store number of successful enrolments

    imported_users = []
    set_user_passwords = []

    # store unique user identifiers - eg. student number - throws error if duplicate in file
    import_unique_identifiers = []
    import_student_numbers = []

    # store unique user identifiers - eg. student number - throws error if duplicate in file
    existing_system_unique_identifiers = _get_existing_users_by_identifier(import_type, users)
    existing_system_student_numbers = _get_existing_users_by_student_number(users)

    # constants
    letters_digits = string.ascii_letters + string.digits

    # create / update users in file
    for user in users:
        length = len(user)
        if length < 1:
            continue  # skip empty row

        # validate unique identifier
        unique_identifier = user[USERNAME].lower() if length > USERNAME and user[USERNAME] else None

        if not unique_identifier:
            invalids.append({'user': User(username=unique_identifier), 'message': 'The username is required.'})
            continue
        elif unique_identifier in import_unique_identifiers:
            invalids.append({'user': User(username=unique_identifier), 'message': 'This username already exists in the file.'})
            continue

        u = existing_system_unique_identifiers.get(unique_identifier, None)
        if not u:
            u = User()
            if import_type == ThirdPartyType.cwl.value:
                # CWL login
                third_party_user = ThirdPartyUser(
                    unique_identifier=unique_identifier,
                    third_party_type=ThirdPartyType.cwl
                )
                u.username = None
                u.third_party_auths.append(third_party_user)
            else:
                # ComPAIR login
                u.username = unique_identifier
        else:
            # user exists in the system, skip user creation
            import_unique_identifiers.append(unique_identifier)
            import_student_numbers.append(u.student_number)
            imported_users.append(u)
            continue

        u.student_number = user[STUDENTNO] if length > STUDENTNO and user[STUDENTNO] else None
        u.firstname = user[FIRSTNAME] if length > FIRSTNAME and user[FIRSTNAME] else None
        u.lastname = user[LASTNAME] if length > LASTNAME and user[LASTNAME] else None
        u.email = user[EMAIL] if length > EMAIL and user[EMAIL] else None
        u.password = None

        # ComPAIR login only
        if import_type == None:
            password = user[PASSWORD] if length > PASSWORD and user[PASSWORD] else None
            if password:
                set_user_passwords.append((u, password))

        # validate student number (if not None)
        if u.student_number:
            # invalid if already showed up in file
            if u.student_number in import_student_numbers:
                u.username = unique_identifier
                invalids.append({'user': u, 'message': 'This student number already exists in the file.'})
                continue
            # invalid if student number already exists in the system
            elif u.student_number in existing_system_student_numbers:
                u.username = unique_identifier
                invalids.append({'user': u, 'message': 'This student number already exists in the system.'})
                continue

        u.system_role = SystemRole.student
        displayname = user[DISPLAYNAME] if length > DISPLAYNAME and user[DISPLAYNAME] else None
        u.displayname = displayname if displayname else display_name_generator()

        import_unique_identifiers.append(unique_identifier)
        import_student_numbers.append(u.student_number)
        db.session.add(u)
        imported_users.append(u)
    db.session.commit()

    enroled = UserCourse.query \
        .filter_by(course_id=course.id) \
        .all()

    enroled = {e.user_id: e for e in enroled}

    students = UserCourse.query \
        .filter_by(
            course_id=course.id,
            course_role=CourseRole.student
        ) \
        .all()
    students = {s.user_id: s for s in students}

    # enrol valid users in file
    for user in imported_users:
        enrol = enroled.get(user.id, UserCourse(course_id=course.id, user_id=user.id))
        # do not overwrite instructor or teaching assistant roles
        if enrol.course_role not in [CourseRole.instructor, CourseRole.teaching_assistant]:
            enrol.course_role = CourseRole.student
            db.session.add(enrol)
            if user.id in students:
                del students[user.id]
            count += 1
    db.session.commit()

    # unenrol users not in file anymore
    for user_id in students:
        enrolment = students.get(user_id)
        # skip users that are already dropped
        if enrolment.course_role == CourseRole.dropped:
            continue
        enrolment.course_role = CourseRole.dropped
        db.session.add(enrolment)
    db.session.commit()

    # wait until user ids are generated before starting background jobs
    # perform password update in chunks of 100
    chunk_size = 100
    chunks = [set_user_passwords[index:index + chunk_size] for index in range(0, len(set_user_passwords), chunk_size)]
    for chunk in chunks:
        set_passwords.delay({
            user.id: password for (user, password) in chunk
        })

    on_classlist_upload.send(
        current_app._get_current_object(),
        event_name=on_classlist_upload.name,
        user=current_user,
        course_id=course.id
    )

    return {
        'success': count,
        'invalids': marshal(invalids, dataformat.get_import_users_results(False))
    }


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    fieldnames = ['username', 'student_number', 'firstname', 'lastname', 'email', 'displayname']
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    if 'objects' in data:
        writer.writerows(data['objects'])
    elif 'invalids' in data:
        writer.writerows(data['invalids'])

    response = make_response(csv_buffer.getvalue(), code)
    response.headers.extend(headers or {})
    response.headers['Content-Disposition'] = 'attachment;filename=classlist.csv'
    return response

# /
class ClasslistRootAPI(Resource):
    # TODO Pagination
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, UserCourse(course_id=course.id))
        restrict_user = not allow(READ, USER_IDENTITY)

        # expire current_user from the session. When loading classlist from database, if the
        # user is already in the session, e.g. instructor for the course, the User.user_courses
        # is not loaded from the query below, but from session. In this case, if user has more
        # than one course, User.user_courses will return multiple row. Thus violating the
        # course_role constrain.
        db.session.expire(current_user)

        class_list = User.query \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .add_columns(UserCourse.course_role, UserCourse.group_name) \
            .filter(and_(
                UserCourse.course_id == course.id,
                UserCourse.course_role != CourseRole.dropped
            )) \
            .order_by(User.firstname) \
            .all()

        for (_user, _course_role, _group_name) in class_list:
            _user.course_role = _course_role
            _user.group_name = _group_name

        class_list = [_user for (_user, _course_role, _group_name) in class_list]

        on_classlist_get.send(
            self,
            event_name=on_classlist_get.name,
            user=current_user,
            course_id=course.id)

        return {'objects': marshal(class_list, dataformat.get_users_in_course(restrict_user=restrict_user))}

    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(EDIT, user_course)

        params = import_classlist_parser.parse_args()
        import_type = params.get('import_type')

        if import_type not in [ThirdPartyType.cwl.value, None]:
            return {'error': 'Invalid import type'}, 400
        elif import_type == ThirdPartyType.cwl.value and not current_app.config.get('CAS_LOGIN_ENABLED'):
            return {'error': 'Invalid import type: CWL auth not enabled'}, 400
        elif import_type is None and not current_app.config.get('APP_LOGIN_ENABLED'):
            return {'error': 'Invalid import type: App auth not enabled'}, 400

        uploaded_file = request.files['file']
        results = {'success': 0, 'invalids': []}
        if uploaded_file and allowed_file(uploaded_file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
            unique = str(uuid.uuid4())
            filename = unique + secure_filename(uploaded_file.filename)
            tmp_name = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(tmp_name)
            current_app.logger.debug("Importing for course " + str(course.id) + " with " + filename)
            with open(tmp_name, 'rt') as csvfile:
                spamreader = csv.reader(csvfile)
                users = []
                for row in spamreader:
                    if row:
                        users.append(row)

                if len(users) > 0:
                    results = import_users(import_type, course, users)

                on_classlist_upload.send(
                    self,
                    event_name=on_classlist_upload.name,
                    user=current_user,
                    course_id=course.id)
            os.remove(tmp_name)
            current_app.logger.debug("Class Import for course " + str(course.id) + " is successful. Removed file.")
            return results
        else:
            return {'error': 'Wrong file type'}, 400


api.add_resource(ClasslistRootAPI, '')


# /user_uuid
class EnrolAPI(Resource):
    @login_required
    def post(self, course_uuid, user_uuid):
        """
        Enrol or update a user enrolment in the course

        The payload for the request has to contain course_role. e.g.
        {"couse_role":"Student"}

        :param course_uuid:
        :param user_uuid:
        :return:
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user = User.get_by_uuid_or_404(user_uuid)

        user_course = UserCourse.query \
            .filter_by(
                user_id=user.id,
                course_id=course.id
            ) \
            .first()

        if not user_course:
            user_course = UserCourse(
                user_id=user.id,
                course_id=course.id
            )

        require(EDIT, user_course)

        params = new_course_user_parser.parse_args()
        role_name = params.get('course_role')

        course_roles = [
            CourseRole.dropped.value,
            CourseRole.student.value,
            CourseRole.teaching_assistant.value,
            CourseRole.instructor.value
        ]
        if role_name not in course_roles:
            abort(404)
        course_role = CourseRole(role_name)
        if user_course.course_role != course_role:
            user_course.course_role = course_role
            db.session.add(user_course)
            db.session.commit()

        result = {
            'user_id': user.uuid,
            'fullname': user.fullname,
            'course_role': course_role.value
        }

        on_classlist_enrol.send(
            self,
            event_name=on_classlist_enrol.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return result

    @login_required
    def delete(self, course_uuid, user_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user = User.get_by_uuid_or_404(user_uuid)
        user_course = UserCourse.query \
            .filter_by(
                user_id=user.id,
                course_id=course.id
            ) \
            .first_or_404()
        require(EDIT, user_course)

        user_course.course_role = CourseRole.dropped
        result = {
            'user_id': user.uuid,
            'fullname': user.fullname,
            'course_role': CourseRole.dropped.value
        }

        db.session.add(user_course)

        on_classlist_unenrol.send(
            self,
            event_name=on_classlist_unenrol.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        db.session.commit()
        return result


api.add_resource(EnrolAPI, '/<user_uuid>')


# /instructors/labels - return list of TAs and Instructors labels
class TeachersAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course)

        instructors = UserCourse.query \
            .filter(and_(
                UserCourse.course_id==course.id,
                UserCourse.course_role.in_([CourseRole.teaching_assistant, CourseRole.instructor])
            )) \
            .all()
        instructor_uuids = {u.user_uuid: u.course_role.value for u in instructors}

        on_classlist_instructor_label.send(
            self,
            event_name=on_classlist_instructor_label.name,
            user=current_user,
            course_id=course.id)

        return {'instructors': instructor_uuids}


api.add_resource(TeachersAPI, '/instructors/labels')


# /students - return list of Students in the course
class StudentsAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course)
        restrict_user = not allow(MANAGE, course)

        students = User.query \
            .with_entities(User, UserCourse.group_name) \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .all()

        users = []
        user_course = UserCourse(course_id=course.id)
        for u in students:
            if allow(READ, user_course):
                users.append({
                    'id': u.User.uuid,
                    'name': u.User.fullname if u.User.fullname else u.User.displayname,
                    'group_name': u.group_name
                })
            else:
                name = u.User.displayname
                if u.User.id == current_user.id:
                    name += ' (You)'
                users.append({
                    'id': u.User.uuid,
                    'name': name,
                    'group_name': u.group_name
                })

        on_classlist_student.send(
            self,
            event_name=on_classlist_student.name,
            user=current_user,
            course_id=course.id
        )

        return { 'objects': users }


api.add_resource(StudentsAPI, '/students')


# /roles - set course role for multi users at once
class UserCourseRoleAPI(Resource):
    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, UserCourse(course_id=course.id))

        params = update_users_course_role_parser.parse_args()

        role_name = params.get('course_role')
        course_roles = [
            CourseRole.dropped.value,
            CourseRole.student.value,
            CourseRole.teaching_assistant.value,
            CourseRole.instructor.value
        ]
        if role_name not in course_roles:
            abort(404)
        course_role = CourseRole(role_name)

        if len(params.get('ids')) == 0:
            return {"error": "Please select at least one user below"}, 400

        user_courses = UserCourse.query \
            .join(User, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                User.uuid.in_(params.get('ids')),
                UserCourse.course_role != CourseRole.dropped
            )) \
            .all()

        if len(params.get('ids')) != len(user_courses):
            return {"error": "One or more users are not enrolled in the course"}, 400

        if len(user_courses) == 1 and user_courses[0].user_id == current_user.id:
            if course_role == CourseRole.dropped:
                return {"error": "You cannot drop yourself from the course. Please select other users"}, 400
            else:
                return {"error": "You cannot change your own course role. Please select other users"}, 400

        for user_course in user_courses:
            # skip current user
            if user_course.user_id == current_user.id:
                continue
            # update user's role'
            user_course.course_role = course_role

        db.session.commit()

        on_classlist_update_users_course_roles.send(
            current_app._get_current_object(),
            event_name=on_classlist_update_users_course_roles.name,
            user=current_user,
            course_id=course.id,
            data={'user_uuids': params.get('ids'), 'course_role': role_name})

        return {'course_role': role_name}


api.add_resource(UserCourseRoleAPI, '/roles')