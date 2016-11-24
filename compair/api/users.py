from flask import Blueprint, current_app, abort, session as sess
from bouncer.constants import MANAGE, EDIT, CREATE, READ
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from flask_login import login_required, current_user
from sqlalchemy.orm import load_only
from sqlalchemy import exc, asc, or_, and_, func

from . import dataformat
from compair.authorization import is_user_access_restricted, require, allow
from compair.core import db, event
from .util import new_restful_api, get_model_changes, pagination_parser
from compair.models import User, SystemRole, Course, UserCourse, CourseRole, \
    Assignment, LTIUser, LTIUserResourceLink, LTIContext, ThirdPartyUser, ThirdPartyType, \
    Answer, Comparison, AnswerComment, AnswerCommentType
from compair.api.login import authenticate

user_api = Blueprint('user_api', __name__)

def non_blank_str(value):
    if value is None:
        return None
    else:
        return None if str(value).strip() == "" else str(value)

new_user_parser = RequestParser()
new_user_parser.add_argument('username', type=str, required=False)
new_user_parser.add_argument('student_number', type=non_blank_str)
new_user_parser.add_argument('system_role', type=str, required=True)
new_user_parser.add_argument('firstname', type=str, required=True)
new_user_parser.add_argument('lastname', type=str, required=True)
new_user_parser.add_argument('displayname', type=str, required=True)
new_user_parser.add_argument('email', type=str)
new_user_parser.add_argument('password', type=str, required=False)

existing_user_parser = RequestParser()
existing_user_parser.add_argument('id', type=str, required=True)
existing_user_parser.add_argument('username', type=str, required=False)
existing_user_parser.add_argument('student_number', type=non_blank_str)
existing_user_parser.add_argument('system_role', type=str, required=True)
existing_user_parser.add_argument('firstname', type=str, required=True)
existing_user_parser.add_argument('lastname', type=str, required=True)
existing_user_parser.add_argument('displayname', type=str, required=True)
existing_user_parser.add_argument('email', type=str)

update_password_parser = RequestParser()
update_password_parser.add_argument('oldpassword', type=str, required=False)
update_password_parser.add_argument('newpassword', type=str, required=True)

user_list_parser = pagination_parser.copy()
user_list_parser.add_argument('search', type=str, required=False, default=None)
user_list_parser.add_argument('ids', type=str, required=False, default=None)

user_course_list_parser = pagination_parser.copy()
user_course_list_parser.add_argument('search', type=str, required=False, default=None)

user_course_status_list_parser = RequestParser()
user_course_status_list_parser.add_argument('ids', type=str, required=True, default=None)

# events
on_user_modified = event.signal('USER_MODIFIED')
on_user_get = event.signal('USER_GET')
on_user_list_get = event.signal('USER_LIST_GET')
on_user_create = event.signal('USER_CREATE')
on_user_course_get = event.signal('USER_COURSE_GET')
on_user_course_status_get = event.signal('USER_COURSE_STATUS_GET')
on_teaching_course_get = event.signal('USER_TEACHING_COURSE_GET')
on_user_edit_button_get = event.signal('USER_EDIT_BUTTON_GET')
on_user_password_update = event.signal('USER_PASSWORD_UPDATE')

def check_valid_system_role(system_role):
    system_roles = [
        SystemRole.sys_admin.value,
        SystemRole.instructor.value,
        SystemRole.student.value
    ]
    if system_role not in system_roles:
        abort(400)

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
        return marshal(user, dataformat.get_user(is_user_access_restricted(user)))

    @login_required
    def post(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)

        if is_user_access_restricted(user):
            return {'error': "Sorry, you don't have permission for this action."}, 403

        params = existing_user_parser.parse_args()

        # make sure the user id in the url and the id matches
        if params['id'] != user_uuid:
            return {"error": "User id does not match URL."}, 400

        # only update username if user uses compair login method
        if user.uses_compair_login:
            username = params.get("username", user.username)
            if username == None:
                return {"error": "Missing required parameter: username."}, 400
            username_exists = User.query.filter_by(username=username).first()
            if username_exists and username_exists.id != user.id:
                return {"error": "This username already exists. Please pick another."}, 409
            else:
                user.username = username
        else:
            user.username = None

        if allow(MANAGE, user):
            system_role = params.get("system_role", user.system_role.value)
            check_valid_system_role(system_role)
            user.system_role = SystemRole(system_role)

        # only students should have student numbers
        if user.system_role == SystemRole.student:
            student_number = params.get("student_number", user.student_number)
            student_number_exists = User.query.filter_by(student_number=student_number).first()
            if student_number is not None and student_number_exists and student_number_exists.id != user.id:
                return {"error": "This student number already exists. Please pick another."}, 409
            else:
                user.student_number = student_number
        else:
            user.student_number = None

        user.firstname = params.get("firstname", user.firstname)
        user.lastname = params.get("lastname", user.lastname)
        user.displayname = params.get("displayname", user.displayname)

        user.email = params.get("email", user.email)
        changes = get_model_changes(user)

        restrict_user = not allow(EDIT, user)

        try:
            db.session.commit()
            on_user_modified.send(
                self,
                event_name=on_user_modified.name,
                user=current_user,
                data={'id': user.id, 'changes': changes})
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to edit user. Duplicate.")
            return {'error': 'A user with the same identifier already exists.'}, 409

        return marshal(user, dataformat.get_user(restrict_user))

# /
class UserListAPI(Resource):
    @login_required
    def get(self):
        restrict_user = not allow(READ, User)

        params = user_list_parser.parse_args()

        query = User.query
        if params['search']:
            search = '%{}%'.format(params['search'])
            query = query.filter(or_(User.firstname.like(search), User.lastname.like(search)))
        page = query.paginate(params['page'], params['perPage'])

        on_user_list_get.send(
            self,
            event_name=on_user_list_get.name,
            user=current_user)

        return {"objects": marshal(page.items, dataformat.get_user(restrict_user)), "page": page.page,
                "pages": page.pages, "total": page.total, "per_page": page.per_page}

    def post(self):
        # login_required when oauth_create_user_link not set
        if not sess.get('oauth_create_user_link'):
            if not current_app.login_manager._login_disabled and \
                    not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()

        user = User()
        params = new_user_parser.parse_args()
        user.student_number = params.get("student_number", None)
        user.email = params.get("email")
        user.firstname = params.get("firstname")
        user.lastname = params.get("lastname")
        user.displayname = params.get("displayname")

        # if creating a cas user, do not set username or password
        if sess.get('oauth_create_user_link') and sess.get('LTI') and sess.get('CAS_CREATE'):
            user.username = None
            user.password = None
        else:
            # else enforce required password and unique username
            user.password = params.get("password")
            if user.password == None:
                return {"error": "Missing required parameter: password."}, 400

            user.username = params.get("username")
            if user.username == None:
                return {"error": "Missing required parameter: username."}, 400

            username_exists = User.query.filter_by(username=user.username).first()
            if username_exists:
                return {"error": "This username already exists. Please pick another."}, 409

        student_number_exists = User.query.filter_by(student_number=user.student_number).first()
        # if student_number is not left blank and it exists -> 409 error
        if user.student_number is not None and student_number_exists:
            return {"error": "This student number already exists. Please pick another."}, 409

        # handle oauth_create_user_link setup for third party logins
        if sess.get('oauth_create_user_link'):
            if sess.get('LTI'):
                lti_user = LTIUser.query.get_or_404(sess['lti_user'])
                lti_user.compair_user = user
                user.system_role = lti_user.system_role

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

                if sess.get('CAS_CREATE'):
                    thirdpartyuser = ThirdPartyUser(
                        third_party_type=ThirdPartyType.cas,
                        unique_identifier=sess.get('CAS_UNIQUE_IDENTIFIER'),
                        params=sess.get('CAS_ADDITIONAL_PARAMS'),
                        user=user
                    )
                    db.session.add(thirdpartyuser)
        else:
            system_role = params.get("system_role")
            check_valid_system_role(system_role)
            user.system_role = SystemRole(system_role)

            require(CREATE, user)

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
                    data=marshal(user, dataformat.get_user(False)))
            else:
                on_user_create.send(
                    self,
                    event_name=on_user_create.name,
                    data=marshal(user, dataformat.get_user(False)))

        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.error("Failed to add new user. Duplicate.")
            return {'error': 'A user with the same identifier already exists.'}, 400

        # handle oauth_create_user_link teardown for third party logins
        if sess.get('oauth_create_user_link'):
            authenticate(user)
            sess.pop('oauth_create_user_link')

            if sess.get('CAS_CREATE'):
                sess.pop('CAS_CREATE')
                sess.pop('CAS_UNIQUE_IDENTIFIER')
                sess['CAS_LOGIN'] = True

        return marshal(user, dataformat.get_user())


# /courses
class UserCourseListAPI(Resource):
    @login_required
    def get(self):
        params = user_course_list_parser.parse_args()

        # Note, start and end dates are optional so default sort is by start_date, end_date, then name
        query = Course.query \
            .filter_by(active=True) \
            .order_by(Course.start_date.desc(), Course.end_date.desc(), Course.name) \

        # we want to list user linked courses only, so only check the association table
        if not allow(MANAGE, Course):
            query = query.join(UserCourse) \
                .filter(and_(
                    UserCourse.user_id == current_user.id,
                    UserCourse.course_role != CourseRole.dropped
                ))

        if params['search']:
            search_terms = params['search'].split()
            for search_term in search_terms:
                if search_term != "":
                    search = '%{}%'.format(search_term)
                    query = query.filter(or_(
                        Course.name.like(search),
                        Course.year.like(search),
                        Course.term.like(search)
                    ))
        page = query.paginate(params['page'], params['perPage'])

        # TODO REMOVE COURSES WHERE COURSE IS UNAVAILABLE?

        on_user_course_get.send(
            self,
            event_name=on_user_course_get.name,
            user=current_user)

        return {"objects": marshal(page.items, dataformat.get_course()),
                "page": page.page, "pages": page.pages,
                "total": page.total, "per_page": page.per_page}

# /courses/status
class UserCourseStatusListAPI(Resource):
    @login_required
    def get(self):
        params = user_course_status_list_parser.parse_args()
        course_uuids = params['ids'].split(',')

        if len(course_uuids) == 0:
            return {"error": "Select at least one course"}, 400

        query = Course.query \
            .filter(and_(
                Course.uuid.in_(course_uuids),
                Course.active == True
            ))
        if not allow(MANAGE, Course):
            query = query.join(UserCourse, and_(
                UserCourse.user_id == current_user.id,
                UserCourse.course_role != CourseRole.dropped
            ))
        courses = query.all()

        if len(course_uuids) != len(courses):
            return {"error": "Not enrolled in course"}, 400

        statuses = {}

        for course in courses:
            incomplete_assignment_ids = set()
            answer_period_assignments = [assignment for assignment in course.assignments if assignment.active and assignment.answer_period]
            compare_period_assignments = [assignment for assignment in course.assignments if assignment.active and assignment.compare_period]

            if len(answer_period_assignments) > 0:
                answer_period_assignment_ids = [assignment.id for assignment in answer_period_assignments]
                answers = Answer.query \
                    .filter(and_(
                        Answer.user_id == current_user.id,
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
                    .join("answer") \
                    .with_entities(
                        Answer.assignment_id,
                        func.count(Answer.assignment_id).label('self_evaluation_count')
                    ) \
                    .filter(and_(
                        AnswerComment.user_id == current_user.id,
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
                    comparison_count = len(assignment_comparisons) / assignment.criteria_count if assignment.criteria_count else 0
                    if comparison_count < assignment.total_comparisons_required:
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

# courses/teaching
class TeachingUserCourseListAPI(Resource):
    @login_required
    def get(self):
        if allow(MANAGE, Course()):
            courses = Course.query.all()
            course_list = [{'id': c.uuid, 'name': c.name} for c in courses]
        else:
            course_list = []
            for user_course in current_user.user_courses:
                if allow(MANAGE, Assignment(course_id=user_course.course_id)):
                    course_list.append({
                        'id': user_course.course_uuid,
                        'name': user_course.course.name
                    })

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
        available = allow(EDIT, user)

        on_user_edit_button_get.send(
            self,
            event_name=on_user_edit_button_get.name,
            user=current_user,
            data={'user_id': user.id, 'available': available})

        return {'available': available}

# /password
class UserUpdatePasswordAPI(Resource):
    @login_required
    def post(self, user_uuid):
        user = User.get_by_uuid_or_404(user_uuid)
        # anyone who passes checking below should be an instructor or admin
        require(EDIT, user)

        if user.uses_compair_login:
            params = update_password_parser.parse_args()
            oldpassword = params.get('oldpassword')
            # if it is not current user changing own password, it must be an instructor or admin
            # because of above check
            if current_user.id != user.id or (oldpassword and user.verify_password(oldpassword)):
                user.password = params.get('newpassword')
                db.session.commit()
                on_user_password_update.send(
                    self,
                    event_name=on_user_password_update.name,
                    user=current_user)
                return marshal(user, dataformat.get_user(False))
            else:
                return {"error": "The old password is incorrect or you do not have permission to change password."}, 403
        else:
            return {"error": "Cannot update password. User does not use ComPAIR account login authentication method."}, 400


api = new_restful_api(user_api)
api.add_resource(UserAPI, '/<user_uuid>')
api.add_resource(UserListAPI, '')
api.add_resource(UserCourseListAPI, '/courses')
api.add_resource(UserCourseStatusListAPI, '/courses/status')
api.add_resource(TeachingUserCourseListAPI, '/courses/teaching')
api.add_resource(UserEditButtonAPI, '/<user_uuid>/edit')
api.add_resource(UserUpdatePasswordAPI, '/<user_uuid>/password')
