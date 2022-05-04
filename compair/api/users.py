import datetime
import dateutil.parser
import pytz

from flask import Blueprint, current_app, session as sess
from bouncer.constants import MANAGE, EDIT, CREATE, READ
from flask_bouncer import can
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from flask_login import login_required, current_user
from sqlalchemy.orm import load_only, joinedload
from sqlalchemy import exc, asc, or_, and_, func, desc, asc
from six import text_type

from . import dataformat
from compair.authorization import is_user_access_restricted, require, USER_IDENTITY
from compair.core import db, event, abort, impersonation
from .util import new_restful_api, get_model_changes, pagination_parser
from compair.models import User, SystemRole, Course, UserCourse, CourseRole, Assignment, \
    LTIConsumer, LTIUser, LTIUserResourceLink, LTIContext, ThirdPartyUser, ThirdPartyType, \
    Answer, Comparison, AnswerComment, AnswerCommentType, EmailNotificationMethod
from compair.api.login import authenticate
from distutils.util import strtobool

user_api = Blueprint('user_api', __name__)

def non_blank_text(value):
    if value is None:
        return None
    else:
        return None if text_type(value).strip() == "" else text_type(value)

def string_to_bool(value):
    if value is None:
        return None
    else:
        return strtobool(value)

new_user_parser = RequestParser()
new_user_parser.add_argument('username', type=non_blank_text, required=False)
new_user_parser.add_argument('student_number', type=non_blank_text)
new_user_parser.add_argument('system_role', default=None)
new_user_parser.add_argument('firstname', type=non_blank_text)
new_user_parser.add_argument('lastname', type=non_blank_text)
new_user_parser.add_argument('displayname', required=True, nullable=False)
new_user_parser.add_argument('email')
new_user_parser.add_argument('email_notification_method')
new_user_parser.add_argument('password', required=False)

existing_user_parser = RequestParser()
existing_user_parser.add_argument('id', required=True, nullable=False)
existing_user_parser.add_argument('username', type=non_blank_text, required=False)
existing_user_parser.add_argument('student_number', type=non_blank_text)
existing_user_parser.add_argument('system_role', default=None)
existing_user_parser.add_argument('firstname', type=non_blank_text)
existing_user_parser.add_argument('lastname', type=non_blank_text)
existing_user_parser.add_argument('displayname', required=True, nullable=False)
existing_user_parser.add_argument('email')
existing_user_parser.add_argument('email_notification_method')

update_notification_settings_parser = RequestParser()
update_notification_settings_parser.add_argument('email_notification_method', required=True, nullable=False)

update_password_parser = RequestParser()
update_password_parser.add_argument('oldpassword', required=False)
update_password_parser.add_argument('newpassword', required=True, nullable=False)

user_list_parser = pagination_parser.copy()
user_list_parser.add_argument('search', required=False, default=None)
user_list_parser.add_argument('orderBy', required=False, default=None)
user_list_parser.add_argument('reverse', type=bool, default=False)
user_list_parser.add_argument('ids', required=False, default=None)

user_course_list_parser = pagination_parser.copy()
user_course_list_parser.add_argument('search', required=False, default=None)
user_course_list_parser.add_argument('includeSandbox', type=string_to_bool, required=False, default=None)
user_course_list_parser.add_argument('period', type=non_blank_text, required=False, default=None)

user_id_course_list_parser = pagination_parser.copy()
user_id_course_list_parser.add_argument('search', required=False, default=None)
user_id_course_list_parser.add_argument('includeSandbox', type=string_to_bool, required=False, default=None)
user_id_course_list_parser.add_argument('period', type=non_blank_text, required=False, default=None)
user_id_course_list_parser.add_argument('orderBy', required=False, default=None)
user_id_course_list_parser.add_argument('reverse', type=bool, default=False)

user_course_status_list_parser = RequestParser()
user_course_status_list_parser.add_argument('ids', required=True, nullable=False, default=None)

# events
on_user_modified = event.signal('USER_MODIFIED')
on_user_get = event.signal('USER_GET')
on_user_list_get = event.signal('USER_LIST_GET')
on_user_create = event.signal('USER_CREATE')
on_user_course_get = event.signal('USER_COURSE_GET')
on_user_course_status_get = event.signal('USER_COURSE_STATUS_GET')
on_teaching_course_get = event.signal('USER_TEACHING_COURSE_GET')
on_user_edit_button_get = event.signal('USER_EDIT_BUTTON_GET')
on_user_notifications_update = event.signal('USER_NOTIFICATIONS_UPDATE')
on_user_password_update = event.signal('USER_PASSWORD_UPDATE')
on_user_lti_users_get = event.signal('USER_LTI_USERS_GET')
on_user_lti_user_unlink = event.signal('USER_LTI_USER_UNLINK')
on_user_third_party_users_get = event.signal('USER_THIRD_PARTY_USERS_GET')
on_user_third_party_user_delete = event.signal('USER_THIRD_PARTY_USER_DELETE')

def check_valid_system_role(system_role):
    system_roles = [
        SystemRole.sys_admin.value,
        SystemRole.instructor.value,
        SystemRole.student.value
    ]
    if system_role not in system_roles:
        abort(400, title="User Not Saved", message="Please try again with a system role from the list of roles provided.")


def check_valid_email_notification_method(email_notification_method):
    email_notification_methods = [
        EmailNotificationMethod.enable.value,
        EmailNotificationMethod.disable.value
    ]
    if email_notification_method not in email_notification_methods:
        abort(400, title="User Not Saved", message="Please try again with an email notification checked or unchecked.")

def marshal_user_data(user):
    if impersonation.is_impersonating() and current_user.id == user.id:
        # when retrieving the profile of the student being impersonated,
        # don't include full profile (i.e. no email)
        return marshal(user, dataformat.get_user(False))
    elif can(MANAGE, user) or current_user.id == user.id:
        return marshal(user, dataformat.get_full_user())
    else:
        return marshal(user, dataformat.get_user(is_user_access_restricted(user)))

# /user_uuid
class UserAPI(Resource):
    @login_required
    def get(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)

        on_user_get.send(
            self,
            event_name=on_user_get.name,
            user=current_user,
            data={'id': user.id}
        )
        return marshal_user_data(user)

    @login_required
    def post(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)

        if is_user_access_restricted(user):
            abort(403, title="User Not Saved", message="Sorry, your role does not allow you to save this user.")

        params = existing_user_parser.parse_args()

        # make sure the user id in the url and the id matches
        if params['id'] != user_uuid:
            abort(400, title="User Not Saved",
                message="The user's ID does not match the URL, which is required in order to save the user.")

        # only update username if user uses compair login method
        if user.uses_compair_login:
            username = params.get("username")
            if username == None:
                abort(400, title="User Not Saved", message="A username is required. Please enter a username and try saving again.")
            username_exists = User.query.filter_by(username=username).first()
            if username_exists and username_exists.id != user.id:
                abort(409, title="User Not Saved", message="Sorry, this username already exists and usernames must be unique in ComPAIR. Please enter another username and try saving again.")

            user.username = username
        elif can(MANAGE, user):
            #admins can optionally set username for users without a username
            username = params.get("username")
            if username:
                username_exists = User.query.filter_by(username=username).first()
                if username_exists and username_exists.id != user.id:
                    abort(409, title="User Not Saved", message="Sorry, this username already exists and usernames must be unique in ComPAIR. Please enter another username and try saving again.")
            user.username = username
        else:
            user.username = None

        if can(MANAGE, user):
            system_role = params.get("system_role", user.system_role.value)
            check_valid_system_role(system_role)
            user.system_role = SystemRole(system_role)

        if can(MANAGE, user) or user.id == current_user.id or current_app.config.get('EXPOSE_EMAIL_TO_INSTRUCTOR', False):
            if current_user.system_role != SystemRole.student or current_app.config.get('ALLOW_STUDENT_CHANGE_EMAIL'):
                user.email = params.get("email", user.email)

            email_notification_method = params.get("email_notification_method")
            check_valid_email_notification_method(email_notification_method)
            user.email_notification_method = EmailNotificationMethod(email_notification_method)

        elif params.get("email") or params.get("email_notification_method"):
            abort(400, title="User Not Saved", message="your role does not allow you to change email settings for this user.")

        if current_user.system_role != SystemRole.student or current_app.config.get('ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'):
            # only students should have student numbers
            if user.system_role == SystemRole.student:
                student_number = params.get("student_number", user.student_number)
                student_number_exists = User.query.filter_by(student_number=student_number).first()
                if student_number is not None and student_number_exists and student_number_exists.id != user.id:
                    abort(409, title="User Not Saved", message="Sorry, this student number already exists and student numbers must be unique in ComPAIR. Please enter another number and try saving again.")
                else:
                    user.student_number = student_number
            else:
                user.student_number = None

        if current_user.system_role != SystemRole.student or current_app.config.get('ALLOW_STUDENT_CHANGE_NAME'):
            user.firstname = params.get("firstname", user.firstname)
            user.lastname = params.get("lastname", user.lastname)

        if current_user.system_role != SystemRole.student or current_app.config.get('ALLOW_STUDENT_CHANGE_DISPLAY_NAME'):
            user.displayname = params.get("displayname", user.displayname)

        model_changes = get_model_changes(user)

        try:
            db.session.commit()
            on_user_modified.send(
                self,
                event_name=on_user_modified.name,
                user=current_user,
                data={'id': user.id, 'changes': model_changes})
        except exc.IntegrityError:
            db.session.rollback()
            abort(409, title="User Not Saved", message="Sorry, this ID already exists and IDs must be unique in ComPAIR. Please try addding another user.")

        return marshal_user_data(user)

# /
class UserListAPI(Resource):
    @login_required
    def get(self):
        require(READ, USER_IDENTITY,
            title="User List Unavailable",
            message="Sorry, your system role does not allow you to view the list of users.")

        params = user_list_parser.parse_args()

        query = User.query
        if params['search']:
            # match each word of search
            for word in params['search'].strip().split(' '):
                if word != '':
                    search = '%'+word+'%'
                    query = query.filter(or_(
                        User.firstname.like(search),
                        User.lastname.like(search),
                        User.displayname.like(search)
                    ))

        if params['orderBy']:
            if params['reverse']:
                query = query.order_by(desc(params['orderBy']))
            else:
                query = query.order_by(asc(params['orderBy']))
        query = query.order_by(User.lastname.asc(), User.firstname.asc())

        page = query.paginate(params['page'], params['perPage'])

        on_user_list_get.send(
            self,
            event_name=on_user_list_get.name,
            user=current_user)

        return {"objects": marshal(page.items, dataformat.get_user(False)), "page": page.page,
                "pages": page.pages, "total": page.total, "per_page": page.per_page}

    def post(self):
        # login_required when lti_create_user_link not set
        if not sess.get('lti_create_user_link') and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

        user = User()
        params = new_user_parser.parse_args()
        user.student_number = params.get("student_number", None)
        user.email = params.get("email")
        user.firstname = params.get("firstname")
        user.lastname = params.get("lastname")
        user.displayname = params.get("displayname")

        email_notification_method = params.get("email_notification_method")
        check_valid_email_notification_method(email_notification_method)
        user.email_notification_method = EmailNotificationMethod(email_notification_method)

        if not current_app.config.get('APP_LOGIN_ENABLED'):
            # if APP_LOGIN_ENABLED is not enabled, allow blank username and password
            user.username = None
            user.password = None
        else:
            # else enforce required password and unique username
            user.password = params.get("password")
            if user.password == None:
                abort(400, title="User Not Saved", message="A password is required. Please enter a password and try saving again.")
            elif len(params.get("password")) < 4:
                abort(400, title="User Not Saved", message="The password must be at least 4 characters long.")

            user.username = params.get("username")
            if user.username == None:
                abort(400, title="User Not Saved", message="A username is required. Please enter a username and try saving again.")

            username_exists = User.query.filter_by(username=user.username).first()
            if username_exists:
                abort(409, title="User Not Saved", message="Sorry, this username already exists and usernames must be unique in ComPAIR. Please enter another username and try saving again.")

        student_number_exists = User.query.filter_by(student_number=user.student_number).first()
        # if student_number is not left blank and it exists -> 409 error
        if user.student_number is not None and student_number_exists:
            abort(409, title="User Not Saved", message="Sorry, this student number already exists and student numbers must be unique in ComPAIR. Please enter another number and try saving again.")

        # handle lti_create_user_link setup for third party logins
        if sess.get('lti_create_user_link') and sess.get('LTI'):
            lti_user = LTIUser.query.get_or_404(sess['lti_user'])
            lti_user.compair_user = user
            user.system_role = lti_user.system_role
            lti_user.update_user_profile()

            if sess.get('lti_context') and sess.get('lti_user_resource_link'):
                lti_context = LTIContext.query.get_or_404(sess['lti_context'])
                lti_user_resource_link = LTIUserResourceLink.query.get_or_404(sess['lti_user_resource_link'])
                if lti_context.is_linked_to_course():
                    # create new enrollment
                    new_user_course = UserCourse(
                        user=user,
                        course_id=lti_context.compair_course_id,
                        course_role=lti_user_resource_link.course_role
                    )
                    db.session.add(new_user_course)
        else:
            system_role = params.get("system_role")
            check_valid_system_role(system_role)
            user.system_role = SystemRole(system_role)

            require(CREATE, user,
                title="User Not Saved",
                message="Sorry, your role does not allow you to save users.")

        # only students can have student numbers
        if user.system_role != SystemRole.student:
            user.student_number = None

        try:
            db.session.add(user)
            db.session.commit()
            if current_user.is_authenticated:
                on_user_create.send(
                    self,
                    event_name=on_user_create.name,
                    user=current_user,
                    data=marshal(user, dataformat.get_full_user()))
            else:
                on_user_create.send(
                    self,
                    event_name=on_user_create.name,
                    data=marshal(user, dataformat.get_full_user()))

        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to add new user. Duplicate.")
            abort(409, title="User Not Saved", message="Sorry, this ID already exists and IDs must be unique in ComPAIR. Please try addding another user.")

        # handle lti_create_user_link teardown for third party logins
        if sess.get('lti_create_user_link'):
            authenticate(user, login_method='LTI')
            sess.pop('lti_create_user_link')

        return marshal_user_data(user)


# /courses
class CurrentUserCourseListAPI(Resource):
    @login_required
    def get(self):
        params = user_course_list_parser.parse_args()

        # Note, start and end dates are optional so default sort is by start_date (course.start_date or min assignment start date), then name
        query = Course.query \
            .filter_by(active=True) \
            .order_by(Course.start_date_order.desc(), Course.name) \

        # we want to list user linked courses only, so only check the association table
        if not can(MANAGE, Course):
            query = query.join(UserCourse) \
                .filter(and_(
                    UserCourse.user_id == current_user.id,
                    UserCourse.course_role != CourseRole.dropped
                ))

        if params['search']:
            search_terms = params['search'].split()
            for search_term in search_terms:
                if search_term != "":
                    search = '%'+search_term+'%'
                    query = query.filter(or_(
                        Course.name.like(search),
                        Course.year.like(search),
                        Course.term.like(search)
                    ))

        if params['includeSandbox'] != None:
            query = query.filter(
                Course.sandbox == params['includeSandbox']
            )

        if params['period'] != None:
            now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
            if params['period'] == 'upcoming':
                query = query.filter(
                    Course.start_date > now
                )
            elif params['period'] == 'active':
                query = query.filter(and_(
                    or_(Course.start_date == None, Course.start_date <= now),
                    or_(Course.end_date == None, Course.end_date >= now),
                ))
            elif params['period'] == 'past':
                query = query.filter(
                    Course.end_date < now
                )

        page = query.paginate(params['page'], params['perPage'])

        # TODO REMOVE COURSES WHERE COURSE IS UNAVAILABLE?

        on_user_course_get.send(
            self,
            event_name=on_user_course_get.name,
            user=current_user)

        return {"objects": marshal(page.items, dataformat.get_course()),
                "page": page.page, "pages": page.pages,
                "total": page.total, "per_page": page.per_page}

# /id/courses
class UserCourseListAPI(Resource):
    @login_required
    def get(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)

        require(MANAGE, User,
            title="User's Courses Unavailable",
            message="Sorry, your system role does not allow you to view courses for this user.")

        params = user_id_course_list_parser.parse_args()

        query = Course.query \
            .with_entities(Course, UserCourse) \
            .options(joinedload(UserCourse.group)) \
            .join(UserCourse, and_(
                UserCourse.course_id == Course.id,
                UserCourse.user_id == user.id,
            )) \
            .filter(and_(
                Course.active == True,
                UserCourse.course_role != CourseRole.dropped
            ))

        if params['search']:
            search_terms = params['search'].split()
            for search_term in search_terms:
                if search_term != "":
                    search = '%'+search_term+'%'
                    query = query.filter(or_(
                        Course.name.like(search),
                        Course.year.like(search),
                        Course.term.like(search)
                    ))

        if params['includeSandbox'] != None:
            query = query.filter(
                Course.sandbox == params['includeSandbox']
            )

        if params['orderBy']:
            if params['reverse']:
                query = query.order_by(desc(params['orderBy']))
            else:
                query = query.order_by(asc(params['orderBy']))
        query = query.order_by(Course.start_date_order.desc(), Course.name)

        page = query.paginate(params['page'], params['perPage'])

        # fix results
        courses = []
        for (_course, _user_course) in page.items:
            _course.course_role = _user_course.course_role
            _course.group = _user_course.group
            _course.group_uuid = _course.group.uuid if _course.group else None
            courses.append(_course)
        page.items = courses

        on_user_course_get.send(
            self,
            event_name=on_user_course_get.name,
            user=user)

        return {"objects": marshal(page.items, dataformat.get_user_courses()),
                "page": page.page, "pages": page.pages,
                "total": page.total, "per_page": page.per_page}

# /courses/status
class UserCourseStatusListAPI(Resource):
    @login_required
    def get(self):
        params = user_course_status_list_parser.parse_args()
        course_uuids = params['ids'].split(',')

        if params['ids'] == '' or len(course_uuids) == 0:
            abort(400, title="Course Status Unavailable", message="Please select a course from the list of courses to see that course's status.")

        query = Course.query \
            .filter(and_(
                Course.uuid.in_(course_uuids),
                Course.active == True,
            )) \
            .add_columns(UserCourse.course_role, UserCourse.group_id) \

        if not can(MANAGE, Course):
            query = query.join(UserCourse, and_(
                    UserCourse.user_id == current_user.id,
                    UserCourse.course_id == Course.id,
                    UserCourse.course_role != CourseRole.dropped
                ))
        else:
            query = query.outerjoin(UserCourse, and_(
                    UserCourse.user_id == current_user.id,
                    UserCourse.course_id == Course.id
                ))

        results = query.all()

        if len(course_uuids) != len(results):
            abort(400, title="Course Status Unavailable",
                message="Sorry, you are not enrolled in one or more of the selected users' courses yet. Course status is not available until your are enrolled in the course.")

        statuses = {}

        for course, course_role, group_id in results:
            incomplete_assignment_ids = set()
            if not can(MANAGE, Course) and course_role == CourseRole.student:
                answer_period_assignments = [assignment for assignment in course.assignments if assignment.active and assignment.answer_period]
                compare_period_assignments = [assignment for assignment in course.assignments if assignment.active and assignment.compare_period]

                if len(answer_period_assignments) > 0:
                    answer_period_assignment_ids = [assignment.id for assignment in answer_period_assignments]
                    answers = Answer.query \
                        .filter(and_(
                            or_(
                                and_(Answer.group_id == group_id, Answer.group_id != None),
                                Answer.user_id == current_user.id,
                            ),
                            Answer.assignment_id.in_(answer_period_assignment_ids),
                            Answer.active == True,
                            Answer.practice == False,
                            Answer.draft == False
                        ))
                    for assignment in answer_period_assignments:
                        answer = next(
                            (answer for answer in answers if answer.assignment_id == assignment.id),
                            None
                        )
                        if answer is None:
                            incomplete_assignment_ids.add(assignment.id)

                if len(compare_period_assignments) > 0:
                    compare_period_assignment_ids = [assignment.id for assignment in compare_period_assignments]
                    comparisons = Comparison.query \
                        .filter(and_(
                            Comparison.user_id == current_user.id,
                            Comparison.assignment_id.in_(compare_period_assignment_ids),
                            Comparison.completed == True
                        ))

                    self_evaluations = AnswerComment.query \
                        .join(Answer) \
                        .with_entities(
                            Answer.assignment_id,
                            func.count(Answer.assignment_id).label('self_evaluation_count')
                        ) \
                        .filter(and_(
                            or_(
                                and_(Answer.group_id == group_id, Answer.group_id != None),
                                Answer.user_id == current_user.id,
                            ),
                            AnswerComment.active == True,
                            AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                            AnswerComment.draft == False,
                            Answer.active == True,
                            Answer.practice == False,
                            Answer.draft == False,
                            Answer.assignment_id.in_(compare_period_assignment_ids)
                        )) \
                        .group_by(Answer.assignment_id) \
                        .all()

                    for assignment in compare_period_assignments:
                        assignment_comparisons = [comparison for comparison in comparisons if comparison.assignment_id == assignment.id]
                        if len(assignment_comparisons) < assignment.total_comparisons_required:
                            incomplete_assignment_ids.add(assignment.id)

                        if assignment.enable_self_evaluation:
                            self_evaluation_count = next(
                                (result.self_evaluation_count for result in self_evaluations if result.assignment_id == assignment.id),
                                0
                            )
                            if self_evaluation_count == 0:
                                incomplete_assignment_ids.add(assignment.id)

            statuses[course.uuid] = {
                'incomplete_assignments': len(incomplete_assignment_ids)
            }

        on_user_course_status_get.send(
            self,
            event_name=on_user_course_status_get.name,
            user=current_user,
            data=statuses)

        return {"statuses": statuses}

# /id/lti/users
class UserLTIListAPI(Resource):
    @login_required
    def get(self, user_uuid):

        user = User.get_by_uuid_or_404(user_uuid)

        require(MANAGE, User,
            title="User's LTI Account Links Unavailable",
            message="Sorry, your system role does not allow you to view LTI account links for this user.")

        lti_users = user.lti_user_links \
                        .order_by(
                            LTIUser.lti_consumer_id,
                            LTIUser.user_id
                            ) \
                        .all()

        on_user_lti_users_get.send(
            self,
            event_name=on_user_lti_users_get.name,
            user=current_user,
            data={'user_id': user.id})

        return {"objects": marshal(lti_users, dataformat.get_lti_user())}

# /id/lti/users/uuid
class UserLTIAPI(Resource):
    @login_required
    def delete(self, user_uuid, lti_user_uuid):
        """
        unlink lti user from compair user
        """

        user = User.get_by_uuid_or_404(user_uuid)
        lti_user = LTIUser.get_by_uuid_or_404(lti_user_uuid)

        require(MANAGE, User,
            title="User's LTI Account Links Unavailable",
            message="Sorry, your system role does not allow you to remove LTI account links for this user.")

        lti_user.compair_user_id = None
        db.session.commit()

        on_user_lti_user_unlink.send(
            self,
            event_name=on_user_lti_user_unlink.name,
            user=current_user,
            data={'user_id': user.id, 'lti_user_id': lti_user.id})

        return { 'success': True }

# /id/third_party/users
class UserThirdPartyUserListAPI(Resource):
    @login_required
    def get(self, user_uuid):

        user = User.get_by_uuid_or_404(user_uuid)

        require(MANAGE, User,
            title="User's Third Party Logins Unavailable",
            message="Sorry, your system role does not allow you to view third party logins for this user.")

        third_party_users = ThirdPartyUser.query \
                                .filter(ThirdPartyUser.user_id == user.id) \
                                .order_by(
                                    ThirdPartyUser.third_party_type,
                                    ThirdPartyUser.unique_identifier
                                    ) \
                                .all()

        on_user_third_party_users_get.send(
            self,
            event_name=on_user_third_party_users_get.name,
            user=current_user,
            data={'user_id': user.id})

        return {"objects": marshal(third_party_users, dataformat.get_third_party_user())}

#/id/third_party/users/uuid
class UserThirdPartyUserAPI(Resource):
    @login_required
    def delete(self, user_uuid, third_party_user_uuid):

        user = User.get_by_uuid_or_404(user_uuid)
        third_party_user = ThirdPartyUser.get_by_uuid_or_404(third_party_user_uuid)

        require(MANAGE, User,
            title="User's Third Party Logins Unavailable",
            message="Sorry, your system role does not allow you to delete third party connections for this user.")

        on_user_third_party_user_delete.send(
            self,
            event_name=on_user_third_party_user_delete.name,
            user=current_user,
            data={'user_id': user.id, 'third_party_type': third_party_user.third_party_type, 'unique_identifier': third_party_user.unique_identifier})

        # TODO: consider adding soft delete to thrid_party_user in the future
        ThirdPartyUser.query.filter(ThirdPartyUser.uuid == third_party_user_uuid).delete()
        db.session.commit()

        return { 'success': True }

# courses/teaching
class TeachingUserCourseListAPI(Resource):
    @login_required
    def get(self):
        if can(MANAGE, Course()):
            courses = Course.query.filter_by(active=True).all()
        else:
            courses = []
            for user_course in current_user.user_courses:
                if user_course.course.active and can(MANAGE, Assignment(course_id=user_course.course_id)):
                    courses.append(user_course.course)

        course_list = [{'id': c.uuid, 'name': c.name} for c in courses]

        on_teaching_course_get.send(
            self,
            event_name=on_teaching_course_get.name,
            user=current_user
        )

        return {'courses': course_list}

# /user_uuid/edit
class UserEditButtonAPI(Resource):
    @login_required
    def get(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)
        available = can(EDIT, user)

        on_user_edit_button_get.send(
            self,
            event_name=on_user_edit_button_get.name,
            user=current_user,
            data={'user_id': user.id, 'available': available})

        return {'available': available}

# /notification
class UserUpdateNotificationAPI(Resource):
    @login_required
    def post(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)
        # anyone who passes checking below should be an admin or current user
        if not can(MANAGE, user) and not user.id == current_user.id and not \
                (can(EDIT, user) and current_app.config.get('EXPOSE_EMAIL_TO_INSTRUCTOR', False)):
            abort(403, title="Notifications Not Updated", message="Sorry, your system role does not allow you to update notification settings for this user.")

        if not user.email:
            abort(400, title="Notifications Not Updated",
                message="Sorry, you cannot update notification settings since this user does not have an email address in ComPAIR.")

        params = update_notification_settings_parser.parse_args()

        email_notification_method = params.get("email_notification_method")
        check_valid_email_notification_method(email_notification_method)
        user.email_notification_method = EmailNotificationMethod(email_notification_method)

        db.session.commit()
        on_user_notifications_update.send(
            self,
            event_name=on_user_notifications_update.name,
            user=current_user)

        return marshal_user_data(user)

# /password
class UserUpdatePasswordAPI(Resource):
    @login_required
    def post(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)
        # anyone who passes checking below should be an instructor or admin
        require(EDIT, user,
            title="Password Not Saved",
            message="Sorry, your system role does not allow you to update passwords for this user.")

        if not user.uses_compair_login:
            abort(400, title="Password Not Saved",
                message="Sorry, you cannot update the password since this user does not use the ComPAIR account login method.")

        params = update_password_parser.parse_args()
        oldpassword = params.get('oldpassword')

        if current_user.id == user.id and not oldpassword:
            abort(400, title="Password Not Saved", message="Sorry, the old password is required. Please enter the old password and try saving again.")
        elif current_user.id == user.id and not user.verify_password(oldpassword):
            abort(400, title="Password Not Saved", message="Sorry, the old password is not correct. Please double-check the old password and try saving again.")
        elif len(params.get('newpassword')) < 4:
            abort(400, title="Password Not Saved", message="The new password must be at least 4 characters long.")

        user.password = params.get('newpassword')
        db.session.commit()
        on_user_password_update.send(
            self,
            event_name=on_user_password_update.name,
            user=current_user)

        return marshal_user_data(user)

api = new_restful_api(user_api)
api.add_resource(UserAPI, '/<user_uuid>')
api.add_resource(UserListAPI, '')
api.add_resource(UserCourseListAPI, '/<user_uuid>/courses')
api.add_resource(UserThirdPartyUserAPI, '/<user_uuid>/third_party/users/<third_party_user_uuid>')
api.add_resource(UserThirdPartyUserListAPI, '/<user_uuid>/third_party/users')
api.add_resource(UserLTIAPI, '/<user_uuid>/lti/users/<lti_user_uuid>')
api.add_resource(UserLTIListAPI, '/<user_uuid>/lti/users')
api.add_resource(CurrentUserCourseListAPI, '/courses')
api.add_resource(UserCourseStatusListAPI, '/courses/status')
api.add_resource(TeachingUserCourseListAPI, '/courses/teaching')
api.add_resource(UserEditButtonAPI, '/<user_uuid>/edit')
api.add_resource(UserUpdateNotificationAPI, '/<user_uuid>/notification')
api.add_resource(UserUpdatePasswordAPI, '/<user_uuid>/password')
