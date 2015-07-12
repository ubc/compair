from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from sqlalchemy import func, and_

from . import dataformat
from .core import event
from .models import SelfEvaluationTypes, PostsForAnswersAndPostsForComments, PostsForAnswers, Courses, \
    PostsForComments, Posts, PostsForQuestions
from .util import new_restful_api

selfeval_api = Blueprint('selfeval_api', __name__)
api = new_restful_api(selfeval_api)

selfeval_acomments_api = Blueprint('selfeval_acomments_api', __name__)
apiA = new_restful_api(selfeval_acomments_api)

# events
selfevaltype_get = event.signal('SELFEVAL_TYPE_GET')
selfeval_question_acomment_count = event.signal('SELFEVAL_QUESTION_ACOMMENT_COUNT')
selfeval_course_acomment_count = event.signal('SELFEVAL_COURSE_ACOMMENT_COUNT')


# /
class SelfEvalTypeRootAPI(Resource):
    @login_required
    def get(self):
        types = SelfEvaluationTypes.query. \
            order_by(SelfEvaluationTypes.name.desc()).all()

        selfevaltype_get.send(
            self,
            event_name=selfevaltype_get.name,
            user=current_user
        )

        return {"types": marshal(types, dataformat.get_selfeval_types())}


api.add_resource(SelfEvalTypeRootAPI, '')


# /questionId
class SelfEvalACommentsQuestionIdAPI(Resource):
    @login_required
    def get(self, course_id, question_id):
        Courses.query.get_or_404(course_id)
        count = comment_count([question_id], current_user.id)

        selfeval_question_acomment_count.send(
            self,
            event_name=selfeval_question_acomment_count.name,
            user=current_user,
            course_id=course_id,
            data={'question_id': question_id})

        return {"count": count}


apiA.add_resource(SelfEvalACommentsQuestionIdAPI, '/<int:question_id>')


# /
class SelfEvalACommentsAPI(Resource):
    @login_required
    def get(self, course_id):
        Courses.query.get_or_404(course_id)
        questions = PostsForQuestions.query.join(Posts).filter_by(courses_id=course_id).all()
        comments = comment_count({question.id for question in questions}, current_user.id)

        selfeval_course_acomment_count.send(
            self,
            event_name=selfeval_course_acomment_count.name,
            user=current_user,
            course_id=course_id
        )

        return {'replies': comments}


apiA.add_resource(SelfEvalACommentsAPI, '')


def comment_count(questions, user_id):
    res = PostsForQuestions.query. \
        with_entities(PostsForQuestions.id, func.count(Posts.id)). \
        filter(PostsForQuestions.id.in_(questions)). \
        outerjoin(PostsForAnswers). \
        outerjoin(PostsForAnswersAndPostsForComments, and_(
            PostsForAnswersAndPostsForComments.answers_id == PostsForAnswers.id,
            PostsForAnswersAndPostsForComments.selfeval)).\
        outerjoin(PostsForComments).\
        outerjoin(Posts, and_(
            PostsForComments.posts_id == Posts.id,
            Posts.users_id == user_id)). \
        group_by(PostsForQuestions.id).all()

    return {q[0]: q[1] for q in res}
