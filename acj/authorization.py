from bouncer.constants import ALL, MANAGE, EDIT, READ, CREATE, DELETE
from flask_bouncer import ensure
from flask_login import current_user
from werkzeug.exceptions import Unauthorized, Forbidden

from .models import Courses, CoursesAndUsers, Users, UserTypesForCourse, UserTypesForSystem, PostsForQuestions, PostsForAnswers, \
    PostsForAnswersAndPostsForComments, Judgements, Criteria, CriteriaAndCourses, \
    PostsForJudgements, Groups, GroupsAndUsers, CriteriaAndPostsForQuestions, Posts, PostsForComments

USER_IDENTITY = 'permission_user_identity'


def define_authorization(user, they):
    """
    Sets up user permissions for Flask-Bouncer
    """
    if not user.is_authenticated():
        return  # user isn't logged in

    def if_my_student(student):
        course_subquery = Courses.query.with_entities(Courses.id). \
            join(CoursesAndUsers).filter_by(users_id=user.id). \
            join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR). \
            subquery()
        exists = Courses.query. \
            join(CoursesAndUsers).filter_by(users_id=student.id). \
            join(UserTypesForCourse).filter_by(name=UserTypesForCourse.TYPE_STUDENT). \
            filter(Courses.id.in_(course_subquery)). \
            count()
        return bool(exists)

    def if_equal_or_lower_than_me(target):
        if user.usertypeforsystem.name == UserTypesForSystem.TYPE_INSTRUCTOR:
            system_role = UserTypesForSystem.query.get(target.usertypesforsystem_id)
            return system_role.name != UserTypesForSystem.TYPE_SYSADMIN

        # student can't create user
        return False

    # Assign permissions based on system roles
    user_system_role = user.usertypeforsystem.name
    if user_system_role == UserTypesForSystem.TYPE_SYSADMIN:
        # sysadmin can do anything
        they.can(MANAGE, ALL)
    elif user_system_role == UserTypesForSystem.TYPE_INSTRUCTOR:
        # instructors can create courses
        they.can(CREATE, Courses)
        they.can(CREATE, Criteria)
        they.can(EDIT, Users, if_my_student)
        they.can(CREATE, Users, if_equal_or_lower_than_me)
        they.can(READ, USER_IDENTITY)

    # users can edit and read their own user account
    they.can(READ, Users, id=user.id)
    they.can(EDIT, Users, id=user.id)
    # they can also look at their own course enrolments
    they.can(READ, CoursesAndUsers, users_id=user.id)
    # they can read and edit their own criteria
    they.can(READ, Criteria, users_id=user.id)
    they.can(EDIT, Criteria, users_id=user.id)

    # Assign permissions based on course roles
    # give access to courses the user is enroled in
    for entry in user.coursesandusers:
        if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_DROPPED:
            continue
        they.can(READ, Courses, id=entry.courses_id)
        they.can(READ, PostsForQuestions, courses_id=entry.courses_id)
        they.can((READ, CREATE), PostsForAnswers, courses_id=entry.courses_id)
        they.can((EDIT, DELETE), PostsForAnswers, users_id=user.id)
        they.can((READ, CREATE), PostsForComments, course_id=entry.courses_id)
        they.can((EDIT, DELETE), PostsForComments, user_id=user.id)
        they.can((READ, CREATE), PostsForAnswersAndPostsForComments, courses_id=entry.courses_id)
        # owner of the answer comment
        they.can((EDIT, DELETE), PostsForAnswersAndPostsForComments, users_id=user.id)
        # instructors can modify the course and enrolment
        if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR:
            they.can(EDIT, Courses, id=entry.courses_id)
            they.can(EDIT, CoursesAndUsers, courses_id=entry.courses_id)
            they.can((CREATE, DELETE), CriteriaAndCourses, courses_id=entry.courses_id)
            they.can((CREATE, DELETE), Groups, courses_id=entry.courses_id)
            they.can((CREATE, DELETE), GroupsAndUsers, courses_id=entry.courses_id)
        # instructors and ta can do anything they want to posts
        if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_INSTRUCTOR or \
                entry.usertypeforcourse.name == UserTypesForCourse.TYPE_TA:
            they.can(MANAGE, PostsForQuestions, courses_id=entry.courses_id)
            they.can(MANAGE, PostsForAnswers, courses_id=entry.courses_id)
            they.can(MANAGE, PostsForComments, course_id=entry.courses_id)
            they.can(MANAGE, PostsForAnswersAndPostsForComments, courses_id=entry.courses_id)
            they.can(MANAGE, PostsForJudgements, courses_id=entry.courses_id)
            they.can(READ, Groups, courses_id=entry.courses_id)
            they.can(READ, GroupsAndUsers, courses_id=entry.courses_id)
            they.can(READ, CoursesAndUsers, courses_id=entry.courses_id)
            they.can((CREATE, DELETE), CriteriaAndPostsForQuestions, courses_id=entry.courses_id)
            they.can(READ, USER_IDENTITY)
        # only students can submit judgements for now
        if entry.usertypeforcourse.name == UserTypesForCourse.TYPE_STUDENT:
            they.can(CREATE, Judgements, courses_id=entry.courses_id)


# Tell the client side about a user's permissions.
# This is necessarily more simplified than Flask-Bouncer's implementation.
# I'm hoping that we don't need fine grained permission checking to the
# level of individual entries. This is only going to be at a coarse level
# of models.
# Note that it looks like Flask-Bouncer judges a user to have permission
# on an model if they're allowed to operate on one instance of it.
# E.g.: A user who can only EDIT their own User object would have
# ensure(READ, Users) return True
def get_logged_in_user_permissions():
    user = Users.query.get(current_user.id)
    require(READ, user)
    dropped_id = UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_DROPPED).first().id
    courses = CoursesAndUsers.query.filter_by(users_id=current_user.id) \
        .filter(CoursesAndUsers.usertypesforcourse_id != dropped_id).all()
    admin = user.usertypeforsystem.name == "System Administrator"
    permissions = {}
    models = {
        Users.__name__: Users,
    }
    post_based_models = {
        PostsForQuestions.__name__: PostsForQuestions()
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
    permissions['Courses'] = {CREATE: {'global': allow(CREATE, Courses)}}
    mod_operations = {MANAGE, READ, EDIT, DELETE}
    for operation in mod_operations:
        permissions['Courses'].setdefault(operation, {})
        permissions['Courses'][operation]['global'] = admin
        for course in courses:
            course_id = str(course.courses_id)
            try:
                ensure(operation, Courses(id=course.courses_id))
                permissions['Courses'][operation][course_id] = True
                permissions['Courses'][operation]['global'] = True
            except Unauthorized:
                permissions['Courses'][operation][course_id] = False

    # post-based models
    for model_name, model in post_based_models.items():
        permissions.setdefault(model_name, {})
        for operation in operations:
            permissions[model_name].setdefault(operation, {})
            permissions[model_name][operation]['global'] = admin
            for course in courses:
                course_id = str(course.courses_id)
                try:
                    m = model
                    p = Posts(courses_id=course.courses_id)
                    setattr(m, 'post', p)
                    ensure(operation, m)
                    permissions[model_name][operation][course_id] = True
                    permissions[model_name][operation]['global'] = True
                except Unauthorized:
                    permissions[model_name][operation][course_id] = False

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
        enrolments = CoursesAndUsers.query.filter_by(users_id=user.id).all()
        # if the logged in user can edit the target user's enrolments, then we let them see full info
        for enrolment in enrolments:
            if allow(EDIT, enrolment):
                access_restricted = False
                break

    return access_restricted
