# Specify what columns should be sent out by the API
from flask.ext.restful import fields

class UnwrapSystemRole(fields.Raw):
    def format(self, system_role):
        return system_role.value

class UnwrapCourseRole(fields.Raw):
    def format(self, course_role):
        return course_role.value

class UnwrapAnswerCommentType(fields.Raw):
    def format(self, comment_type):
        return comment_type.value

def get_user(restrict_user=True):
    restricted = {
        'id': fields.Integer,
        'displayname': fields.String,
        'avatar': fields.String,
        'last_online': fields.DateTime,
        'created': fields.DateTime
    }
    if restrict_user:
        return restricted
    unrestricted = {
        'username': fields.String,
        'student_number': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'email': fields.String,
        'fullname': fields.String,
        'modified': fields.DateTime,
        'system_role': UnwrapSystemRole(attribute='system_role')
    }
    unrestricted.update(restricted)
    return unrestricted


def get_users_in_course(restrict_user=True):
    users = get_user(restrict_user)
    users['group_name'] = fields.String
    if not restrict_user:
        users['course_role'] = UnwrapCourseRole(attribute='course_role')
    return users


def get_course(include_details=True):
    data_format = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
    }
    if include_details:
        details = {
            'start_date': fields.DateTime,
            'end_date': fields.DateTime,
            'modified': fields.DateTime,
            'created': fields.DateTime
        }
        data_format.update(details)
    return data_format


def get_criterion():
    data_format = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'user_id': fields.Integer,
        'default': fields.Boolean,
        'compared': fields.Boolean,
        'modified': fields.DateTime,
        'created': fields.DateTime
    }
    return data_format


def get_assignment(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'user_id': fields.Integer,

        'name': fields.String,
        'description': fields.String,
        'number_of_comparisons': fields.Integer,

        'criteria': fields.List(fields.Nested(get_criterion())),
        'file': fields.Nested(get_file(), allow_null=True),

        'answer_start': fields.DateTime,
        'answer_end': fields.DateTime,
        'compare_start': fields.DateTime,
        'compare_end': fields.DateTime,
        'available': fields.Boolean,

        'students_can_reply': fields.Boolean,
        'enable_self_evaluation': fields.Boolean,

        'compared': fields.Boolean,

        'answer_period': fields.Boolean,
        'compare_period': fields.Boolean,
        'after_comparing': fields.Boolean,
        'evaluation_count': fields.Integer,
        'comment_count': fields.Integer,
        'answer_count': fields.Integer,
        'self_evaluation_count': fields.Integer,

        'user': {
            'id': fields.Integer(attribute="user_id"),
            'displayname': fields.String(attribute="user_displayname"),
            'avatar': fields.String(attribute="user_avatar"),
        },

        'modified': fields.DateTime,
        'created': fields.DateTime
    }
    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user_fullname")

    return ret

def get_answer(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'user_id': fields.Integer,

        'content': fields.String,
        'file': fields.Nested(get_file(), allow_null=True),
        'flagged': fields.Boolean,

        'scores': fields.List(fields.Nested(get_score())),
        'comment_count': fields.Integer,
        'private_comment_count': fields.Integer,
        'public_comment_count': fields.Integer,

        'user': {
            'id': fields.Integer(attribute="user_id"),
            'displayname': fields.String(attribute="user_displayname"),
            'avatar': fields.String(attribute="user_avatar"),
        },

        'created': fields.DateTime
    }
    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user_fullname")

    return ret


def get_assignment_comment(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'user_id': fields.Integer,

        'content': fields.String,

        'user': {
            'id': fields.Integer(attribute="user_id"),
            'displayname': fields.String(attribute="user_displayname"),
            'avatar': fields.String(attribute="user_avatar"),
        },

        'created': fields.DateTime,
    }
    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user_fullname")

    return ret


def get_answer_comment(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'answer_id': fields.Integer,
        'user_id': fields.Integer,
        'content': fields.String,
        'comment_type': UnwrapAnswerCommentType(attribute='comment_type'),

        'user': {
            'id': fields.Integer(attribute="user_id"),
            'displayname': fields.String(attribute="user_displayname"),
            'avatar': fields.String(attribute="user_avatar"),
        },
        'created': fields.DateTime,
    }
    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user_fullname")

    return ret


def get_file():
    return {
        'id': fields.Integer,
        'name': fields.String,
        'alias': fields.String
    }


def get_comparison(restrict_user=True, with_answers=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'criterion_id': fields.Integer,
        'user_id': fields.Integer,
        'answer1_id': fields.Integer,
        'answer2_id': fields.Integer,
        'winner_id': fields.Integer(default=None),

        'content': fields.String,
        'criterion': fields.Nested(get_criterion()),

        'user': {
            'id': fields.Integer(attribute="user_id"),
            'displayname': fields.String(attribute="user_displayname"),
            'avatar': fields.String(attribute="user_avatar"),
        },
        'created': fields.DateTime
    }
    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user_fullname")

    if with_answers:
        ret['answer1'] = fields.Nested(get_answer(
            restrict_user=restrict_user))
        ret['answer2'] = fields.Nested(get_answer(
            restrict_user=restrict_user))

    return ret

def get_comparison_set(restrict_user=True):
    ret = {
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'user_id': fields.Integer,

        'comparisons': fields.List(fields.Nested(get_comparison(
            restrict_user=restrict_user, with_answers=False))),

        'answer1_id': fields.Integer,
        'answer2_id': fields.Integer,
        'answer1': fields.Nested(get_answer()),
        'answer2': fields.Nested(get_answer()),

        'user': {
            'id': fields.Integer(attribute="user.id"),
            'displayname': fields.String(attribute="user.displayname"),
            'avatar': fields.String(attribute="user.avatar"),
        },

        'answer1_feedback': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'answer2_feedback': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'self_evaluation': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'created': fields.DateTime
    }

    if not restrict_user:
        ret['user']['fullname'] = fields.String(attribute="user.fullname")

    return ret

def get_import_users_results(restrict_user=True):
    user = get_user(restrict_user)
    return {
        'user': fields.Nested(user),
        'message': fields.String
    }


def get_score():
    return {
        'id': fields.Integer,
        'criterion_id': fields.Integer,
        'answer_id': fields.Integer,
        'normalized_score': fields.Integer
    }
