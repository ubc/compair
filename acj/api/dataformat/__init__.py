# Specify what columns should be sent out by the API
from flask_restful import fields

class UnwrapSystemRole(fields.Raw):
    def format(self, system_role):
        return system_role.value

class UnwrapCourseRole(fields.Raw):
    def format(self, course_role):
        return course_role.value

class UnwrapAnswerCommentType(fields.Raw):
    def format(self, comment_type):
        return comment_type.value

class UnwrapPairingAlgorithm(fields.Raw):
    def format(self, pairing_algorithm):
        return pairing_algorithm.value

def get_partial_user(restrict_user=True):
    ret = {
        'id': fields.String(attribute="user_uuid"),
        'displayname': fields.String(attribute="user_displayname"),
        'avatar': fields.String(attribute="user_avatar"),
    }
    if not restrict_user:
        ret['fullname'] = fields.String(attribute="user_fullname")

    return ret

def get_user(restrict_user=True):
    restricted = {
        'id': fields.String(attribute="uuid"),
        'displayname': fields.String,
        'avatar': fields.String,
        'last_online': fields.DateTime(dt_format='iso8601'),
        'created': fields.DateTime(dt_format='iso8601')
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
        'modified': fields.DateTime(dt_format='iso8601'),
        'system_role': UnwrapSystemRole(attribute='system_role'),
        'uses_acj_login': fields.Boolean
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
    return {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'year': fields.Integer,
        'term': fields.String,
        'description': fields.String,
        'start_date': fields.DateTime(dt_format='iso8601'),
        'end_date': fields.DateTime(dt_format='iso8601'),
        'available': fields.Boolean,
        'lti_linked': fields.Boolean,
        'modified': fields.DateTime(dt_format='iso8601'),
        'created': fields.DateTime(dt_format='iso8601')
    }

def get_criterion():
    data_format = {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'description': fields.String,
        'user_id': fields.String(attribute="user_uuid"),
        'public': fields.Boolean,
        'default': fields.Boolean,
        'compared': fields.Boolean,
        'modified': fields.DateTime(dt_format='iso8601'),
        'created': fields.DateTime(dt_format='iso8601')
    }
    return data_format


def get_assignment(restrict_user=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'user_id': fields.String(attribute="user_uuid"),

        'name': fields.String,
        'description': fields.String,
        'number_of_comparisons': fields.Integer,
        'total_comparisons_required': fields.Integer,
        'total_steps_required': fields.Integer,

        'criteria': fields.List(fields.Nested(get_criterion())),
        'file': fields.Nested(get_file(), allow_null=True),

        'answer_start': fields.DateTime(dt_format='iso8601'),
        'answer_end': fields.DateTime(dt_format='iso8601'),
        'compare_start': fields.DateTime(dt_format='iso8601'),
        'compare_end': fields.DateTime(dt_format='iso8601'),
        'available': fields.Boolean,

        'students_can_reply': fields.Boolean,
        'enable_self_evaluation': fields.Boolean,
        'pairing_algorithm': UnwrapPairingAlgorithm(attribute='pairing_algorithm'),
        'rank_display_limit': fields.Integer(default=None),

        'compared': fields.Boolean,

        'lti_linkable': fields.Boolean,

        'answer_period': fields.Boolean,
        'compare_period': fields.Boolean,
        'after_comparing': fields.Boolean,
        'evaluation_count': fields.Integer,
        'comment_count': fields.Integer,
        'answer_count': fields.Integer,
        'self_evaluation_count': fields.Integer,

        'user': get_partial_user(restrict_user),

        'modified': fields.DateTime(dt_format='iso8601'),
        'created': fields.DateTime(dt_format='iso8601')
    }

    return ret

def get_answer(restrict_user=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'user_id': fields.String(attribute="user_uuid"),

        'content': fields.String,
        'file': fields.Nested(get_file(), allow_null=True),
        'flagged': fields.Boolean,
        'draft': fields.Boolean,

        'scores': fields.List(fields.Nested(get_score(
            restrict_user=restrict_user
        ))),
        'comment_count': fields.Integer,
        'private_comment_count': fields.Integer,
        'public_comment_count': fields.Integer,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601')
    }

    return ret


def get_assignment_comment(restrict_user=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'content': fields.String,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601'),
    }

    return ret


def get_answer_comment(restrict_user=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'answer_id': fields.String(attribute="answer_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'content': fields.String,
        'comment_type': UnwrapAnswerCommentType(attribute='comment_type'),
        'draft': fields.Boolean,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601'),
    }

    return ret


def get_file():
    return {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'alias': fields.String
    }


def get_comparison(restrict_user=True, with_answers=True):
    ret = {
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'criterion_id': fields.String(attribute="criterion_uuid"),
        'answer1_id': fields.String(attribute="answer1_uuid"),
        'answer2_id': fields.String(attribute="answer2_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'winner_id': fields.String(attribute="winner_uuid", default=None),

        'content': fields.String,
        'criterion': fields.Nested(get_criterion()),

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601')
    }

    if with_answers:
        ret['answer1'] = fields.Nested(get_answer(
            restrict_user=restrict_user))
        ret['answer2'] = fields.Nested(get_answer(
            restrict_user=restrict_user))

    return ret

def get_comparison_example(with_answers=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'answer1_id': fields.String(attribute="answer1_uuid"),
        'answer2_id': fields.String(attribute="answer2_uuid"),
        'modified': fields.DateTime(dt_format='iso8601'),
        'created': fields.DateTime(dt_format='iso8601')
    }

    if with_answers:
        ret['answer1'] = fields.Nested(get_answer(
            restrict_user=False))
        ret['answer2'] = fields.Nested(get_answer(
            restrict_user=False))

    return ret

def get_comparison_set(restrict_user=True):
    ret = {
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'user_id': fields.String(attribute="user_uuid"),

        'comparisons': fields.List(fields.Nested(get_comparison(
            restrict_user=restrict_user, with_answers=False
        ))),

        'answer1_id': fields.String(attribute="answer1_uuid"),
        'answer2_id': fields.String(attribute="answer2_uuid"),
        'answer1': fields.Nested(get_answer()),
        'answer2': fields.Nested(get_answer()),

        'user': get_partial_user(restrict_user),

        'answer1_feedback': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'answer2_feedback': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'self_evaluation': fields.List(fields.Nested(get_answer_comment(restrict_user))),
        'created': fields.DateTime(dt_format='iso8601')
    }

    return ret

def get_import_users_results(restrict_user=True):
    return {
        'user': fields.Nested(get_user(restrict_user)),
        'message': fields.String
    }


def get_score(restrict_user=True):
    ret = {
        'criterion_id': fields.String(attribute="criterion_uuid"),
        'rank': fields.Integer
    }
    if not restrict_user:
        ret['normalized_score'] = fields.Integer

    return ret