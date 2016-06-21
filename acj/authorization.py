from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE, DELETE
from flask_bouncer import ensure
from flask_login import current_user
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy import and_

from .models import Course, User, UserCourse, CourseRole, SystemRole, Assignment, Answer, \
    AnswerComment, Comparison, Criterion, AssignmentComment, AssignmentCriterion

USER_IDENTITY = 'permission_user_identity'


def define_authorization(user, they):
    """
    Sets up user permissions for Flask-Bouncer
    """
    if not user.is_authenticated():
        return  # user isn't logged in

    def if_my_student(student):
        course_subquery = Course.query \
            .with_entities(Course.id) \
            .join(UserCourse) \
            .filter(and_(
                UserCourse.user_id == user.id,
                UserCourse.course_role == CourseRole.instructor
            )) \
            .subquery()
        exists = Course.query. \
            join(UserCourse) \
            .filter(and_(
                UserCourse.user_id == student.id,
                UserCourse.course_role == CourseRole.student
            )) \
            .filter(Course.id.in_(course_subquery)) \
            .count()
        return bool(exists)

    def if_system_role_equal_or_lower_than_me(target):

        if user.system_role == SystemRole.instructor:
            return target.system_role != SystemRole.sys_admin
        elif user.system_role == SystemRole.sys_admin:
            return True
        else:
            # student can't create user
            return False

    # Assign permissions based on system roles
    if user.system_role == SystemRole.sys_admin:
        # sysadmin can do anything
        they.can(MANAGE, ALL)
    elif user.system_role == SystemRole.instructor:
        # instructors can create courses
        they.can(CREATE, Course)
        they.can(CREATE, Criterion)
        they.can(EDIT, User, if_my_student)
        they.can(CREATE, User, if_system_role_equal_or_lower_than_me)
        they.can(READ, USER_IDENTITY)

    # users can edit and read their own user account
    they.can((READ, EDIT), User, id=user.id)
    # they can also look at their own course enrolments
    they.can(READ, UserCourse, user_id=user.id)
    # they can read and edit their own criteria
    they.can((READ, EDIT), Criterion, user_id=user.id)

    # Assign permissions based on course roles
    # give access to courses the user is enroled in
    for entry in user.user_courses:
        if entry.course_role == CourseRole.dropped:
            continue
        they.can(READ, Course, id=entry.course_id)
        they.can(READ, Assignment, course_id=entry.course_id)
        they.can((READ, CREATE), Answer, course_id=entry.course_id)
        they.can((EDIT, DELETE), Answer, user_id=user.id)
        they.can((READ, CREATE), AssignmentComment, course_id=entry.course_id)
        they.can((EDIT, DELETE), AssignmentComment, user_id=user.id)
        they.can((READ, CREATE), AnswerComment, course_id=entry.course_id)
        # owner of the answer comment
        they.can((EDIT, DELETE), AnswerComment, user_id=user.id)
        # instructors can modify the course and enrolment
        if entry.course_role == CourseRole.instructor:
            they.can(EDIT, Course, id=entry.course_id)
            they.can(EDIT, UserCourse, course_id=entry.course_id)
        # instructors and ta can do anything they want to assignments
        if entry.course_role == CourseRole.instructor or \
                entry.course_role == CourseRole.teaching_assistant:
            they.can(MANAGE, Assignment, course_id=entry.course_id)
            they.can(MANAGE, Answer, course_id=entry.course_id)
            they.can(MANAGE, AssignmentComment, course_id=entry.course_id)
            they.can(MANAGE, AnswerComment, course_id=entry.course_id)
            they.can(READ, UserCourse, course_id=entry.course_id)
            they.can((CREATE, DELETE), AssignmentCriterion, course_id=entry.course_id)
            they.can(READ, USER_IDENTITY)
            # TA can create criteria
            they.can(CREATE, Criterion)
        # only students can submit comparisons for now
        if entry.course_role == CourseRole.student:
            they.can(CREATE, Comparison, course_id=entry.course_id)


# Tell the client side about a user's permissions.
# This is necessarily more simplified than Flask-Bouncer's implementation.
# I'm hoping that we don't need fine grained permission checking to the
# level of individual entries. This is only going to be at a coarse level
# of models.
# Note that it looks like Flask-Bouncer judges a user to have permission
# on an model if they're allowed to operate on one instance of it.
# E.g.: A user who can only EDIT their own User object would have
# ensure(READ, User) return True
def get_logged_in_user_permissions():
    user = User.query.get(current_user.id)
    require(READ, user)
    courses = UserCourse.query.filter_by(user_id=current_user.id) \
        .filter(UserCourse.course_role != CourseRole.dropped).all()
    admin = user.system_role == SystemRole.sys_admin
    permissions = {}
    models = {
        User.__name__: user,
    }
    operations = {
        MANAGE,
        READ,
        EDIT,
        CREATE,
        DELETE
    }
    # global models
    for model_name, model in models.items():
        # create entry if not already exists
        permissions.setdefault(model_name, {})
        # if not model_name in permissions:
        # permissions[model_name] = {}
        # obtain permission values for each operation
        for operation in operations:
            permissions[model_name][operation] = {'global': True}
            try:
                ensure(operation, model)
            except Unauthorized:
                permissions[model_name][operation]['global'] = False
    # course model
    # model_name / operation / courseId OR global
    permissions['Course'] = {CREATE: {'global': allow(CREATE, Course)}}
    mod_operations = {MANAGE, READ, EDIT, DELETE}
    for operation in mod_operations:
        permissions['Course'].setdefault(operation, {})
        permissions['Course'][operation]['global'] = admin
        for course in courses:
            course_id = str(course.course_id)
            try:
                ensure(operation, Course(id=course.course_id))
                permissions['Course'][operation][course_id] = True
                permissions['Course'][operation]['global'] = True
            except Unauthorized:
                permissions['Course'][operation][course_id] = False

    # assignment model
    # model_name / operation / courseId OR global
    permissions['Assignment'] = {}
    mod_operations = {MANAGE, READ, EDIT, CREATE, DELETE}
    for operation in mod_operations:
        permissions['Assignment'].setdefault(operation, {})
        permissions['Assignment'][operation]['global'] = admin
        for course in courses:
            course_id = str(course.course_id)
            try:
                ensure(operation, Assignment(course_id=course.course_id))
                permissions['Assignment'][operation][course_id] = True
                permissions['Assignment'][operation]['global'] = True
            except Unauthorized:
                permissions['Assignment'][operation][course_id] = False

    return permissions


def allow(operation, target):
    """
    This duplicates bouncer's can() operation since flask-bouncer doesn't implement it.
    Named allow() to avoid namespace confusion with bouncer.
    """
    try:
        ensure(operation, target)
        return True
    except Unauthorized:
        return False


def require(operation, target):
    """
    This is basically Flask-Bouncer's ensure except it throws a 403 instead of a 401
    if the permission check fails. A 403 is more accurate since authentication would
    not help and it would prevent the login box from showing up. Named require() to avoid
    confusion with Flask-Bouncer
    :param operation: same as Flask-Bouncer's ensure
    :param target: same as Flask-Bouncer's ensure
    :return:same as Flask-Bouncer's ensure
    """
    try:
        ensure(operation, target)
    except Unauthorized as e:
        raise Forbidden(e.get_description())


def is_user_access_restricted(user):
    """
    determine if the current user has full view of another user
    This provides a measure of anonymity among students, while instructors and above can see real names.
    """
    # Determine if the logged in user can view full info on the target user
    access_restricted = not allow(READ, user)
    if access_restricted:
        enrolments = UserCourse.query.filter_by(user_id=user.id).all()
        # if the logged in user can edit the target user's enrolments, then we let them see full info
        for enrolment in enrolments:
            if allow(EDIT, enrolment):
                access_restricted = False
                break

    return access_restricted
