from bouncer.constants import CREATE, READ, EDIT, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, abort
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import and_, or_
from sqlalchemy.orm import load_only, joinedload, contains_eager

from . import dataformat
from acj.core import db
from acj.authorization import require, allow, USER_IDENTITY
from acj.core import event
from acj.models import Posts, PostsForComments, PostsForAnswers, \
    PostsForQuestions, Courses, PostsForQuestionsAndPostsForComments, \
    PostsForAnswersAndPostsForComments, UserTypesForCourse, UserTypesForSystem
from .util import new_restful_api, get_model_changes, pagination_parser

commentsforquestions_api = Blueprint('commentsforquestions_api', __name__)
apiQ = new_restful_api(commentsforquestions_api)

commentsforanswers_api = Blueprint('commentsforanswers_api', __name__)
apiA = new_restful_api(commentsforanswers_api)

new_comment_parser = RequestParser()
new_comment_parser.add_argument('content', type=str, required=True)
new_comment_parser.add_argument('selfeval', type=bool, required=False, default=False)
new_comment_parser.add_argument('evaluation', type=bool, required=False, default=False)
new_comment_parser.add_argument('type', type=int, default=0)
new_comment_parser.add_argument('user_id', type=int, default=None)

existing_comment_parser = RequestParser()
existing_comment_parser.add_argument('id', type=int, required=True, help="Comment id is required.")
existing_comment_parser.add_argument('content', type=str, required=True)
existing_comment_parser.add_argument('type', type=int, default=0)

answer_comment_list_parser = pagination_parser.copy()
answer_comment_list_parser.add_argument('selfeval', type=str, required=False, default='true')
answer_comment_list_parser.add_argument('ids', type=str, required=False, default=None)
answer_comment_list_parser.add_argument('answer_ids', type=str, required=False, default=None)
answer_comment_list_parser.add_argument('question_id', type=int, required=False, default=None)
answer_comment_list_parser.add_argument('user_ids', type=str, required=False, default=None)

# events
on_comment_modified = event.signal('COMMENT_MODIFIED')
on_comment_get = event.signal('COMMENT_GET')
on_comment_list_get = event.signal('COMMENT_LIST_GET')
on_comment_create = event.signal('COMMENT_CREATE')
on_comment_delete = event.signal('COMMENT_DELETE')

on_answer_comment_modified = event.signal('ANSWER_COMMENT_MODIFIED')
on_answer_comment_get = event.signal('ANSWER_COMMENT_GET')
on_answer_comment_list_get = event.signal('ANSWER_COMMENT_LIST_GET')
on_answer_comment_create = event.signal('ANSWER_COMMENT_CREATE')
on_answer_comment_delete = event.signal('ANSWER_COMMENT_DELETE')
on_answer_comment_user_get = event.signal('ANSWER_COMMENT_USER_GET')


# /
class QuestionCommentRootAPI(Resource):
    # TODO pagination
    @login_required
    def get(self, course_id, question_id):
        Courses.exists_or_404(course_id)
        question = PostsForQuestions.query. \
            options(load_only('id', 'criteria_count', 'posts_id')). \
            get_or_404(question_id)
        require(READ, question)
        restrict_users = not allow(MANAGE, question)

        comments = PostsForComments.query. \
            options(joinedload('post').joinedload('user')). \
            join(Posts).filter_by(courses_id=course_id). \
            join(PostsForQuestionsAndPostsForComments).filter_by(questions_id=question_id). \
            order_by(Posts.created.asc()).all()

        on_comment_list_get.send(
            self,
            event_name=on_comment_list_get.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id})

        return {"objects": marshal(comments, dataformat.get_posts_for_comments_new(restrict_users))}

    @login_required
    def post(self, course_id, question_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        post = Posts(courses_id=course_id)
        comment = PostsForComments(post=post)
        comment_for_question = PostsForQuestionsAndPostsForComments(postsforcomments=comment, questions_id=question_id)
        require(CREATE, comment)
        params = new_comment_parser.parse_args()
        post.content = params.get("content")
        if not post.content:
            return {"error": "The comment content is empty!"}, 400
        post.users_id = current_user.id
        db.session.add(post)
        db.session.add(comment)
        db.session.add(comment_for_question)

        on_comment_create.send(
            self,
            event_name=on_comment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(comment, dataformat.get_posts_for_comments_new(False)))

        db.session.commit()
        return marshal(comment, dataformat.get_posts_for_comments_new())

apiQ.add_resource(QuestionCommentRootAPI, '')


# / id
class QuestionCommentIdAPI(Resource):
    @login_required
    def get(self, course_id, question_id, comment_id):
        Courses.query.get_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        comment = PostsForComments.query. \
            options(joinedload('post').joinedload('user')). \
            get_or_404(comment_id)
        require(READ, comment)

        on_comment_get.send(
            self,
            event_name=on_comment_get.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id, 'comment_id': comment_id})

        return marshal(comment, dataformat.get_posts_for_comments_new())

    @login_required
    def post(self, course_id, question_id, comment_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        comment = PostsForComments.query. \
            options(joinedload('post').joinedload('user')). \
            get_or_404(comment_id)
        require(EDIT, comment)

        params = existing_comment_parser.parse_args()
        # make sure the comment id in the rul and the id matches
        if params['id'] != comment.id:
            return {"error": "Comment id does not match URL."}, 400
        # modify comment according to new values, preserve original values if values not passed
        if not params.get("content"):
            return {"error": "The comment content is empty!"}, 400
        comment.content = params.get("content")
        db.session.add(comment.post)

        on_comment_modified.send(
            self,
            event_name=on_comment_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(comment.post))

        db.session.commit()
        return marshal(comment, dataformat.get_posts_for_comments_new())

    @login_required
    def delete(self, course_id, question_id, comment_id):
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        comment = PostsForComments.query. \
            options(joinedload('post').joinedload('user')). \
            get_or_404(comment_id)
        require(DELETE, comment)
        data = marshal(comment, dataformat.get_posts_for_comments_new(False))
        db.session.delete(comment)
        db.session.commit()

        on_comment_delete.send(
            self,
            event_name=on_comment_delete.name,
            user=current_user,
            course_id=course_id,
            data=data)

        return {'id': comment.id}
apiQ.add_resource(QuestionCommentIdAPI, '/<int:comment_id>')


class AnswerCommentListAPI(Resource):
    @login_required
    def get(self, **kwargs):
        """
        **Example request**:

        .. sourcecode:: http

            GET /api/answer/123/comments HTTP/1.1
            Host: example.com
            Accept: application/json

        .. sourcecode:: http

            GET /api/answer_comments?ids=1,2,3&selfeval=only HTTP/1.1
            Host: example.com
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json
            [{
                'id': 1
                'content': 'comment text',
                'created': '',
                'user_id': 1,
                'user_displayname': 'John',
                'user_fullname': 'John Smith',
                'user_avatar': '12k3jjh24k32jhjksaf',
                'selfeval': true,
                'evaluation': true,
                'type': 0,
                'course_id': 1,
            }]

        :query string ids: a comma separated comment IDs to query
        :query string answer_ids: a comma separated answer IDs for answer filter
        :query int question_id: filter the answer comments with a question
        :query string user_ids: a comma separated user IDs that own the comments
        :query string selfeval: indicate whether the result should include self-evaluation comments or self-eval only.
                Possible values: true, false or only. Default true.
        :reqheader Accept: the response content type depends on :mailheader:`Accept` header
        :resheader Content-Type: this depends on :mailheader:`Accept` header of request
        :statuscode 200: no error
        :statuscode 404: answers don't exist

        """
        params = answer_comment_list_parser.parse_args()
        answer_ids = []
        if 'answer_id' in kwargs:
            answer_ids.append(kwargs['answer_id'])
        elif 'answer_ids' in params and params['answer_ids']:
            answer_ids.extend(params['answer_ids'].split(','))

        if not answer_ids and not params['ids'] and not params['question_id'] and not params['user_ids']:
            abort(404)

        conditions = []

        answers = PostsForAnswers.query. \
            options(joinedload(PostsForAnswers.post)). \
            filter(PostsForAnswers.id.in_(answer_ids)).all() if answer_ids else []
        if answer_ids and not answers:
            # non-existing answer ids. we return empty result
            abort(404)

        # build query condition for each answer
        for answer in answers:
            clauses = [PostsForAnswersAndPostsForComments.answers_id == answer.id]

            # student can only see the comments for themselves or public ones.
            # since the owner of the answer can access all comments. We only filter
            # on non-owners
            if current_user.get_course_role(answer.course_id) == UserTypesForCourse.TYPE_STUDENT \
                    and answer.user_id != current_user.id:
                public_comment_condition = and_(
                    PostsForAnswersAndPostsForComments.evaluation.isnot(True),
                    PostsForAnswersAndPostsForComments.selfeval.isnot(True),
                    PostsForAnswersAndPostsForComments.type != 0
                )
                # public comments or comments owned by current user
                clauses.append(or_(public_comment_condition, PostsForComments.user_id == current_user.id))

            conditions.append(and_(*clauses))

        query = PostsForComments.query. \
            options(contains_eager(PostsForComments.post).joinedload(Posts.user)) . \
            options(contains_eager(PostsForComments.post).joinedload(Posts.files)) . \
            join(PostsForAnswersAndPostsForComments). \
            options(contains_eager(PostsForComments.answer_assoc)). \
            filter(or_(*conditions)) . \
            join(Posts)

        if params['ids']:
            query = query.filter(PostsForComments.id.in_(params['ids'].split(',')))

        if params['selfeval'] == 'false':
            # do not include self-eval
            query = query.filter(PostsForAnswersAndPostsForComments.selfeval.is_(False))
        elif params['selfeval'] == 'only':
            # only selfeval
            query = query.filter(PostsForAnswersAndPostsForComments.selfeval.is_(True))

        if params['question_id']:
            query = query.join(PostsForAnswersAndPostsForComments.postsforanswers). \
                filter_by(questions_id=params['question_id'])

        if params['user_ids']:
            user_ids = params['user_ids'].split(',')
            query = query.filter(Posts.users_id.in_(user_ids))

        comments = query.order_by(Posts.created.desc()).all()

        # checking the permission
        for comment in comments:
            require(READ, comment.answer_assoc)

        on_answer_comment_list_get.send(
            self,
            event_name=on_answer_comment_list_get.name,
            user=current_user,
            data={'answer_ids': ','.join([str(answer_id) for answer_id in answer_ids])})

        return marshal(comments, dataformat.get_answer_comment(not allow(READ, USER_IDENTITY)))

    @login_required
    def post(self, course_id, question_id, answer_id):
        """
        Create comment for a answer
        """
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        answer = PostsForAnswers.query.get_or_404(answer_id)
        post = Posts(courses_id=course_id)
        comment = PostsForComments(post=post)
        comment_for_answer = PostsForAnswersAndPostsForComments(postsforcomments=comment, answers_id=answer.id)
        require(CREATE, comment_for_answer)
        params = new_comment_parser.parse_args()
        post.content = params.get("content")
        if not post.content:
            return {"error": "The comment content is empty!"}, 400

        if params.get('user_id') and current_user.system_role == UserTypesForSystem.TYPE_SYSADMIN:
            post.users_id = params.get('user_id')
        else:
            post.users_id = current_user.id
        comment_for_answer.selfeval = params.get("selfeval", False)
        comment_for_answer.evaluation = params.get("evaluation", False)
        comment_for_answer.type = params.get("type", 0)
        db.session.add(post)
        db.session.add(comment)
        db.session.add(comment_for_answer)

        on_answer_comment_create.send(
            self,
            event_name=on_answer_comment_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(comment, dataformat.get_answer_comment(False)))

        db.session.commit()
        return marshal(comment, dataformat.get_answer_comment())

apiA.add_resource(
    AnswerCommentListAPI,
    '/answers/<int:answer_id>/comments', '/answer_comments',
    endpoint='answer_comments')


class AnswerCommentAPI(Resource):
    @login_required
    def get(self, course_id, question_id, answer_id, comment_id):
        """
        Get an answer comment
        """
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        PostsForAnswers.query.options(load_only('id')).get_or_404(answer_id)
        comment = PostsForComments.query.get_or_404(comment_id)
        require(READ, comment)

        on_answer_comment_get.send(
            self,
            event_name=on_answer_comment_get.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id, 'answer_id': answer_id, 'comment_id': comment_id})

        return marshal(comment, dataformat.get_answer_comment())

    @login_required
    def post(self, course_id, question_id, answer_id, comment_id):
        """
        Create an answer comment
        """
        Courses.exists_or_404(course_id)
        PostsForQuestions.query.options(load_only('id')).get_or_404(question_id)
        PostsForAnswers.query.options(load_only('id')).get_or_404(answer_id)
        comment = PostsForComments.query.get_or_404(comment_id)
        require(EDIT, comment)
        params = existing_comment_parser.parse_args()
        # make sure the comment id in the rul and the id matches
        if params['id'] != comment.id:
            return {"error": "Comment id does not match URL."}, 400
        # modify comment according to new values, preserve original values if values not passed
        comment.content = params.get("content")
        if not comment.content:
            return {"error": "The comment content is empty!"}, 400
        comment.answer_assoc.type = params.get("type")
        db.session.add(comment)

        on_answer_comment_modified.send(
            self,
            event_name=on_answer_comment_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(comment))

        db.session.commit()
        return marshal(comment, dataformat.get_answer_comment())

    @login_required
    def delete(self, course_id, question_id, answer_id, comment_id):
        """
        Delete an answer comment
        """
        comment = PostsForComments.query.get_or_404(comment_id)
        require(DELETE, comment)
        data = marshal(comment, dataformat.get_answer_comment(False))
        db.session.delete(comment)
        db.session.commit()

        on_answer_comment_delete.send(
            self,
            event_name=on_answer_comment_delete.name,
            user=current_user,
            course_id=course_id,
            data=data)

        return {'id': comment.id}

apiA.add_resource(AnswerCommentAPI, '/answers/<int:answer_id>/comments/<int:comment_id>', endpoint='answer_comment')
