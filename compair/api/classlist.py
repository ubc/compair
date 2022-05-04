import os
import uuid
import unicodecsv as csv

from bouncer.constants import EDIT, READ, MANAGE
from flask import Blueprint, request, current_app, make_response
from flask_bouncer import can
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from six import BytesIO
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from flask_restful.reqparse import RequestParser

from . import dataformat
from compair.core import db, event, abort, allowed_file, display_name_generator
from compair.authorization import require, USER_IDENTITY
from compair.models import UserCourse, Course, User, SystemRole, CourseRole, \
    ThirdPartyType, ThirdPartyUser, Group
from compair.tasks import set_passwords
from .util import new_restful_api

classlist_api = Blueprint('classlist_api', __name__)
api = new_restful_api(classlist_api)

new_course_user_parser = RequestParser()
new_course_user_parser.add_argument('course_role')

update_users_course_role_parser = RequestParser()
update_users_course_role_parser.add_argument('ids', type=list, required=True, nullable=False, default=[], location='json')
update_users_course_role_parser.add_argument('course_role', default=CourseRole.dropped.value)


import_classlist_parser = RequestParser()
import_classlist_parser.add_argument('import_type', default=None, required=False)

# upload file column name to index number
COMPAIR_IMPORT = {
    'username': 0,
    'password': 1,
    'student_number': 2,
    'firstname': 3,
    'lastname': 4,
    'email': 5,
    'displayname': 6,
    'group_name': 7
}

CAS_OR_SAML_IMPORT = {
    'username': 0,
    'student_number': 1,
    'firstname': 2,
    'lastname': 3,
    'email': 4,
    'displayname': 5,
    'group_name': 6
}

# events
on_classlist_get = event.signal('CLASSLIST_GET')
on_classlist_upload = event.signal('CLASSLIST_UPLOAD')
on_classlist_enrol = event.signal('CLASSLIST_ENROL')
on_classlist_unenrol = event.signal('CLASSLIST_UNENROL')
on_classlist_instructor = event.signal('CLASSLIST_INSTRUCTOR_GET')
on_classlist_student = event.signal('CLASSLIST_STUDENT_GET')
on_classlist_update_users_course_roles = event.signal('CLASSLIST_UPDATE_USERS_COURSE_ROLES')


def _parse_user_row(import_type, row):
    length = len(row)

    columns = COMPAIR_IMPORT
    if import_type == ThirdPartyType.cas.value or import_type == ThirdPartyType.saml.value:
        columns = CAS_OR_SAML_IMPORT

    # get common columns
    user = {
        'username': row[columns['username']] if length > columns['username'] and row[columns['username']] else None,
        'student_number': row[columns['student_number']] if length > columns['student_number'] and row[columns['student_number']] else None,
        'firstname': row[columns['firstname']] if length > columns['firstname'] and row[columns['firstname']] else None,
        'lastname': row[columns['lastname']] if length > columns['lastname'] and row[columns['lastname']] else None,
        'email': row[columns['email']] if length > columns['email'] and row[columns['email']] else None,
        'displayname': row[columns['displayname']] if length > columns['displayname'] and row[columns['displayname']] else None,
        'group': row[columns['group_name']] if length > columns['group_name'] and row[columns['group_name']] else None
    }

    # get import specific columns
    if import_type == None:
        user['password'] = row[columns['password']] if length > columns['password'] and row[columns['password']] else None

    return user


def _get_existing_users_by_identifier(import_type, users):
    username_index = COMPAIR_IMPORT['username']
    if import_type == ThirdPartyType.cas.value or import_type == ThirdPartyType.saml.value:
        username_index = CAS_OR_SAML_IMPORT['username']
    usernames = [u[username_index] for u in users if len(u) > username_index]
    if len(usernames) == 0:
        return {}

    if import_type == ThirdPartyType.cas.value or import_type == ThirdPartyType.saml.value:
        # CAS/SAML login
        third_party_users = ThirdPartyUser.query \
            .options(joinedload('user')) \
            .filter(and_(
                ThirdPartyUser.unique_identifier.in_(usernames),
                ThirdPartyUser.third_party_type == ThirdPartyType(import_type)
            )) \
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

def _get_existing_users_by_student_number(import_type, users):
    student_number_index = COMPAIR_IMPORT['student_number']
    if import_type == ThirdPartyType.cas.value or import_type == ThirdPartyType.saml.value:
        student_number_index = CAS_OR_SAML_IMPORT['student_number']
    student_number = [u[student_number_index] for u in users if len(u) > student_number_index]
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
    import_usernames = []
    import_student_numbers = []

    # store unique user identifiers - eg. student number - throws error if duplicate in file
    existing_system_usernames = _get_existing_users_by_identifier(import_type, users)
    existing_system_student_numbers = _get_existing_users_by_student_number(import_type, users)

    groups = course.groups.all()
    groups_by_name = {}
    for group in groups:
        groups_by_name[group.name] = group

    # create / update users in file
    for user_row in users:
        if len(user_row) < 1:
            continue  # skip empty row
        user = _parse_user_row(import_type, user_row)

        # validate unique identifier
        username = user.get('username')
        password = user.get('password') #always None for CAS/SAML import, can be None for existing users on ComPAIR import
        student_number = user.get('student_number')

        u = existing_system_usernames.get(username, None)

        if not username:
            invalids.append({'user': User(username=username), 'message': 'The username is required.'})
            continue
        elif username in import_usernames:
            invalids.append({'user': User(username=username), 'message': 'This username already exists in the file.'})
            continue

        if u:
            # overwrite password if user has not logged in yet
            if u.last_online == None and not password in [None, '*']:
                set_user_passwords.append((u, password))
        else:
            u = User(
                username=None,
                password=None,
                student_number=user.get('student_number'),
                firstname=user.get('firstname'),
                lastname=user.get('lastname'),
                email=user.get('email')
            )
            if import_type == ThirdPartyType.cas.value or import_type == ThirdPartyType.saml.value:
                # CAS/SAML login
                u.third_party_auths.append(ThirdPartyUser(
                    unique_identifier=username,
                    third_party_type=ThirdPartyType(import_type)
                ))
            else:
                # ComPAIR login
                u.username = username
                if password in [None, '*']:
                    invalids.append({'user': u, 'message': 'The password is required.'})
                    continue
                elif len(password) < 4:
                    invalids.append({'user': u, 'message': 'The password must be at least 4 characters long.'})
                    continue
                else:
                    set_user_passwords.append((u, password))

            # validate student number (if not None)
            if student_number:
                # invalid if already showed up in file
                if student_number in import_student_numbers:
                    u.username = username
                    invalids.append({'user': u, 'message': 'This student number already exists in the file.'})
                    continue
                # invalid if student number already exists in the system
                elif student_number in existing_system_student_numbers:
                    u.username = username
                    invalids.append({'user': u, 'message': 'This student number already exists in the system.'})
                    continue

            u.system_role = SystemRole.student
            u.displayname = user.get('displayname') if user.get('displayname') else display_name_generator()
            db.session.add(u)

        import_usernames.append(username)
        if student_number:
            import_student_numbers.append(student_number)
        imported_users.append( (u, user.get('group')) )
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
    for user, group_name in imported_users:
        enrol = enroled.get(user.id, UserCourse(course_id=course.id, user_id=user.id))
        enrol.group = None
        if group_name:
            group = groups_by_name.get(group_name)
            # add new groups if needed
            if not group:
                group = Group(
                    course=course,
                    name=group_name
                )
                groups_by_name[group_name] = group
                db.session.add(group)
            enrol.group = group

        # do not overwrite instructor or teaching assistant roles
        if enrol.course_role not in [CourseRole.instructor, CourseRole.teaching_assistant]:
            enrol.course_role = CourseRole.student
            if user.id in students:
                del students[user.id]
            count += 1
        db.session.add(enrol)

    db.session.commit()

    # unenrol users not in file anymore
    for user_id in students:
        enrolment = students.get(user_id)
        # skip users that are already dropped
        if enrolment.course_role == CourseRole.dropped:
            continue
        enrolment.course_role = CourseRole.dropped
        enrolment.group_id = None
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
    fieldnames = ['username', 'student_number', 'firstname', 'lastname', 'displayname', 'group_name']

    if can(MANAGE, User) or current_app.config.get('EXPOSE_EMAIL_TO_INSTRUCTOR', False):
        fieldnames.insert(4, 'email')

    if can(MANAGE, User) or current_app.config.get('EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR', False):
        if current_app.config.get('CAS_LOGIN_ENABLED'):
            fieldnames.insert(1, 'cas_username')
        if current_app.config.get('SAML_LOGIN_ENABLED'):
            fieldnames.insert(1, 'saml_username')

    csv_buffer = BytesIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    if 'objects' in data:
        writer.writerows(data['objects'])

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
        require(READ, UserCourse(course_id=course.id),
            title="Class List Unavailable",
            message="Sorry, your role in this course does not allow you to view the class list.")
        restrict_user = not can(READ, USER_IDENTITY)

        # expire current_user from the session. When loading classlist from database, if the
        # user is already in the session, e.g. instructor for the course, the User.user_courses
        # is not loaded from the query below, but from session. In this case, if user has more
        # than one course, User.user_courses will return multiple row. Thus violating the
        # course_role constrain.
        db.session.expire(current_user)

        users = User.query \
            .with_entities(User, UserCourse) \
            .options(joinedload(UserCourse.group)) \
            .join(UserCourse, and_(
                UserCourse.user_id == User.id,
                UserCourse.course_id == course.id
            )) \
            .filter(
                UserCourse.course_role != CourseRole.dropped
            ) \
            .order_by(User.lastname, User.firstname) \
            .all()

        if not restrict_user:
            user_ids = [_user.id for (_user, _user_course) in users]
            third_party_auths = ThirdPartyUser.query \
                .filter(and_(
                    ThirdPartyUser.user_id.in_(user_ids),
                    or_(
                        ThirdPartyUser.third_party_type == ThirdPartyType.cas,
                        ThirdPartyUser.third_party_type == ThirdPartyType.saml,
                    )
                )) \
                .all()

        class_list = []
        for (_user, _user_course) in users:
            _user.course_role = _user_course.course_role
            _user.group = _user_course.group
            _user.group_uuid = _user.group.uuid if _user.group else None
            _user.group_name = _user.group.name if _user.group else None

            if not restrict_user:
                cas_auth = next(
                    (auth for auth in third_party_auths if auth.user_id == _user.id and auth.third_party_type == ThirdPartyType.cas),
                    None
                )
                _user.cas_username = cas_auth.unique_identifier if cas_auth else None
                saml_auth = next(
                    (auth for auth in third_party_auths if auth.user_id == _user.id and auth.third_party_type == ThirdPartyType.saml),
                    None
                )
                _user.saml_username = saml_auth.unique_identifier if saml_auth else None

            class_list.append(_user)

        on_classlist_get.send(
            self,
            event_name=on_classlist_get.name,
            user=current_user,
            course_id=course.id)

        if can(MANAGE, User):
            return {'objects': marshal(class_list, dataformat.get_full_users_in_course())}
        else:
            return {'objects': marshal(class_list, dataformat.get_users_in_course(restrict_user=restrict_user))}

    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        user_course = UserCourse(course_id=course.id)
        require(EDIT, user_course,
            title="Class List Not Imported",
            message="Sorry, your role in this course does not allow you to import or otherwise change the class list.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if course.id == DemoDataFixture.DEFAULT_COURSE_ID:
                abort(400, title="Class List Not Imported", message="Sorry, you cannot import users for the default demo course.")

        params = import_classlist_parser.parse_args()
        import_type = params.get('import_type')

        if import_type not in [ThirdPartyType.cas.value, ThirdPartyType.saml.value, None]:
            abort(400, title="Class List Not Imported", message="Please select a way for students to log in and try importing again.")
        elif import_type == ThirdPartyType.cas.value and not current_app.config.get('CAS_LOGIN_ENABLED'):
            abort(400, title="Class List Not Imported", message="Please select another way for students to log in and try importing again. Students are not able to use CWL logins based on the current settings.")
        elif import_type == ThirdPartyType.saml.value and not current_app.config.get('SAML_LOGIN_ENABLED'):
            abort(400, title="Class List Not Imported", message="Please select another way for students to log in and try importing again. Students are not able to use CWL logins based on the current settings.")
        elif import_type is None and not current_app.config.get('APP_LOGIN_ENABLED'):
            abort(400, title="Class List Not Imported", message="Please select another way for students to log in and try importing again. Students are not able to use the ComPAIR logins based on the current settings.")

        uploaded_file = request.files['file']
        results = {'success': 0, 'invalids': []}

        if not uploaded_file:
            abort(400, title="Class List Not Imported", message="No file was found to upload. Please try uploading again.")
        elif not allowed_file(uploaded_file.filename, current_app.config['UPLOAD_ALLOWED_EXTENSIONS']):
            abort(400, title="Class List Not Imported", message="Sorry, only CSV files can be imported. Please try again with a CSV file.")

        unique = str(uuid.uuid4())
        filename = unique + secure_filename(uploaded_file.filename)
        tmp_name = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(tmp_name)
        current_app.logger.debug("Importing for course " + str(course.id) + " with " + filename)
        with open(tmp_name, 'rb') as csvfile:
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

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if course.id == DemoDataFixture.DEFAULT_COURSE_ID and user.id in DemoDataFixture.DEFAULT_COURSE_USERS:
                abort(400, title="Enrollment Not Updated", message="Sorry, you cannot update course role for the default users in the default demo course.")

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

        require(EDIT, user_course,
            title="Enrollment Not Updated",
            message="Sorry, your role in this course does not allow you to update enrollment.")

        params = new_course_user_parser.parse_args()
        role_name = params.get('course_role')

        course_roles = [
            CourseRole.dropped.value,
            CourseRole.student.value,
            CourseRole.teaching_assistant.value,
            CourseRole.instructor.value
        ]
        if role_name not in course_roles:
            abort(400, title="Enrollment Not Updated", message="Please try again with a course role from the list of roles provided.")
        course_role = CourseRole(role_name)
        if user_course.course_role != course_role:
            user_course.course_role = course_role
            db.session.add(user_course)
            db.session.commit()

        on_classlist_enrol.send(
            self,
            event_name=on_classlist_enrol.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        return {
            'user_id': user.uuid,
            'fullname': user.fullname,
            'fullname_sortable': user.fullname_sortable,
            'course_role': course_role.value
        }

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
        require(EDIT, user_course,
            title="Enrollment Not Updated",
            message="Sorry, your role in this course does not allow you to update enrollment.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if course.id == DemoDataFixture.DEFAULT_COURSE_ID and user.id in DemoDataFixture.DEFAULT_COURSE_USERS:
                abort(400, title="Enrollment Not Updated", message="Sorry, you cannot update course role for the default users in the default demo course.")

        user_course.course_role = CourseRole.dropped
        db.session.add(user_course)

        on_classlist_unenrol.send(
            self,
            event_name=on_classlist_unenrol.name,
            user=current_user,
            course_id=course.id,
            data={'user_id': user.id})

        db.session.commit()

        return {
            'user_id': user.uuid,
            'fullname': user.fullname,
            'fullname_sortable': user.fullname_sortable,
            'course_role': CourseRole.dropped.value
        }



api.add_resource(EnrolAPI, '/<user_uuid>')

# /students - return list of Students in the course
class StudentsAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course,
            title="Students Unavailable",
            message="Students can only be seen here by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, course)

        students = User.query \
            .with_entities(User, UserCourse) \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                UserCourse.course_id == course.id,
                UserCourse.course_role == CourseRole.student
            ) \
            .order_by(User.lastname, User.firstname) \
            .all()

        users = []
        user_course = UserCourse(course_id=course.id)
        for u in students:
            if can(READ, user_course):
                users.append({
                    'id': u.User.uuid,
                    'name': u.User.fullname_sortable,
                    'group_id': u.UserCourse.group_id,
                    'role': u.UserCourse.course_role.value
                })
            else:
                name = u.User.displayname
                if u.User.id == current_user.id:
                    name += ' (You)'
                users.append({
                    'id': u.User.uuid,
                    'name': name,
                    'group_id': u.UserCourse.group_id,
                    'role': u.UserCourse.course_role.value
                })

        on_classlist_student.send(
            self,
            event_name=on_classlist_student.name,
            user=current_user,
            course_id=course.id
        )

        return { 'objects': users }


api.add_resource(StudentsAPI, '/students')

# /instructors - return list of Instructors and TAs of the course
class InstructorsAPI(Resource):
    @login_required
    def get(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(READ, course,
            title="Instructors Unavailable",
            message="Instructors can only be seen here by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, course)

        instructors = User.query \
            .with_entities(User, UserCourse) \
            .join(UserCourse, UserCourse.user_id == User.id) \
            .filter(
                UserCourse.course_id == course.id,
                or_(
                    UserCourse.course_role == CourseRole.instructor,
                    UserCourse.course_role == CourseRole.teaching_assistant
                )
            ) \
            .order_by(User.lastname, User.firstname) \
            .all()

        users = []
        user_course = UserCourse(course_id=course.id)
        for u in instructors:
            if can(READ, user_course):
                users.append({
                    'id': u.User.uuid,
                    'name': u.User.fullname_sortable,
                    'group_id': u.UserCourse.group_id,
                    'role': u.UserCourse.course_role.value
                })
            else:
                users.append({
                    'id': u.User.uuid,
                    'name': u.User.displayname,
                    'group_id': u.UserCourse.group_id,
                    'role': u.UserCourse.course_role.value
                })

        on_classlist_instructor.send(
            self,
            event_name=on_classlist_instructor.name,
            user=current_user,
            course_id=course.id
        )

        return { 'objects': users }


api.add_resource(InstructorsAPI, '/instructors')

# /roles - set course role for multi users at once
class UserCourseRoleAPI(Resource):
    @login_required
    def post(self, course_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, UserCourse(course_id=course.id),
            title="Enrollment Not Updated",
            message="Sorry, your role in this course does not allow you to update enrollment.")

        params = update_users_course_role_parser.parse_args()

        role_name = params.get('course_role')
        course_roles = [
            CourseRole.dropped.value,
            CourseRole.student.value,
            CourseRole.teaching_assistant.value,
            CourseRole.instructor.value
        ]
        if role_name not in course_roles:
            abort(400, title="Enrollment Not Updated", message="Please try again with a course role from the list of roles provided.")
        course_role = CourseRole(role_name)

        if len(params.get('ids')) == 0:
            abort(400, title="Enrollment Not Updated", message="Please select at least one user below and then try to update the enrollment again.")

        user_courses = UserCourse.query \
            .join(User, UserCourse.user_id == User.id) \
            .filter(and_(
                UserCourse.course_id == course.id,
                User.uuid.in_(params.get('ids')),
                UserCourse.course_role != CourseRole.dropped
            )) \
            .all()

        if len(params.get('ids')) != len(user_courses):
            abort(400, title="Enrollment Not Updated", message="One or more users selected are not enrolled in the course yet.")

        if len(user_courses) == 1 and user_courses[0].user_id == current_user.id:
            if course_role == CourseRole.dropped:
                abort(400, title="Enrollment Not Updated",
                    message="Sorry, you cannot drop yourself from the course. Please select only other users and try again.")
            else:
                abort(400, title="Enrollment Not Updated",
                    message="Sorry, you cannot change your own course role. Please select only other users and try again.")

        for user_course in user_courses:
            if current_app.config.get('DEMO_INSTALLATION', False):
                from data.fixtures import DemoDataFixture
                if course.id == DemoDataFixture.DEFAULT_COURSE_ID and user.id in DemoDataFixture.DEFAULT_COURSE_USERS:
                    abort(400, title="Enrollment Not Updated", message="Sorry, you cannot update course role for the default users in the default demo course.")

            # skip current user
            if user_course.user_id == current_user.id:
                continue
            # update user's role
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
