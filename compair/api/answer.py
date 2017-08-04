from bouncer.constants import CREATE, READ, EDIT, MANAGE, DELETE
from flask import Blueprint
from flask_login import login_required, current_user, current_app
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import joinedload, undefer_group
from itertools import groupby
from operator import attrgetter

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require, allow, is_user_access_restricted
from compair.models import Answer, Assignment, Course, User, Comparison, Criterion, \
    AnswerScore, UserCourse, SystemRole, CourseRole, AnswerComment, AnswerCommentType, File

from .util import new_restful_api, get_model_changes, pagination_parser

answers_api = Blueprint('answers_api', __name__)
api = new_restful_api(answers_api)

new_answer_parser = RequestParser()
new_answer_parser.add_argument('user_id', default=None)
new_answer_parser.add_argument('content', default=None)
new_answer_parser.add_argument('file_id', default=None)
new_answer_parser.add_argument('draft', type=bool, default=False)

existing_answer_parser = RequestParser()
existing_answer_parser.add_argument('id', required=True, help="Answer id is required.")
existing_answer_parser.add_argument('user_id', default=None)
existing_answer_parser.add_argument('content', default=None)
existing_answer_parser.add_argument('file_id', default=None)
existing_answer_parser.add_argument('draft', type=bool, default=False)

answer_list_parser = pagination_parser.copy()
answer_list_parser.add_argument('group', required=False, default=None)
answer_list_parser.add_argument('author', required=False, default=None)
answer_list_parser.add_argument('orderBy', required=False, default=None)
answer_list_parser.add_argument('top', type=bool, required=False, default=None)
answer_list_parser.add_argument('ids', required=False, default=None)

user_answer_list_parser = RequestParser()
user_answer_list_parser.add_argument('draft', type=bool, required=False, default=False)
user_answer_list_parser.add_argument('unsaved', type=bool, required=False, default=False)

answer_comparison_list_parser = pagination_parser.copy()
answer_comparison_list_parser.add_argument('group', required=False, default=None)
answer_comparison_list_parser.add_argument('author', required=False, default=None)

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

        require(READ, assignment,
            title="Assignment Answers Unavailable",
            message="Answers are visible only to those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not allow(MANAGE, assignment)

        params = answer_list_parser.parse_args()

        if restrict_user and not assignment.after_comparing:
            # only the answer from student himself/herself should be returned
            params['author'] = current_user.uuid

        # this query could be further optimized by reduction the selected columns
        query = Answer.query \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('score')) \
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

        if params['orderBy'] == 'score':
            query = query.join(AnswerScore) \
                .order_by(AnswerScore.score.desc(), Answer.created.desc())

            # limit answers up to rank if rank_display_limit is set and current_user is restricted (student)
            if assignment.rank_display_limit and restrict_user:
                score_for_rank = AnswerScore.get_score_for_rank(assignment.id, assignment.rank_display_limit)

                # display answers with score >= score_for_rank
                if score_for_rank != None:
                    # will get all answer with a score greater than or equal to the score for a given rank
                    # the '- 0.00001' fixes floating point precision problems
                    query = query.filter(AnswerScore.score >= score_for_rank - 0.00001)

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
            abort(403, title="Answer Not Saved", message="The answer deadline has passed. No answers can be saved beyond the deadline unless the instructor saves it on your behalf.")

        require(CREATE, Answer(course_id=course.id),
            title="Answers Not Saved",
            message="Answers can be saved only to those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not allow(MANAGE, assignment)

        answer = Answer(assignment_id=assignment.id)

        params = new_answer_parser.parse_args()
        answer.content = params.get("content")
        answer.draft = params.get("draft")

        file_uuid = params.get('file_id')
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            answer.file_id = attachment.id
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            abort(400, title="Answer Not Saved", message="Please provide content in the text editor or upload a file to save this answer.")

        user_uuid = params.get("user_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and not allow(MANAGE, Answer(course_id=course.id)):
            abort(400, title="Answer Not Saved", message="Only instructors and teaching assistants can submit an answer on behalf of another.")

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
                abort(400, title="Answer Not Saved", message="Answers can be saved only to those enrolled in the course. Please double-check your enrollment in this course.")

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
                abort(400, title="Answer Not Saved", message="An answer has already been submitted for this assignment by you or on your behalf.")

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
            joinedloads=['file', 'user', 'score']
        )
        require(READ, answer,
            title="Answer Unavailable",
            message="Your role in this course does not allow you to view this answer.")
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
            abort(403, title="Answer Not Updated", message="The answer deadline has passed. No answers can be updated beyond the deadline unless the instructor updates it on your behalf.")

        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        require(EDIT, answer,
            title="Answer Not Updated",
            message="Your role in this course does not allow you to update this answer.")
        restrict_user = not allow(MANAGE, assignment)

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS and answer.user_id in DemoDataFixture.DEFAULT_STUDENT_IDS:
                abort(400, title="Answer Not Updated", message="Sorry, you cannot edit the default student demo answers.")

        params = existing_answer_parser.parse_args()
        # make sure the answer id in the url and the id matches
        if params['id'] != answer_uuid:
            abort(400, title="Answer Not Updated", message="The answer's ID does not match the URL, which is required in order to update the answer.")

        # modify answer according to new values, preserve original values if values not passed
        answer.content = params.get("content")

        user_uuid = params.get("user_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and user_uuid != answer.user_uuid:
            if not allow(MANAGE, answer) or not answer.draft:
                abort(400, title="Answer Not Updated",
                    message="Only instructors and teaching assistants can update an answer on behalf of another.")
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
                    abort(400, title="Answer Not Updated", message="An answer has already been submitted for this assignment by you or on your behalf.")

        # can only change draft status while a draft
        if answer.draft:
            answer.draft = params.get("draft")
        uploaded = params.get('uploadFile')

        file_uuid = params.get('file_id')
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            answer.file_id = attachment.id
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            abort(400, title="Answer Not Updated", message="Please provide content in the text editor or upload a file to update this answer.")

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
        require(DELETE, answer,
            title="Answer Not Deleted",
            message="Your role in this course does not allow you to delete this answer.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS and answer.user_id in DemoDataFixture.DEFAULT_STUDENT_IDS:
                abort(400, title="Answer Not Deleted", message="Sorry, you cannot remove the default student demo answers.")

        answer.active = False
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
        require(READ, assignment,
            title="Assignment Comparisons Unavailable",
            message="Your role in this course does not allow you to view comparisons for this assignment.")

        can_read = allow(READ, Comparison(course_id=course.id))
        restrict_user = is_user_access_restricted(current_user)

        params = answer_comparison_list_parser.parse_args()

        # each pagination entry would be one comparison set by a user for the assignment
        query = Comparison.query \
            .options(joinedload('answer1')) \
            .options(joinedload('answer2')) \
            .options(joinedload('comparison_criteria')) \
            .filter_by(assignment_id=assignment.id, completed=True) \
            .order_by(Comparison.user_id, Comparison.created)

        if not can_read:
            query = query.filter_by(user_id=current_user.id)
        elif params['author']:
            query = query.filter_by(user_uuid=params['author'])
        elif params['group']:
            subquery = User.query \
                .with_entities(User.id) \
                .join('user_courses') \
                .filter_by(group_name=params['group']) \
                .subquery()
            query = query.filter(Comparison.user_id.in_(subquery))

        page = query.paginate(params['page'], params['perPage'])

        results = []
        if page.total:
            # retrieve the answer comments
            user_comparison_answers = {}

            for comparison in page.items:
                user_answers = user_comparison_answers.setdefault(comparison.user_id, set())
                user_answers.add(comparison.answer1_id)
                user_answers.add(comparison.answer2_id)

            conditions = []
            for user_id, answer_set in user_comparison_answers.items():
                conditions.append(and_(
                        AnswerComment.comment_type == AnswerCommentType.evaluation,
                        AnswerComment.user_id == user_id,
                        AnswerComment.answer_id.in_(list(answer_set)),
                        AnswerComment.assignment_id == assignment.id
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

            for comparison in page.items:
                comparison.answer1_feedback = [comment for comment in answer_comments if
                    comment.user_id == comparison.user_id and
                    comment.answer_id == comparison.answer1_id and
                    comment.comment_type == AnswerCommentType.evaluation
                ]

                comparison.answer2_feedback = [comment for comment in answer_comments if
                    comment.user_id == comparison.user_id and
                    comment.answer_id == comparison.answer2_id and
                    comment.comment_type == AnswerCommentType.evaluation
                ]

                comparison.self_evaluation = [comment for comment in answer_comments if
                    comment.user_id == comparison.user_id and
                    comment.comment_type == AnswerCommentType.self_evaluation
                ]

                results.append(comparison)

        on_answer_comparisons_get.send(
            self,
            event_name=on_answer_comparisons_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id}
        )

        return {"objects": marshal(results, dataformat.get_comparison(restrict_user, with_feedback=True, with_self_evaluation=True)),
                "page": page.page, "pages": page.pages, "total": page.total, "per_page": page.per_page}


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

        require(READ, Answer(user_id=current_user.id),
            title="Answers Unavailable",
            message="Your role in this course does not allow you to view answers for this assignment.")
        restrict_user = not allow(MANAGE, assignment)

        params = user_answer_list_parser.parse_args()

        query = Answer.query \
            .options(joinedload('comments')) \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('score')) \
            .filter_by(
                active=True,
                assignment_id=assignment.id,
                course_id=course.id,
                user_id=current_user.id,
                draft=params.get('draft')
            )

        if params.get('unsaved'):
            query = query.filter(Answer.modified == Answer.created)

        answers = query.all()

        on_user_answer_get.send(
            self,
            event_name=on_user_answer_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {"objects": marshal(answers, dataformat.get_answer(restrict_user))}


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

        require(READ, answer,
            title="Answer Not Flagged",
            message="Your role in this course does not allow you to flag answers.")
        restrict_user = not allow(MANAGE, answer)

        # anyone can flag an answer, but only the original flagger or someone who can manage
        # the answer can unflag it
        if answer.flagged and answer.flagger_user_id != current_user.id and \
                not allow(MANAGE, answer):
            abort(400, title="Answer Update Failed", message="You do not have permission to unflag this answer.")

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

        require(MANAGE, answer,
            title="Answer Not Selected",
            message="Your role in this course does not allow you to select top answers.")

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