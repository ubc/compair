from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE, DELETE
from flask_bouncer import can, ensure
from flask_login import current_user
from werkzeug.exceptions import Forbidden
from sqlalchemy import and_

from .core import abort, impersonation

from .models import Course, User, UserCourse, CourseRole, SystemRole, \
    Assignment, Answer, AnswerComment, Comparison, Criterion, \
    AssignmentCriterion, ComparisonExample, File, Group

USER_IDENTITY = 'permission_user_identity'


def define_authorization(user, they, impersonation_original_user=None):
    """
    Sets up user permissions for Flask-Bouncer
    """
    if not user.is_authenticated:
        return  # user isn't logged in

    original_user_courses_dict = {} if not impersonation_original_user else \
        {c.course_id: c for c in impersonation_original_user.user_courses \
            if c.course_role != CourseRole.dropped}

    def if_my_student(student):
        course_subquery = Course.query \
            .with_entities(Course.id) \
            .join(UserCourse) \
            .filter(and_(
                UserCourse.user_id == user.id,
                UserCourse.course_role == CourseRole.instructor
            ))
        exists = Course.query. \
            join(UserCourse) \
            .filter(and_(
                UserCourse.user_id == student.id,
                UserCourse.course_role == CourseRole.student
            )) \
            .filter(Course.id.in_(course_subquery)) \
            .count()
        return bool(exists)

    def if_can_delete_attachment_reference(file):
        for assignment in file.assignments.all():
            if can(DELETE, assignment):
                return True

        for answer in file.answers.all():
            if can(DELETE, answer):
                return True

        return False

    # Assign permissions based on system roles
    if user.system_role == SystemRole.sys_admin:
        # sysadmin can do anything
        they.can(MANAGE, ALL)
    elif user.system_role == SystemRole.instructor:
        # instructors can create courses
        they.can(CREATE, Course)
        # instructors can read the default criterion
        they.can(READ, Criterion, public=True)
        they.can(CREATE, Criterion)
        they.can(EDIT, User, if_my_student)
        they.can(READ, USER_IDENTITY)
        # instructors can impersonate their students
        they.can(impersonation.IMPERSONATE, User, if_my_student) # TODO also check if it is a current course??

    # users can edit and read their own user account
    they.can((READ, EDIT), User, id=user.id)
    # they can also look at their own course enrolments
    they.can(READ, UserCourse, user_id=user.id)
    # they can read and edit their own criteria
    they.can((READ, EDIT), Criterion, user_id=user.id)

    # they can delete their own attachments
    they.can(DELETE, File, user_id=user.id)

    # Assign permissions based on course roles
    # give access to courses the user is enroled in
    for entry in user.user_courses:
        if entry.course_role == CourseRole.dropped:
            continue
        # if impersonating and the original user has no access to the course, skip it
        if impersonation_original_user \
            and not original_user_courses_dict.get(entry.course_id, None) \
            and not impersonation_original_user.system_role == SystemRole.sys_admin:
            continue
        they.can(READ, Course, id=entry.course_id)
        they.can(READ, Assignment, course_id=entry.course_id)
        # only owner/Instructors/TAs can read answer drafts
        they.can(READ, Answer, course_id=entry.course_id, draft=False)
        they.can(CREATE, Answer, course_id=entry.course_id)
        they.can((EDIT, DELETE, READ), Answer, user_id=user.id)
        if entry.group_id:
            they.can((EDIT, DELETE, READ), Answer, group_id=entry.group_id)
        they.can(DELETE, File, if_can_delete_attachment_reference)
        # only owner/Instructors/TAs can read answer comment drafts
        they.can(READ, AnswerComment, course_id=entry.course_id, draft=False)
        they.can(CREATE, AnswerComment, course_id=entry.course_id)
        # owner of the answer comment
        they.can((EDIT, DELETE, READ), AnswerComment, user_id=user.id)
        # students, instructor and ta can submit comparisons
        they.can((CREATE, EDIT), Comparison, course_id=entry.course_id)
        # instructors can modify the course, enrolment, and groups
        if entry.course_role == CourseRole.instructor:
            they.can((EDIT, DELETE), Course, id=entry.course_id)
            they.can(EDIT, UserCourse, course_id=entry.course_id)
            they.can((EDIT, DELETE, CREATE), Group, course_id=entry.course_id)
        # instructors and ta can do anything they want to assignments
        if entry.course_role == CourseRole.instructor or \
                entry.course_role == CourseRole.teaching_assistant:
            they.can(MANAGE, Assignment, course_id=entry.course_id)
            they.can(MANAGE, Answer, course_id=entry.course_id)
            they.can(MANAGE, AnswerComment, course_id=entry.course_id)
            they.can(MANAGE, ComparisonExample, course_id=entry.course_id)
            they.can(READ, Comparison, course_id=entry.course_id)
            they.can(READ, UserCourse, course_id=entry.course_id)
            they.can(READ, Group, course_id=entry.course_id)
            they.can((CREATE, DELETE), AssignmentCriterion, course_id=entry.course_id)
            they.can(READ, USER_IDENTITY)
            # TA can create criteria
            they.can(CREATE, Criterion)


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

    is_admin = user.system_role == SystemRole.sys_admin
    permissions = {}
    models = {
        User.__name__: user,
    }
    operations = [MANAGE, READ, EDIT,  CREATE, DELETE]

    # global models
    for model_name, model in models.items():
        # create entry if not already exists
        permissions.setdefault(model_name, {})
        # if not model_name in permissions:
        # permissions[model_name] = {}
        # obtain permission values for each operations

        global_permissions = set()
        for operation in operations:
            if can(operation, model):
                global_permissions.add(operation)
        permissions[model_name]['global'] = list(global_permissions)

    # course model
    # model_name / courseId OR global / operation
    permissions['Course'] = {}
    mod_operations = [MANAGE, READ, EDIT, DELETE]
    course_global_permissions = set()

    for user_course in user.user_courses:
        if user_course.course_role == CourseRole.dropped:
            continue
        course_permissions = set()
        for operation in mod_operations:
            if can(operation, Course(id=user_course.course_id)):
                course_permissions.add(operation)
                course_global_permissions.add(operation)
        permissions['Course'][user_course.course_uuid] = list(course_permissions)

    if can(CREATE, Course):
        course_global_permissions.add(CREATE)
    if is_admin:
        for operation in mod_operations:
            course_global_permissions.add(operation)
    permissions['Course']['global'] = list(course_global_permissions)

    # assignment model
    # model_name / courseId OR global / operation
    permissions['Assignment'] = {}
    assignment_global_permissions = set()

    for user_course in user.user_courses:
        if user_course.course_role == CourseRole.dropped:
            continue
        assignment_permissions = set()
        for operation in operations:
            if can(operation, Assignment(course_id=user_course.course_id)):
                assignment_permissions.add(operation)
                assignment_global_permissions.add(operation)
        permissions['Assignment'][user_course.course_uuid] = list(assignment_permissions)

    if is_admin:
        for operation in operations:
            assignment_global_permissions.add(operation)
    permissions['Assignment']['global'] = list(assignment_global_permissions)

    return permissions


def require(operation, target, title=None, message=None):
    """
    This is basically Flask-Bouncer's ensure except it also takes an optional
    error title and message that'll be passed to the user if the permission
    check failed. Named require() to avoid confusion with Flask-Bouncer
    :param operation: same as Flask-Bouncer's ensure
    :param target: same as Flask-Bouncer's ensure
    :return:same as Flask-Bouncer's ensure
    """
    try:
        ensure(operation, target)
    except Forbidden as e:
        if not title:
            title = "Forbidden"
        if not message:
            message = e.description
        abort(403, title=title, message=message)


def is_user_access_restricted(user):
    """
    determine if the current user has full view of another user
    This provides a measure of anonymity among students, while instructors and above can see real names.
    Also restrict access during impersonation
    """
    # Determine if the logged in user can view full info on the target user
    access_restricted = not can(READ, user) or impersonation.is_impersonating()
    if access_restricted:
        enrolments = UserCourse.query.filter_by(user_id=user.id).all()
        # if the logged in user can edit the target user's enrolments, then we let them see full info
        for enrolment in enrolments:
            if can(EDIT, enrolment):
                access_restricted = False
                break

    return access_restricted
