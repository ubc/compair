from operator import attrgetter
from itertools import groupby

from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from bouncer.constants import READ, EDIT, CREATE, MANAGE
from sqlalchemy.orm import load_only, joinedload, contains_eager
from sqlalchemy.sql.expression import and_, or_

from . import dataformat
from acj.core import db, event
from acj.models import Judgements, PostsForComments, PostsForJudgements, Courses, PostsForQuestions, Posts, \
    AnswerPairings, CoursesAndUsers, CriteriaAndPostsForQuestions, Users, \
    PostsForAnswersAndPostsForComments
from acj.util import new_restful_api, pagination_parser
from .authorization import allow, require

evalcomments_api = Blueprint('evalcomments_api', __name__)
api = new_restful_api(evalcomments_api)


def judgement_type(value):
    return dict(value)


new_comment_parser = RequestParser()
new_comment_parser.add_argument('judgements', type=judgement_type, required=True, action='append')
new_comment_parser.add_argument('selfeval', type=bool, required=False, default=False)

comment_list_parser = pagination_parser.copy()
comment_list_parser.add_argument('group', type=int, required=False, default=None)
comment_list_parser.add_argument('author', type=int, required=False, default=None)

# events
on_evalcomment_create = event.signal('EVALCOMMENT_CREATE')
on_evalcomment_get = event.signal('EVALCOMMENT_GET')
on_evalcomment_view = event.signal('EVALCOMMENT_VIEW')
on_evalcomment_view_my = event.signal('EVALCOMMENT_VIEW_MY')


# /
class EvalCommentRootAPI(Resource):
    @login_required
    def get(self, course_id, question_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        post = Posts(courses_id=course_id)
        comment = PostsForComments(post=post)
        judgement_comment = PostsForJudgements(postsforcomments=comment)
        require(MANAGE, judgement_comment)
        comments = PostsForJudgements.query \
            .join(Judgements, AnswerPairings).filter_by(questions_id=question_id) \
            .join(PostsForComments, Posts, Users).order_by(Users.firstname, Users.lastname, Users.id).all()
        restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course_id))

        on_evalcomment_get.send(
            self,
            event_name=on_evalcomment_get.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id}
        )

        return {'comments': marshal(comments, dataformat.get_posts_for_judgements(restrict_users))}

    @login_required
    def post(self, course_id, question_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        question = PostsForQuestions(post=Posts(courses_id=course_id))
        criteria_and_questions = CriteriaAndPostsForQuestions(question=question)
        judgements = Judgements(question_criterion=criteria_and_questions)
        require(CREATE, judgements)
        params = new_comment_parser.parse_args()
        results = []
        for judgement in params['judgements']:
            judge = Judgements.query.get_or_404(judgement['id'])
            post = Posts(courses_id=course_id)
            post.content = judgement['comment']
            post.users_id = current_user.id
            comment = PostsForComments(post=post)
            selfeval = params.get('selfeval', False)
            evalcomment = PostsForJudgements(postsforcomments=comment, judgements_id=judge.id, selfeval=selfeval)
            db.session.add(post)
            db.session.add(comment)
            db.session.add(evalcomment)
            db.session.commit()
            results.append(evalcomment)

        on_evalcomment_create.send(
            self,
            event_name=on_evalcomment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(results, dataformat.get_posts_for_judgements(False)))

        return {'objects': marshal(results, dataformat.get_posts_for_judgements())}


api.add_resource(EvalCommentRootAPI, '')


# /view
class EvalCommentViewAPI(Resource):
    @login_required
    def get(self, course_id, question_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        question = PostsForQuestions(post=Posts(courses_id=course_id))
        require(READ, question)
        comment = PostsForComments(post=Posts(courses_id=course_id))
        can_manage = allow(MANAGE, PostsForJudgements(postsforcomments=comment))

        params = comment_list_parser.parse_args()

        # find out the user_id and pairing_id combination on current page
        # aggregate on those id pairs so that we have accurate per page judgement number
        pair_query = Judgements.query. \
            with_entities(Judgements.users_id, Judgements.answerpairings_id). \
            join(AnswerPairings).filter_by(questions_id=question_id). \
            group_by(Judgements.users_id, Judgements.answerpairings_id)

        # this if block also acts as access control because a non-privileged user will be caught in the first if.
        if not can_manage:
            pair_query = pair_query.filter(Judgements.users_id == current_user.id)
        elif params['author']:
            pair_query = pair_query.filter(Judgements.users_id == params['author'])
        elif params['group']:
            subquery = Users.query.with_entities(Users.id).join(Users.groups).filter_by(
                groups_id=params['group']).subquery()
            pair_query = pair_query.filter(Judgements.users_id.in_(subquery))

        page = pair_query.paginate(params['page'], params['perPage'])

        judgements = []

        if page.total:
            # build condition based on ids
            conditions = []
            for user_id, pairing_id in page.items:
                conditions.append(and_(Judgements.users_id == user_id, Judgements.answerpairings_id == pairing_id))

            # retrieve judgements for each criterion, if there is multiple criteria,
            # len(criteria_judgements) > params['perPage'], we will consolidate them into judgement list with feedback
            criteria_judgements = Judgements.query. \
                options(joinedload('comment').joinedload('postsforcomments').joinedload('post').joinedload('files')). \
                options(joinedload('user')). \
                options(joinedload('answerpairing')). \
                filter(or_(*conditions)). \
                order_by(Judgements.users_id, Judgements.answerpairings_id). \
                all()

            # compile the conditions for feedback
            feedback_conditions = []
            for criteria_judgement in criteria_judgements:
                feedback_conditions.append(
                    and_(Posts.users_id == criteria_judgement.users_id,
                         or_(PostsForAnswersAndPostsForComments.answers_id == criteria_judgement.answerpairing.answers_id1,
                             PostsForAnswersAndPostsForComments.answers_id == criteria_judgement.answerpairing.answers_id2,
                             )
                         )
                )
            # retrieve feedback for answers, it will be one feedback for an answer per user
            feedback = PostsForAnswersAndPostsForComments.query. \
                options(contains_eager('postsforcomments').contains_eager('post')). \
                join(PostsForComments). \
                join(PostsForComments.post). \
                filter(or_(*feedback_conditions)). \
                all()

            # now let's build judgements list, which has the following structure
            # judgements = [
            #   criteria_judgements = [
            #       judgement1 (for criterion 1),
            #       judgement2 (for criterion 2),
            #       judgement3 (for criterion 3),
            #   ],
            #   user_id,
            #   name,
            #   avatar,
            #   answer1 = {id: id, feedback: feedback}
            #   answer2 = {id: id, feedback: feedback}
            #   created,
            #   selfeval = [
            #       selfeval1,
            #       selfeval2,
            #   ],
            # ]
            def get_feedback(u_id, answer_id, feedback_list):
                return next(
                    iter([l.postsforcomments.content for l in feedback_list if
                          l.users_id == u_id and l.answers_id == answer_id]),
                    None)

            for (user_id, pairing_id), g in groupby(criteria_judgements, attrgetter('users_id', 'answerpairings_id')):
                group = list(g)
                j = group[0]
                judgement = {
                    'criteria_judgements': [convert_judgement(j) for j in group],
                    'user_id': user_id,
                    'name': j.user.fullname if j.user.fullname else j.user.displayname,
                    'avatar': j.user.avatar,
                    'answer1': {'id': j.answerpairing.answers_id1,
                                'feedback': get_feedback(user_id, j.answerpairing.answers_id1, feedback)},
                    'answer2': {'id': j.answerpairing.answers_id2,
                                'feedback': get_feedback(user_id, j.answerpairing.answers_id2, feedback)},
                    'created': j.created,
                    'selfeval': [{'content': f.postsforcomments.content} for f in feedback if
                                 f.users_id == user_id and f.selfeval]
                }
                judgements.append(judgement)

        on_evalcomment_view.send(
            self,
            event_name=on_evalcomment_view.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id}
        )

        return {'objects': marshal(judgements, dataformat.get_eval_comments()), "page": page.page,
                "pages": page.pages, "total": page.total, "per_page": page.per_page}


def convert_judgement(judgement):
    """
    Convert judgement object into a dict with reduced attributes. The dict is intented to be used in
    aggregate criteria judgement dictionary

    :param judgement: judgement DB object
    :return: dict
    """
    return {
        'content': judgement.comment.content if judgement.comment else None,
        'criteriaandquestions_id': judgement.criteriaandquestions_id,
        'winner': judgement.answers_id_winner,
    }


api.add_resource(EvalCommentViewAPI, '/view')
