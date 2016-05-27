# Specify what columns should be sent out by the API
from flask.ext.restful import fields

class UnwrapSystemRole(fields.Raw):
    def format(self, system_role):
        return system_role.value
        
class UnwrapCourseRole(fields.Raw):
    def format(self, course_role):
        return course_role.value

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


def get_criteria():
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


def get_assignment_criteria():
    data_format = {
        'id': fields.Integer,
        'active': fields.Boolean,
        'criterion': fields.Nested(get_criteria())
    }
    return data_format


def get_assignment(restrict_user=True):
    return {
        'id': fields.Integer,
        'user_id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'criteria': fields.Nested(get_assignment_criteria()),
        'file': fields.Nested(get_file()),
        'answer_start': fields.DateTime,
        'answer_end': fields.DateTime,
        'compare_start': fields.DateTime,
        'compare_end': fields.DateTime,
        'students_can_reply': fields.Boolean,
        'enable_self_eval': fields.Boolean,
        'number_of_comparisons': fields.Integer,
        'available': fields.Boolean,
        'answer_period': fields.Boolean,
        'compare_period': fields.Boolean,
        'after_comparing': fields.Boolean,
        'compared': fields.Boolean,
        'evaluation_count': fields.Integer,
        'comments_count': fields.Integer,
        'answers_count': fields.Integer,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'modified': fields.DateTime,
        'created': fields.DateTime
    }
    if not restrict_user:
        ret.update({'user_fullname': fields.String})
    

def get_answer(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'user_id': fields.Integer,
        'content': fields.String,
        'file': fields.Nested(get_file()),
        'flagged': fields.Boolean,
        'scores': fields.Nested(get_score()),
        'comments_count': fields.Integer,
        'private_comments_count': fields.Integer,
        'public_comments_count': fields.Integer,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'created': fields.DateTime
    }
    if not restrict_user:
        ret.update({'user_fullname': fields.String})

    return ret


def get_assignment_comment(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'user_id': fields.Integer,
        'content': fields.String,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'created': fields.DateTime,
    }
    if not restrict_user:
        ret.update({'user_fullname': fields.String})
    return ret


def get_answer_comment(restrict_user=True):
    ret = {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'answer_id': fields.Integer,
        'user_id': fields.Integer,
        'content': fields.String,
        'private': fields.Boolean,
        'self_eval': fields.Boolean,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'created': fields.DateTime,
    }
    if not restrict_user:
        ret.update({'user_fullname': fields.String})
    return ret


def get_file():
    return {
        'id': fields.Integer,
        'name': fields.String,
        'alias': fields.String
    }


def get_comparison(restrict_user=True):
    return {
        'id': fields.Integer,
        'course_id': fields.Integer,
        'assignment_id': fields.Integer,
        'criteria_id': fields.Integer,
        'user_id': fields.Integer,
        'answer1_id': fields.Integer,
        'answer2_id': fields.Integer,
        'winner_id': fields.Integer,
        'content': fields.String,
        'answer1': fields.Nested(get_answer()),
        'answer2': fields.Nested(get_answer()),
        'criterion': fields.Nested(get_criteria()),
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'created': fields.DateTime
    }
    if not restrict_user:
        ret.update({'user_fullname': fields.String})


def get_import_users_results(restrict_user=True):
    user = get_user(restrict_user)
    return {
        'user': fields.Nested(user),
        'message': fields.String
    }


def get_score():
    return {
        'id': fields.Integer,
        'criteria_id': fields.Integer,
        'answer_id': fields.Integer,
        'rounds': fields.Integer,
        'wins': fields.Integer,
        'score': fields.Float,
        'normalized_score': fields.Integer
    }
