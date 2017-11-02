# Specify what columns should be sent out by the API
from flask_restful import fields
import pytz

def replace_tzinfo(datetime):
    return datetime.replace(tzinfo=pytz.utc) if datetime else None

class UnwrapEnum(fields.Raw):
    def format(self, enum):
        return enum.value if enum != None else None

def get_partial_user(restrict_user=True):
    ret = {
        'id': fields.String(attribute="user_uuid"),
        'displayname': fields.String(attribute="user_displayname"),
        'avatar': fields.String(attribute="user_avatar"),
    }
    if not restrict_user:
        ret['fullname'] = fields.String(attribute="user_fullname")
        ret['fullname_sortable'] = fields.String(attribute="user_fullname_sortable")

    return ret

def get_user(restrict_user=True):
    restricted = {
        'id': fields.String(attribute="uuid"),
        'displayname': fields.String,
        'avatar': fields.String,
        'last_online': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.last_online)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
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
        'fullname_sortable': fields.String,
        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'system_role': UnwrapEnum(attribute='system_role'),
        'email_notification_method': UnwrapEnum(attribute='email_notification_method'),
        'uses_compair_login': fields.Boolean
    }
    unrestricted.update(restricted)
    return unrestricted


def get_users_in_course(restrict_user=True):
    users = get_user(restrict_user)
    users['group_name'] = fields.String
    if not restrict_user:
        users['course_role'] = UnwrapEnum(attribute='course_role')
        users['cas_username'] = fields.String
    return users


def get_course():
    return {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'year': fields.Integer,
        'term': fields.String,
        'sandbox': fields.Boolean,
        'start_date': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.start_date)),
        'end_date': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.end_date)),
        'available': fields.Boolean,
        'lti_linked': fields.Boolean,
        'assignment_count': fields.Integer,
        'student_assignment_count': fields.Integer,
        'student_count': fields.Integer,
        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }


def get_user_courses():
    courses = get_course()
    courses['group_name'] = fields.String
    courses['course_role'] = UnwrapEnum(attribute='course_role')
    return courses

def get_criterion(with_weight=False):
    ret = {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'description': fields.String,
        'user_id': fields.String(attribute="user_uuid"),
        'public': fields.Boolean,
        'default': fields.Boolean,
        'compared': fields.Boolean,
        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

    if with_weight:
        ret['weight'] = fields.Integer

    return ret


def get_assignment(restrict_user=True):
    return {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'user_id': fields.String(attribute="user_uuid"),

        'name': fields.String,
        'description': fields.String,
        'peer_feedback_prompt': fields.String(default=None),
        'number_of_comparisons': fields.Integer,
        'total_comparisons_required': fields.Integer,
        'total_steps_required': fields.Integer,

        'criteria': fields.List(fields.Nested(get_criterion(with_weight=True))),
        'file': fields.Nested(get_file(), allow_null=True),

        'answer_start': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.answer_start)),
        'answer_end': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.answer_end)),
        'compare_start': fields.DateTime(dt_format='iso8601', default=None, attribute=lambda x: replace_tzinfo(x.compare_start)),
        'compare_end': fields.DateTime(dt_format='iso8601', default=None, attribute=lambda x: replace_tzinfo(x.compare_end)),
        'available': fields.Boolean,

        'students_can_reply': fields.Boolean,
        'enable_self_evaluation': fields.Boolean,
        'pairing_algorithm': UnwrapEnum(attribute='pairing_algorithm'),
        'educators_can_compare': fields.Boolean,
        'rank_display_limit': fields.Integer(default=None),

        'compared': fields.Boolean,

        'lti_course_linked': fields.Boolean,
        'lti_linked': fields.Boolean,

        'answer_period': fields.Boolean,
        'compare_period': fields.Boolean,
        'after_comparing': fields.Boolean,
        'evaluation_count': fields.Integer,
        'comment_count': fields.Integer,
        'answer_count': fields.Integer,
        'top_answer_count': fields.Integer,
        'self_evaluation_count': fields.Integer,

        'user': get_partial_user(restrict_user),

        'answer_grade_weight': fields.Integer,
        'comparison_grade_weight': fields.Integer,
        'self_evaluation_grade_weight': fields.Integer,

        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

def get_answer(restrict_user=True):
    return {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'user_id': fields.String(attribute="user_uuid"),

        'content': fields.String,
        'file': fields.Nested(get_file(), allow_null=True),
        'flagged': fields.Boolean,
        'draft': fields.Boolean,
        'top_answer': fields.Boolean,

        'score': fields.Nested(get_score(restrict_user=restrict_user), allow_null=True),

        'comment_count': fields.Integer,
        'private_comment_count': fields.Integer,
        'public_comment_count': fields.Integer,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }


def get_assignment_comment(restrict_user=True):
    return {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'content': fields.String,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }


def get_answer_comment(restrict_user=True):
    return {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'answer_id': fields.String(attribute="answer_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'content': fields.String,
        'comment_type': UnwrapEnum(attribute='comment_type'),
        'draft': fields.Boolean,

        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }


def get_file():
    return {
        'id': fields.String(attribute="uuid"),
        'name': fields.String,
        'alias': fields.String,
        'extension': fields.String,
        'mimetype': fields.String,
        'kaltura_media': fields.Nested(get_kaltura_media(), allow_null=True)
    }

def get_kaltura_media():
    return {
        'partner_id': fields.Integer,
        'player_id': fields.Integer,
        'entry_id': fields.String,
        'service_url': fields.String,
        #'download_url': fields.String, #currently no reason to expose download url
        'media_type': fields.Integer,
        'show_recent_warning': fields.Boolean
    }


def get_comparison(restrict_user=True, with_answers=True, with_feedback=False):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'answer1_id': fields.String(attribute="answer1_uuid"),
        'answer2_id': fields.String(attribute="answer2_uuid"),
        'user_id': fields.String(attribute="user_uuid"),
        'winner': UnwrapEnum(attribute='winner'),

        'comparison_criteria': fields.List(fields.Nested(get_comparison_criterion())),
        'user': get_partial_user(restrict_user),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

    if with_answers:
        ret['answer1'] = fields.Nested(get_answer(
            restrict_user=restrict_user))
        ret['answer2'] = fields.Nested(get_answer(
            restrict_user=restrict_user))

    if with_feedback:
        ret['answer1_feedback'] = fields.List(fields.Nested(get_answer_comment(restrict_user)))
        ret['answer2_feedback'] = fields.List(fields.Nested(get_answer_comment(restrict_user)))

    return ret

def get_comparison_set(restrict_user=True, with_user=True):
    ret = {
        'comparisons': fields.List(fields.Nested(get_comparison(restrict_user, True, True))),
        'self_evaluations': fields.List(fields.Nested(get_answer_comment(restrict_user)))
    }

    if with_user:
        ret['user'] = fields.Nested(get_user(restrict_user))

    return ret

def get_comparison_criterion():
    return {
        'id': fields.String(attribute="uuid"),
        'criterion_id': fields.String(attribute="criterion_uuid"),
        'content': fields.String,
        'winner': UnwrapEnum(attribute='winner'),

        'criterion': fields.Nested(get_criterion()),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

def get_comparison_example(with_answers=True):
    ret = {
        'id': fields.String(attribute="uuid"),
        'course_id': fields.String(attribute="course_uuid"),
        'assignment_id': fields.String(attribute="assignment_uuid"),
        'answer1_id': fields.String(attribute="answer1_uuid"),
        'answer2_id': fields.String(attribute="answer2_uuid"),
        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

    if with_answers:
        ret['answer1'] = fields.Nested(get_answer(
            restrict_user=False))
        ret['answer2'] = fields.Nested(get_answer(
            restrict_user=False))

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

def get_gradebook(include_scores=False, include_self_evaluation=False):
    ret = {
        'user': fields.Nested(get_user(restrict_user=False)),
        'num_answers': fields.Integer,
        'num_comparisons': fields.Integer,
        'grade': fields.Float,
        'flagged': fields.String,
        'file': fields.Nested(get_file(), allow_null=True),
    }

    if include_scores:
        ret['score'] = fields.Raw

    if include_self_evaluation:
        ret['num_self_evaluation'] = fields.Integer

    return ret

def get_lti_consumer(include_sensitive=False):
    ret = {
        'id': fields.String(attribute="uuid"),
        'oauth_consumer_key': fields.String,
        'user_id_override': fields.String,
        'active': fields.Boolean,
        'modified': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.modified)),
        'created': fields.DateTime(dt_format='iso8601', attribute=lambda x: replace_tzinfo(x.created))
    }

    if include_sensitive:
        ret['oauth_consumer_secret'] = fields.String

    return ret