from bouncer.constants import CREATE, READ, EDIT, MANAGE, DELETE
from flask import Blueprint, abort
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import load_only, joinedload, contains_eager, undefer_group

from . import dataformat
from acj.core import db
from acj.authorization import require, allow, is_user_access_restricted
from acj.models import Answer, Assignment, Course, User, Comparison, \
    Score, UserCourse, CourseRole
    
from .util import new_restful_api, get_model_changes, pagination_parser
from .file import add_new_file, delete_file
from acj.core import event

answers_api = Blueprint('answers_api', __name__)
api = new_restful_api(answers_api)

new_answer_parser = RequestParser()
new_answer_parser.add_argument('user', type=int, default=None)
new_answer_parser.add_argument('content', type=str, default=None)
new_answer_parser.add_argument('file_name', type=str, default=None)
new_answer_parser.add_argument('file_alias', type=str, default=None)

existing_answer_parser = new_answer_parser.copy()
existing_answer_parser.add_argument('id', type=int, required=True, help="Answer id is required.")
existing_answer_parser.add_argument('uploadedFile', type=bool, default=False)

answer_list_parser = pagination_parser.copy()
answer_list_parser.add_argument('group', type=str, required=False, default=None)
answer_list_parser.add_argument('author', type=int, required=False, default=None)
answer_list_parser.add_argument('orderBy', type=str, required=False, default=None)
answer_list_parser.add_argument('ids', type=str, required=False, default=None)

flag_parser = RequestParser()
flag_parser.add_argument(
    'flagged', type=bool, required=True,
    help="Expected boolean value 'flagged' is missing."
)


# events
on_answer_modified = event.signal('ANSWER_MODIFIED')
on_answer_get = event.signal('ANSWER_GET')
on_answer_list_get = event.signal('ANSWER_LIST_GET')
on_answer_create = event.signal('ANSWER_CREATE')
on_answer_delete = event.signal('ANSWER_DELETE')
on_answer_flag = event.signal('ANSWER_FLAG')
on_user_answer_get = event.signal('USER_ANSWER_GET')
on_user_answered_count = event.signal('USER_ANSWERED_COUNT')

# messages
answer_deadline_message = 'Answer deadline has passed.'

# /
class AnswerRootAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        """
        Return a list of answers for a assignment based on search criteria. The
        list of the answers are paginated. If there is any answers from instructor
        or TA, their answers will be on top of the list.

        :param course_id: course id
        :param assignment_id: assignment id
        :return: list of answers
        """
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, assignment)
        restrict_user = not allow(MANAGE, assignment)

        params = answer_list_parser.parse_args()
        
        if restrict_user and not assignment.after_comparing:
            # only the answer from student himself/herself should be returned
            params['author'] = current_user.id

        # this query could be further optimized by reduction the selected columns
        query = Answer.query. \
            options(joinedload('file')). \
            options(joinedload('user')). \
            options(joinedload('scores')). \
            options(undefer_group('counts')). \
            filter_by(
                assignment_id=assignment_id,
                active=True
            )

        user_ids = []
        if params['author']:
            query = query.filter(Answer.user_id == params['author'])
            user_ids.append(params['author'])
        elif params['group']:
            # get all user ids in the group
            user_courses = UserCourse.query. \
                filter_by(
                    course_id=course_id,
                    group_name=params['group']
                ). \
                all()
            user_ids = [x.user_id for x in user_courses]

        if params['ids']:
            query = query.filter(Answer.id.in_(params['ids'].split(',')))

        # place instructor and TA's answer at the top of the list
        inst_subquery = Answer.query \
            .with_entities(Answer.id.label('inst_answer')) \
            .join(UserCourse, Answer.user_id == UserCourse.user_id) \
            .filter(and_(
                UserCourse.course_id == course_id,
                UserCourse.course_role == CourseRole.instructor
            ))
        ta_subquery = Answer.query \
            .with_entities(Answer.id.label('ta_answer')) \
            .join(UserCourse, Answer.user_id == UserCourse.user_id) \
            .filter(and_(
                UserCourse.course_id == course_id,
                UserCourse.course_role == CourseRole.teaching_assistant
            ))
        query = query.order_by(Answer.id.in_(inst_subquery).desc(), Answer.id.in_(ta_subquery).desc())

        if params['orderBy'] and len(user_ids) != 1:
            # order answer ids by one criterion and pagination, in case there are multiple criteria in assignment
            # left join on Score and add or condition for criteria_id is None to include all answers
            # that don't have score yet
            query = query.outerjoin(Score) \
                .filter(or_(
                    Score.criteria_id == params['orderBy'], 
                    Score.criteria_id.is_(None)
                 ))
            query = query.order_by(Score.score.desc(), Answer.created.desc())
        else:
            query = query.order_by(Answer.created.desc())

        if user_ids:
            query = query.filter(Answer.user_id.in_(user_ids))

        page = query.paginate(params['page'], params['perPage'])

        on_answer_list_get.send(
            self,
            event_name=on_answer_list_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id})

        return {"objects": marshal(page.items, dataformat.get_answer(restrict_user)), 
                "page": page.page, "pages": page.pages, 
                "total": page.total, "per_page": page.per_page}

    @login_required
    def post(self, course_id, assignment_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        if not assignment.answer_grace and not allow(MANAGE, assignment):
            return {'error': answer_deadline_message}, 403
        require(CREATE, Answer(course_id=course_id))
        
        answer = Answer(assignment_id=assignment_id)
        
        params = new_answer_parser.parse_args()
        answer.content = params.get("content")
        
        file_name = params.get('file_name')
        if not (answer.content or file_name):
            return {"error": "The answer content is empty!"}, 400
        
        user = params.get("user")
        answer.user_id = user if user else current_user.id

        # we allow instructor and TA to submit multiple answers for their own,
        # but not for student. Each student can only have one answer.
        if not allow(MANAGE, Answer(course_id=course_id)) or user is not None:
            # check if there is a previous answer submitted
            prev_answer = Answer.query. \
                filter_by(
                    assignment_id=assignment_id,
                    user_id=answer.user_id
                ). \
                first()
            if prev_answer:
                return {"error": "An answer has already been submitted."}, 400

        db.session.add(answer)
        db.session.commit()

        on_answer_create.send(
            self,
            event_name=on_answer_create.name,
            user=current_user,
            course_id=course_id,
            data=marshal(answer, dataformat.get_answer(False)))

        if file_name:
            answer.file_id = add_new_file(params.get('file_alias'), file_name, 
                Answer.__name__, answer.id)
                
            db.session.commit()
        
        return marshal(answer, dataformat.get_answer())


api.add_resource(AnswerRootAPI, '')


# /id
class AnswerIdAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id, answer_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        
        answer = Answer.get_active_or_404(
            answer_id, 
            joinedloads=['file', 'user', 'scores']
        )
        require(READ, answer)

        on_answer_get.send(
            self,
            event_name=on_answer_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'answer_id': answer_id})

        return marshal(answer, dataformat.get_answer(True))

    @login_required
    def post(self, course_id, assignment_id, answer_id):
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        if not assignment.answer_grace and not allow(MANAGE, assignment):
            return {'error': answer_deadline_message}, 403
        answer = Answer.get_active_or_404(answer_id)
        require(EDIT, answer)
        
        params = existing_answer_parser.parse_args()
        # make sure the answer id in the url and the id matches
        if params['id'] != answer_id:
            return {"error": "Answer id does not match the URL."}, 400
            
        # modify answer according to new values, preserve original values if values not passed
        answer.content = params.get("content")
        uploaded = params.get('uploadFile')
        file_name = params.get('file_name')
        if not (answer.content or uploaded or file_name):
            return {"error": "The answer content is empty!"}, 400
            
        db.session.add(answer)
        db.session.commit()

        on_answer_modified.send(
            self,
            event_name=on_answer_modified.name,
            user=current_user,
            course_id=course_id,
            data=get_model_changes(answer))

        if file_name:
            answer.file_id = add_new_file(params.get('file_alias'), file_name, 
                Answer.__name__, answer.id)
                
            db.session.commit()
        
        return marshal(answer, dataformat.get_answer())

    @login_required
    def delete(self, course_id, assignment_id, answer_id):
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        answer = Answer.get_active_or_404(answer_id)
        require(DELETE, answer)
        
        delete_file(answer.file_id)
        answer.file_id = None
        answer.active = False
        db.session.commit()

        on_answer_delete.send(
            self,
            event_name=on_answer_delete.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id, 'answer_id': answer_id})

        return {'id': answer.id}


api.add_resource(AnswerIdAPI, '/<int:answer_id>')


# /user
class AnswerUserIdAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        """
        Get answers submitted to the assignment submitted by current user

        :param course_id:
        :param assignment_id:
        :return: answers
        """
        Course.get_active_or_404(course_id)
        assignment = Assignment.get_active_or_404(assignment_id)
        require(READ, Answer(course_id=course_id))
        
        answers = Answer.query. \
            options(joinedload('comments')). \
            options(joinedload('file')). \
            options(joinedload('user')). \
            options(joinedload('scores')). \
            filter_by(
                active=True,
                assignment_id=assignment_id,
                course_id=course_id,
                user_id=current_user.id
            ). \
            all()

        on_user_answer_get.send(
            self,
            event_name=on_user_answer_get.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id})

        return {"objects": marshal( answers, dataformat.get_answer(True))}


api.add_resource(AnswerUserIdAPI, '/user')

# /flag
class AnswerFlagAPI(Resource):
    @login_required
    def post(self, course_id, assignment_id, answer_id):
        """
        Mark an answer as inappropriate or incomplete to instructors
        :param course_id:
        :param assignment_id:
        :param answer_id:
        :return: marked answer
        """
        Course.get_active_or_404(course_id)
        answer = Answer.get_active_or_404(answer_id)
        require(READ, answer)
        
        # anyone can flag an answer, but only the original flagger or someone who can manage
        # the answer can unflag it
        if answer.flagged and answer.flagger_user_id != current_user.id and \
                not allow(MANAGE, answer):
            return {"error": "You do not have permission to unflag this answer."}, 400
            
        params = flag_parser.parse_args()
        answer.flagged = params['flagged']
        answer.flagger_user_id = current_user.id
        db.session.add(answer)

        on_answer_flag.send(
            self,
            event_name=on_answer_flag.name,
            user=current_user,
            course_id=course_id,
            assignment_id=assignment_id,
            data={'answer_id': answer_id, 'flag': answer.flagged})

        db.session.commit()
        return marshal(
            answer,
            dataformat.get_answer(restrict_user=is_user_access_restricted(current_user))
        )


api.add_resource(AnswerFlagAPI, '/<int:answer_id>/flagged')


# /count
class AnswerCountAPI(Resource):
    @login_required
    def get(self, course_id, assignment_id):
        """
        Return number of answers submitted for the assignment by current user.

        :param course_id:
        :param assignment_id:
        :return: answer count
        """
        Course.get_active_or_404(course_id)
        Assignment.get_active_or_404(assignment_id)
        require(READ, Answer(course_id=course_id))
        
        answered = Answer.query. \
            filter_by(
                assignment_id=assignment_id,
                active=True,
                user_id=current_user.id
            ). \
            count()

        on_user_answered_count.send(
            self,
            event_name=on_user_answered_count.name,
            user=current_user,
            course_id=course_id,
            data={'assignment_id': assignment_id})

        return {'answered': answered}


api.add_resource(AnswerCountAPI, '/count')