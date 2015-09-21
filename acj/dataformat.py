# Specify what columns should be sent out by the API
from flask.ext.restful import fields


def get_user_types_for_course():
    return {
        'id': fields.Integer,
        'name': fields.String
    }


def get_user_types_for_system():
    return {
        'id': fields.Integer,
        'name': fields.String
    }


def get_users(restrict_users=True):
    restricted = {
        'id': fields.Integer,
        'displayname': fields.String,
        'avatar': fields.String,
        'lastonline': fields.DateTime,
        'created': fields.DateTime
    }
    if restrict_users:
        return restricted
    unrestricted = {
        'username': fields.String,
        'student_no': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'email': fields.String,
        'fullname': fields.String,
        'modified': fields.DateTime,
        'usertypesforsystem_id': fields.Integer,
        'usertypeforsystem': fields.Nested(get_user_types_for_system()),
        'system_role': fields.String
    }
    unrestricted.update(restricted)
    return unrestricted


def get_users_in_course(restrict_users=True):
    users = get_users(restrict_users)
    users['group_id'] = fields.Integer
    if not restrict_users:
        users['course_role'] = fields.String
    return users


def get_courses(include_details=True):
    data_format = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String
    }
    if include_details:
        details = {
            'available': fields.Boolean,
            # 'criteriaandcourses': fields.Nested(get_criteria_in_course()),
            'enable_student_create_questions': fields.Boolean,
            'enable_student_create_tags': fields.Boolean,
            'modified': fields.DateTime,
            'created': fields.DateTime
        }
        data_format.update(details)
    return data_format


def get_courses_and_users(restrict_user=True, include_user=True, include_groups=True):
    data_format = {
        'id': fields.Integer,
        'courses_id': fields.Integer,
        'usertypeforcourse': fields.Nested(get_user_types_for_course()),
        'modified': fields.DateTime,
        'created': fields.DateTime
    }
    if include_user:
        data_format['user'] = fields.Nested(get_users(restrict_user))
    if include_groups:
        data_format['groups'] = fields.Nested(get_groups_and_users())
    return data_format


def get_groups_and_users(restrict_user=True):
    data_format = {
        'groups_id': fields.Integer,
        'groups_name': fields.String
    }

    if not restrict_user:
        data_format['user'] = fields.Nested(get_users(restrict_user))
    return data_format


def get_groups():
    data_format = {
        'id': fields.Integer,
        'name': fields.String
    }
    return data_format


def get_criteria():
    data_format = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'modified': fields.DateTime,
        'created': fields.DateTime,
        'users_id': fields.Integer,
        'default': fields.Boolean,
        'judged': fields.Boolean
    }
    return data_format


def get_criteria_in_course():
    data_format = get_criteria()
    data_format.update({
        'course_id': fields.Integer(attribute=lambda x: x.course_assoc.courses_id),
        'active': fields.Boolean(attribute=lambda x: x.course_assoc.active),
        'in_question': fields.Boolean(attribute=lambda x: x.course_assoc.in_question)
    })
    return data_format


def get_criteria_and_posts_for_questions():
    data_format = {
        'id': fields.Integer,
        'criterion': fields.Nested(get_criteria()),
        'active': fields.Boolean
    }
    return data_format


def get_posts(restrict_users=True):
    return {
        'id': fields.Integer,
        'user': fields.Nested(get_users(restrict_users)),
        'course': fields.Nested(get_courses()),
        'content': fields.String,
        'modified': fields.DateTime,
        'created': fields.DateTime,
        'files': fields.Nested(get_files_for_posts())
    }


def get_posts_for_questions(restrict_users=True, include_answers=True):
    post = get_posts(restrict_users)
    del post['course']
    ret = {
        'id': fields.Integer,
        'post': fields.Nested(post),
        'title': fields.String,
        'answers_count': fields.Integer,
        'modified': fields.DateTime,
        'comments_count': fields.Integer,
        'available': fields.Boolean,
        'criteria': fields.Nested(get_criteria_and_posts_for_questions()),
        'answer_period': fields.Boolean,
        'judging_period': fields.Boolean,
        'after_judging': fields.Boolean,
        'answer_start': fields.DateTime,
        'answer_end': fields.DateTime,
        'judge_start': fields.DateTime,
        'judge_end': fields.DateTime,
        'can_reply': fields.Boolean,
        'num_judgement_req': fields.Integer,
        'selfevaltype_id': fields.Integer,
        'judged': fields.Boolean,
        'evaluation_count': fields.Integer
    }
    if include_answers:
        answer = get_posts_for_answers(restrict_users)
        ret['answers'] = fields.List(fields.Nested(answer))
    return ret


def get_posts_for_answers(restrict_users=True):
    score = get_scores()
    ret = {
        'id': fields.Integer,
        'content': fields.String,
        'files': fields.Nested(get_files_for_posts()),
        'created': fields.DateTime,
        'user_id': fields.Integer,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'posts_id': fields.Integer,
        'scores': fields.Nested(score),
        'flagged': fields.Boolean,
        'questions_id': fields.Integer,
        'comments_count': fields.Integer,
        'private_comments_count': fields.Integer,
        'public_comments_count': fields.Integer
    }
    if not restrict_users:
        ret.update({'user_fullname': fields.String})

    return ret


def get_posts_for_comments(restrict_users=True):
    post = get_posts(restrict_users)
    del post['course']
    return {
        'id': fields.Integer,
        'post': fields.Nested(post)
    }


def get_posts_for_comments_new(restrict_users=True):
    """
    new data format for comments. Should deprecate the old one.
    """
    ret = {
        'id': fields.Integer,
        'content': fields.String,
        'created': fields.DateTime,
        'user_id': fields.Integer,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
    }
    if not restrict_users:
        ret.update({'user_fullname': fields.String})
    return ret


def get_answer_comment(restrict_users=True):
    ret = get_posts_for_comments_new(restrict_users)
    ret.update({
        'selfeval': fields.Boolean,
        'evaluation': fields.Boolean,
        'type': fields.Integer,
        'course_id': fields.Integer,
    })

    return ret


def get_posts_for_answers_and_posts_for_comments(restrict_users=True):
    ret = {
        'id': fields.Integer,
        'selfeval': fields.Boolean,
        'evaluation': fields.Boolean,
        'type': fields.Integer,
        'course_id': fields.Integer,
        'comments_id': fields.Integer,
        'content': fields.String,
        'files': fields.Nested(get_files_for_posts()),
        'created': fields.DateTime,
        'user_id': fields.Integer,
        'user_displayname': fields.String,
        'user_avatar': fields.String,
        'posts_id': fields.Integer
    }
    if not restrict_users:
        ret.update({'user_fullname': fields.String})
    return ret


def get_files_for_posts():
    return {
        'id': fields.Integer,
        'posts_id': fields.Integer,
        'name': fields.String,
        'alias': fields.String
    }


def get_selfeval_types():
    return {
        'id': fields.Integer,
        'name': fields.String
    }


def get_answer_pairings(include_answers=False):
    ret = {
        'id': fields.Integer,
        'questions_id': fields.Integer,
        'answers_id1': fields.Integer,
        'answers_id2': fields.Integer
    }
    if include_answers:
        ret['answer1'] = fields.Nested(get_posts_for_answers())
        ret['answer2'] = fields.Nested(get_posts_for_answers())
    return ret


def get_judgements():
    return {
        'id': fields.Integer,
        'answerpairing': fields.Nested(get_answer_pairings()),
        'users_id': fields.Integer,
        'answers_id_winner': fields.Integer,
        'question_criterion': fields.Nested(get_criteria_and_posts_for_questions())
    }


def get_posts_for_judgements(restrict_users=True):
    judgement = get_judgements()
    comment = get_posts_for_comments(restrict_users)
    return {
        'postsforcomments': fields.Nested(comment),
        'judgement': fields.Nested(judgement)
    }


def get_import_users_results(restrict_users=True):
    user = get_users(restrict_users)
    return {
        'user': fields.Nested(user),
        'message': fields.String
    }


def get_eval_comments():
    answer = {'id': fields.Integer, 'feedback': fields.String}
    criteria_judgement = {'content': fields.String, 'criteriaandquestions_id': fields.Integer, 'winner': fields.Integer}
    selfeval = {'content': fields.String}
    return {
        'user_id': fields.Integer,
        'name': fields.String,
        'avatar': fields.String,
        'criteria_judgements': fields.Nested(criteria_judgement),
        'selfeval': fields.Nested(selfeval),
        'created': fields.DateTime,
        'answer1': fields.Nested(answer),
        'answer2': fields.Nested(answer),
    }


def get_scores():
    return {
        'id': fields.Integer,
        'criteriaandquestions_id': fields.Integer,
        'answers_id': fields.Integer,
        'rounds': fields.Integer,
        'wins': fields.Integer,
        'score': fields.Float,
        'normalized_score': fields.Integer
    }
