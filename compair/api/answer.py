from bouncer.constants import CREATE, READ, EDIT, MANAGE, DELETE
from flask import Blueprint, abort
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import joinedload, undefer_group
from itertools import groupby
from operator import attrgetter

from . import dataformat
from compair.core import db, event
from compair.authorization import require, allow, is_user_access_restricted
from compair.models import Answer, Assignment, Course, User, Comparison, Criterion, \
    Score, UserCourse, SystemRole, CourseRole, AnswerComment, AnswerCommentType, File

from .util import new_restful_api, get_model_changes, pagination_parser

answers_api = Blueprint('answers_api', __name__)
api = new_restful_api(answers_api)

new_answer_parser = RequestParser()
new_answer_parser.add_argument('user_id', type=str, default=None)
new_answer_parser.add_argument('content', type=str, default=None)
new_answer_parser.add_argument('file_id', type=str, default=None)
new_answer_parser.add_argument('draft', type=bool, default=False)

existing_answer_parser = RequestParser()
existing_answer_parser.add_argument('id', type=str, required=True, help="Answer id is required.")
existing_answer_parser.add_argument('user_id', type=str, default=None)
existing_answer_parser.add_argument('content', type=str, default=None)
existing_answer_parser.add_argument('file_id', type=str, default=None)
existing_answer_parser.add_argument('draft', type=bool, default=False)

answer_list_parser = pagination_parser.copy()
answer_list_parser.add_argument('group', type=str, required=False, default=None)
answer_list_parser.add_argument('author', type=str, required=False, default=None)
answer_list_parser.add_argument('orderBy', type=str, required=False, default=None)
answer_list_parser.add_argument('top', type=bool, required=False, default=None)
answer_list_parser.add_argument('ids', type=str, required=False, default=None)

user_answer_list_parser = RequestParser()
user_answer_list_parser.add_argument('draft', type=bool, required=False, default=False)

answer_comparison_list_parser = pagination_parser.copy()
answer_comparison_list_parser.add_argument('group', type=str, required=False, default=None)
answer_comparison_list_parser.add_argument('author', type=str, required=False, default=None)

flag_parser = RequestParser()
flag_parser.add_argument('flagged', type=bool, required=True,
    help="Expected boolean value 'flagged' is missing."
)

top_answer_parser = RequestParser()
top_answer_parser.add_argument(
    'top_answer', type=bool, required=True,
    help="Expected boolean value 'top_answer' is missing."
)


# events
on_answer_modified = event.signal('ANSWER_MODIFIED')
on_answer_get = event.signal('ANSWER_GET')
on_answer_list_get = event.signal('ANSWER_LIST_GET')
on_answer_create = event.signal('ANSWER_CREATE')
on_answer_delete = event.signal('ANSWER_DELETE')
on_answer_flag = event.signal('ANSWER_FLAG')
on_set_top_answer = event.signal('SET_TOP_ANSWER')
on_user_answer_get = event.signal('USER_ANSWER_GET')
on_answer_comparisons_get = event.signal('ANSWER_COMPARISONS_GET')

# messages
answer_deadline_message = 'Answer deadline has passed.'

# /
class AnswerRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        """
        Return a list of answers for a assignment based on search criteria. The
        list of the answers are paginated. If there is any answers from instructor
        or TA, their answers will be on top of the list.

        :param course_uuid: course uuid
        :param assignment_uuid: assignment uuid
        :return: list of answers
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        require(READ, assignment)
        restrict_user = not allow(MANAGE, assignment)

        params = answer_list_parser.parse_args()

        if restrict_user and not assignment.after_comparing:
            # only the answer from student himself/herself should be returned
            params['author'] = current_user.uuid

        # this query could be further optimized by reduction the selected columns
        query = Answer.query \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('scores')) \
            .options(undefer_group('counts')) \
            .join(UserCourse, and_(
                Answer.user_id == UserCourse.user_id,
                UserCourse.course_id == course.id
            )) \
            .add_columns(
                UserCourse.course_role.__eq__(CourseRole.instructor).label("instructor_role"),
                UserCourse.course_role.__eq__(CourseRole.teaching_assistant).label("ta_role")
            ) \
            .filter(and_(
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                UserCourse.course_role != CourseRole.dropped
            )) \
            .order_by(desc('instructor_role'), desc('ta_role'))

        if params['author']:
            user = User.get_by_uuid_or_404(params['author'])
            query = query.filter(Answer.user_id == user.id)
        elif params['group']:
            query = query.filter(UserCourse.group_name == params['group'])

        if params['ids']:
            query = query.filter(Answer.uuid.in_(params['ids'].split(',')))

        if params['top']:
            query = query.filter(Answer.top_answer == True)

        if params['orderBy']:
            criterion = Criterion.get_active_by_uuid_or_404(params['orderBy'])

            # order answer ids by one criterion and pagination, in case there are multiple criteria in assignment
            # does not include answers without a score (Note: ta and instructor never have a score)
            query = query.join(Score) \
                .filter(Score.criterion_id == criterion.id) \
                .order_by(Score.score.desc(), Answer.created.desc())

            # limit answers up to rank if rank_display_limit is set and current_user is restricted (student)
            if assignment.rank_display_limit and restrict_user:
                score_for_rank = Score.get_score_for_rank(
                    assignment.id, criterion.id, assignment.rank_display_limit)

                # display answers with score >= score_for_rank
                if score_for_rank != None:
                    # will get all answer with a score greater than or equal to the score for a given rank
                    # the '- 0.00001' fixes floating point precision problems
                    query = query.filter(Score.score >= score_for_rank - 0.00001)

        else:
            query = query.order_by(Answer.created.desc())

        page = query.paginate(params['page'], params['perPage'])
        # remove label entities from results
        page.items = [answer for (answer, instructor_role, ta_role) in page.items]

        on_answer_list_get.send(
            self,
            event_name=on_answer_list_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {"objects": marshal(page.items, dataformat.get_answer(restrict_user)),
                "page": page.page, "pages": page.pages,
                "total": page.total, "per_page": page.per_page}

    @login_required
    def post(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        if not assignment.answer_grace and not allow(MANAGE, assignment):
            return {'error': answer_deadline_message}, 403

        require(CREATE, Answer(course_id=course.id))
        restrict_user = not allow(MANAGE, assignment)

        answer = Answer(assignment_id=assignment.id)

        params = new_answer_parser.parse_args()
        answer.content = params.get("content")
        answer.draft = params.get("draft")

        file_uuid = params.get('file_id')
        if file_uuid:
            uploaded_file = File.get_by_uuid_or_404(file_uuid)
            answer.file_id = uploaded_file.id
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            return {"error": "The answer content is empty!"}, 400

        user_uuid = params.get("user_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and not allow(MANAGE, Answer(course_id=course.id)):
            return {"error": "Only instructors and teaching assistants can submit an answer on behalf of another user."}, 400

        if user_uuid:
            user = User.get_by_uuid_or_404(user_uuid)
            answer.user_id = user.id
        else:
            answer.user_id = current_user.id

        user_course = UserCourse.query \
            .filter_by(
                course_id=course.id,
                user_id=answer.user_id
            ) \
            .one_or_none()

        # we allow instructor and TA to submit multiple answers for their own,
        # but not for student. Each student can only have one answer.
        instructors_and_tas = [CourseRole.instructor.value, CourseRole.teaching_assistant.value]
        if user_course == None:
            # only system admin can add answers for themselves to a class without being enrolled in it
            # required for managing comparison examples as system admin
            if current_user.id != answer.user_id or current_user.system_role != SystemRole.sys_admin:
                return {"error": "You are not enrolled in the course."}, 400

        elif user_course.course_role.value not in instructors_and_tas:
            # check if there is a previous answer submitted for the student
            prev_answer = Answer.query. \
                filter_by(
                    assignment_id=assignment.id,
                    user_id=answer.user_id,
                    active=True
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
            course_id=course.id,
            data=marshal(answer, dataformat.get_answer(restrict_user)))

        # update course & assignment grade for user if answer is fully submitted
        if not answer.draft:
            assignment.calculate_grade(answer.user)
            course.calculate_grade(answer.user)

        return marshal(answer, dataformat.get_answer(restrict_user))


api.add_resource(AnswerRootAPI, '')


# /id
class AnswerIdAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid, answer_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        answer = Answer.get_active_by_uuid_or_404(
            answer_uuid,
            joinedloads=['file', 'user', 'scores']
        )
        require(READ, answer)
        restrict_user = not allow(MANAGE, assignment)

        on_answer_get.send(
            self,
            event_name=on_answer_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id, 'answer_id': answer.id})

        return marshal(answer, dataformat.get_answer(restrict_user))

    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        if not assignment.answer_grace and not allow(MANAGE, assignment):
            return {'error': answer_deadline_message}, 403

        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        require(EDIT, answer)
        restrict_user = not allow(MANAGE, assignment)

        params = existing_answer_parser.parse_args()
        # make sure the answer id in the url and the id matches
        if params['id'] != answer_uuid:
            return {"error": "Answer id does not match the URL."}, 400

        # modify answer according to new values, preserve original values if values not passed
        answer.content = params.get("content")

        user_uuid = params.get("user_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and user_uuid != answer.user_uuid:
            if not allow(MANAGE, answer) or not answer.draft:
                return {"error": "Only instructors and teaching assistants can submit an answer on behalf of another user."}, 400
            user = User.get_by_uuid_or_404(user_uuid)
            answer.user_id = user.id

            user_course = UserCourse.query \
                .filter_by(
                    course_id=course.id,
                    user_id=answer.user_id
                ) \
                .one_or_none()

            if user_course.course_role.value not in [CourseRole.instructor.value, CourseRole.teaching_assistant.value]:
                # check if there is a previous answer submitted for the student
                prev_answer = Answer.query \
                    .filter(Answer.id != answer.id) \
                    .filter_by(
                        assignment_id=assignment.id,
                        user_id=answer.user_id,
                        active=True
                    ) \
                    .first()
                if prev_answer:
                    return {"error": "An answer has already been submitted."}, 400

        # can only change draft status while a draft
        if answer.draft:
            answer.draft = params.get("draft")
        uploaded = params.get('uploadFile')

        file_uuid = params.get('file_id')
        if file_uuid:
            answer.file = File.get_by_uuid_or_404(file_uuid)
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            return {"error": "The answer content is empty!"}, 400

        db.session.add(answer)
        db.session.commit()

        on_answer_modified.send(
            self,
            event_name=on_answer_modified.name,
            user=current_user,
            course_id=course.id,
            answer=answer,
            assignment=assignment,
            data=get_model_changes(answer))

        # update course & assignment grade for user if answer is fully submitted
        if not answer.draft:
            assignment.calculate_grade(answer.user)
            course.calculate_grade(answer.user)

        return marshal(answer, dataformat.get_answer(restrict_user))

    @login_required
    def delete(self, course_uuid, assignment_uuid, answer_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        require(DELETE, answer)

        answer.active = False
        if answer.file:
            answer.file.active = False
        db.session.commit()

        # update course & assignment grade for user if answer was fully submitted
        if not answer.draft:
            assignment.calculate_grade(answer.user)
            course.calculate_grade(answer.user)

        on_answer_delete.send(
            self,
            event_name=on_answer_delete.name,
            user=current_user,
            course_id=course.id,
            answer=answer,
            data={'assignment_id': assignment.id, 'answer_id': answer.id})

        return {'id': answer.uuid}


api.add_resource(AnswerIdAPI, '/<answer_uuid>')


# /comparisons
class AnswerComparisonsAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        require(READ, assignment)

        can_read = allow(READ, Comparison(course_id=course.id))
        restrict_user = is_user_access_restricted(current_user)

        params = answer_comparison_list_parser.parse_args()

        # each pagination entry would be one comparison set by a user for the assignment
        comparison_sets = Comparison.query \
            .with_entities(Comparison.user_id, Comparison.answer1_id, Comparison.answer2_id) \
            .filter_by(assignment_id=assignment.id, completed=True) \
            .group_by(Comparison.user_id, Comparison.answer1_id, Comparison.answer2_id)

        if not can_read:
            comparison_sets = comparison_sets.filter_by(user_id=current_user.id)
        elif params['author']:
            comparison_sets = comparison_sets.filter_by(user_uuid=params['author'])
        elif params['group']:
            subquery = User.query \
                .with_entities(User.id) \
                .join('user_courses') \
                .filter_by(group_name=params['group']) \
                .subquery()
            comparison_sets = comparison_sets.filter(Comparison.user_id.in_(subquery))

        page = comparison_sets.paginate(params['page'], params['perPage'])

        results = []

        if page.total:

            # retrieve the comparisons
            conditions = []
            for user_id, answer1_id, answer2_id in page.items:
                conditions.append(and_(
                    Comparison.user_id == user_id,
                    Comparison.answer1_id == answer1_id,
                    Comparison.answer2_id == answer2_id
                ))
            comparisons = Comparison.query \
                .options(joinedload('answer1')) \
                .options(joinedload('answer2')) \
                .options(joinedload('criterion')) \
                .filter_by(completed=True) \
                .filter(or_(*conditions)) \
                .order_by(Comparison.user_id, Comparison.created) \
                .all()

            # retrieve the answer comments
            user_comparioson_answers = {}
            for (user_id, answer1_id, answer2_id), group_set in groupby(comparisons, attrgetter('user_id', 'answer1_id', 'answer2_id')):
                user_answers = user_comparioson_answers.setdefault(user_id, set())
                user_answers.add(answer1_id)
                user_answers.add(answer2_id)

            conditions = []
            for user_id, answer_set in user_comparioson_answers.items():
                conditions.append(and_(
                        AnswerComment.user_id == user_id,
                        AnswerComment.comment_type == AnswerCommentType.evaluation,
                        AnswerComment.answer_id.in_(list(answer_set))
                ))
                conditions.append(and_(
                    AnswerComment.comment_type == AnswerCommentType.self_evaluation,
                    AnswerComment.user_id == user_id,
                    AnswerComment.assignment_id == assignment.id
                ))

            answer_comments = AnswerComment.query \
                .filter(or_(*conditions)) \
                .filter_by(draft=False) \
                .all()

            for (user_id, answer1_id, answer2_id), group_set in groupby(comparisons, attrgetter('user_id', 'answer1_id', 'answer2_id')):
                group = list(group_set)
                default = group[0]

                comparison_set = {
                    'course_uuid': default.course_uuid,
                    'assignment_uuid': default.assignment_uuid,
                    'user_uuid': default.user_uuid,

                    'comparisons': [comparison for comparison in group],
                    'answer1_uuid': default.answer1_uuid,
                    'answer2_uuid': default.answer2_uuid,
                    'answer1': default.answer1,
                    'answer2': default.answer2,

                    'user_fullname': default.user_fullname,
                    'user_displayname': default.user_displayname,
                    'user_avatar': default.user_avatar,

                    'answer1_feedback': [comment for comment in answer_comments if
                        comment.user_id == user_id and
                        comment.answer_id == default.answer1_id and
                        comment.comment_type == AnswerCommentType.evaluation
                    ],
                    'answer2_feedback': [comment for comment in answer_comments if
                        comment.user_id == user_id and
                        comment.answer_id == default.answer2_id and
                        comment.comment_type == AnswerCommentType.evaluation
                    ],
                    'self_evaluation': [comment for comment in answer_comments if
                        comment.user_id == user_id and
                        comment.comment_type == AnswerCommentType.self_evaluation
                    ],

                    'created': default.created
                }

                results.append(comparison_set)

        on_answer_comparisons_get.send(
            self,
            event_name=on_answer_comparisons_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id}
        )

        return {'objects': marshal(results, dataformat.get_comparison_set(restrict_user)), "page": page.page,
                "pages": page.pages, "total": page.total, "per_page": page.per_page}


api.add_resource(AnswerComparisonsAPI, '/comparisons')


# /user
class AnswerUserIdAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        """
        Get answers submitted to the assignment submitted by current user

        :param course_uuid:
        :param assignment_uuid:
        :return: answers
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        require(READ, Answer(user_id=current_user.id))
        restrict_user = not allow(MANAGE, assignment)

        params = user_answer_list_parser.parse_args()

        answers = Answer.query \
            .options(joinedload('comments')) \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('scores')) \
            .filter_by(
                active=True,
                assignment_id=assignment.id,
                course_id=course.id,
                user_id=current_user.id,
                draft=params.get('draft')
            ) \
            .all()

        on_user_answer_get.send(
            self,
            event_name=on_user_answer_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {"objects": marshal( answers, dataformat.get_answer(restrict_user))}


api.add_resource(AnswerUserIdAPI, '/user')

# /flag
class AnswerFlagAPI(Resource):
    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid):
        """
        Mark an answer as inappropriate or incomplete to instructors
        :param course_uuid:
        :param assignment_uuid:
        :param answer_uuid:
        :return: marked answer
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)

        require(READ, answer)
        restrict_user = not allow(MANAGE, answer)

        # anyone can flag an answer, but only the original flagger or someone who can manage
        # the answer can unflag it
        if answer.flagged and answer.flagger_user_id != current_user.id and \
                not allow(MANAGE, answer):
            return {"error": "You do not have permission to unflag this answer."}, 400

        params = flag_parser.parse_args()
        answer.flagged = params['flagged']
        answer.flagger_user_id = current_user.id
        db.session.add(answer)
        db.session.commit()

        on_answer_flag.send(
            self,
            event_name=on_answer_flag.name,
            user=current_user,
            course_id=course.id,
            assignment_id=assignment.id,
            answer=answer,
            data={'answer_id': answer.id, 'flag': answer.flagged})

        return marshal(answer, dataformat.get_answer(restrict_user))

api.add_resource(AnswerFlagAPI, '/<answer_uuid>/flagged')

# /top
class TopAnswerAPI(Resource):
    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid):
        """
        Mark an answer as being a top answer
        :param course_uuid:
        :param assignment_uuid:
        :param answer_uuid:
        :return: marked answer
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)

        require(MANAGE, answer)

        params = top_answer_parser.parse_args()
        answer.top_answer = params.get('top_answer')
        db.session.add(answer)

        on_set_top_answer.send(
            self,
            event_name=on_set_top_answer.name,
            user=current_user,
            course_id=course.id,
            assignment_id=assignment.id,
            data={'answer_id': answer.id, 'top_answer': answer.top_answer})

        db.session.commit()
        return marshal(answer, dataformat.get_answer(restrict_user=False))

api.add_resource(TopAnswerAPI, '/<answer_uuid>/top')