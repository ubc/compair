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
            'criteriaandcourses': fields.Nested(get_criteria_and_courses()),
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


def get_criteria_and_courses():
    data_format = {
        'id': fields.Integer,
        'criterion': fields.Nested(get_criteria()),
        'courses_id': fields.Integer,
        'active': fields.Boolean,
        'in_question': fields.Boolean
    }
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


def get_posts_for_answers(restrict_users=True, include_comments=True):
    post = get_posts(restrict_users)
    # comments = get_posts_for_answers_and_posts_for_comments(restrict_users)
    score = get_scores()
    del post['course']
    ret = {
        'id': fields.Integer,
        'content': fields.String,
        'files': fields.Nested(get_files_for_posts()),
        'created': fields.DateTime,
        'user_id': fields.Integer,
        'user_displayname': fields.String,
        'user_fullname': fields.String,
        'user_avatar': fields.String,
        'posts_id': fields.Integer,
        'scores': fields.Nested(score),
        'flagged': fields.Boolean,
        'questions_id': fields.Integer
    }
    # can see who flagged this post if user can view unrestricted data
    # it seems it is not being used for now
    # if not restrict_users:
    #     ret['flagger'] = fields.Nested(get_users(restrict_users))
    if include_comments:
        # ret['comments'] = fields.List(fields.Nested(comments))
        ret['comments_count'] = fields.Integer
        ret['private_comments_count'] = fields.Integer
        ret['public_comments_count'] = fields.Integer
    return ret


def get_posts_for_comments(retrict_users=True):
    post = get_posts(retrict_users)
    del post['course']
    return {
        'id': fields.Integer,
        'post': fields.Nested(post)
    }


def get_posts_for_questions_and_posts_for_comments(restrict_users=True):
    comment = get_posts_for_comments(restrict_users)
    return {
        'id': fields.Integer,
        'postsforcomments': fields.Nested(comment),
        'content': fields.String
    }


def get_posts_for_answers_and_posts_for_comments(restrict_users=True):
    comment = get_posts_for_comments(restrict_users)
    return {
        'id': fields.Integer,
        # 'postsforcomments': fields.Nested(comment),
        'selfeval': fields.Boolean,
        'evaluation': fields.Boolean,
        'type': fields.Integer,
        'course_id': fields.Integer,
        'content': fields.String,
        'files': fields.Nested(get_files_for_posts()),
        'created': fields.DateTime,
        'user_id': fields.Integer,
        'user_displayname': fields.String,
        'user_fullname': fields.String,
        'user_avatar': fields.String,
        'posts_id': fields.Integer
    }


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
        ret['answer1'] = fields.Nested(get_posts_for_answers(include_comments=False))
        ret['answer2'] = fields.Nested(get_posts_for_answers(include_comments=False))
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
    return {
        'user_id': fields.Integer,
        'name': fields.String,
        'avatar': fields.String,
        'criteriaandquestions_id': fields.Integer,
        'answerpairings_id': fields.Integer,
        'content': fields.String,
        'selfeval': fields.Boolean,
        'created': fields.DateTime,
        'answer1': fields.Nested(answer),
        'answer2': fields.Nested(answer),
        'winner': fields.Integer
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
