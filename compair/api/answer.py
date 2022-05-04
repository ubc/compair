import datetime

from bouncer.constants import CREATE, READ, EDIT, MANAGE, DELETE
from flask import Blueprint, current_app
from flask_bouncer import can
from flask_login import login_required, current_user
from flask_restful import Resource, marshal
from flask_restful.reqparse import RequestParser
from sqlalchemy import func, or_, and_, not_, desc
from sqlalchemy.orm import joinedload, undefer_group

from . import dataformat
from compair.core import db, event, abort
from compair.authorization import require
from compair.models import Answer, Assignment, Course, User, Comparison, Criterion, \
    AnswerScore, UserCourse, SystemRole, CourseRole, AnswerComment, AnswerCommentType, \
    File, Group

from .util import new_restful_api, get_model_changes, pagination_parser

answers_api = Blueprint('answers_api', __name__)
api = new_restful_api(answers_api)

new_answer_parser = RequestParser()
new_answer_parser.add_argument('user_id', default=None)
new_answer_parser.add_argument('group_id', default=None)
new_answer_parser.add_argument('comparable', type=bool, default=True)
new_answer_parser.add_argument('content', default=None)
new_answer_parser.add_argument('file_id', default=None)
new_answer_parser.add_argument('draft', type=bool, default=False)
new_answer_parser.add_argument('attempt_uuid', default=None)
new_answer_parser.add_argument('attempt_started', default=None)
new_answer_parser.add_argument('attempt_ended', default=None)

existing_answer_parser = new_answer_parser.copy()
existing_answer_parser.add_argument('id', required=True, help="Answer id is required.")

answer_list_parser = pagination_parser.copy()
answer_list_parser.add_argument('group', required=False, default=None)
answer_list_parser.add_argument('author', required=False, default=None)
answer_list_parser.add_argument('orderBy', required=False, default=None)
answer_list_parser.add_argument('top', type=bool, required=False, default=None)
answer_list_parser.add_argument('ids', required=False, default=None)

user_answer_list_parser = RequestParser()
user_answer_list_parser.add_argument('draft', type=bool, required=False, default=False)

top_answer_parser = RequestParser()
top_answer_parser.add_argument(
    'top_answer', type=bool, required=True, nullable=False,
    help="Expected boolean value 'top_answer' is missing."
)


# events
on_answer_modified = event.signal('ANSWER_MODIFIED')
on_answer_get = event.signal('ANSWER_GET')
on_answer_list_get = event.signal('ANSWER_LIST_GET')
on_answer_create = event.signal('ANSWER_CREATE')
on_answer_delete = event.signal('ANSWER_DELETE')
on_set_top_answer = event.signal('SET_TOP_ANSWER')
on_user_answer_get = event.signal('USER_ANSWER_GET')

from compair.api.file import on_attach_file, on_detach_file

# /
class AnswerRootAPI(Resource):
    @login_required
    def get(self, course_uuid, assignment_uuid):
        """
        Return a list of answers for a assignment based on search criteria. The
        list of the answers are paginated. If there is any answers from instructor
        or TA, their answers will be on top of the list (unless they are comparable).

        :param course_uuid: course uuid
        :param assignment_uuid: assignment uuid
        :return: list of answers
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        require(READ, assignment,
            title="Answers Unavailable",
            message="Answers are visible only to those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, assignment)

        params = answer_list_parser.parse_args()

        # if assingment has no rank display limit set, restricted users can't force to retreive by rank
        if params['orderBy'] == 'score' and restrict_user and not assignment.rank_display_limit:
            abort(400, title="Answers Unavailable", message="Sorry, you cannot cannot see answers by rank for this assignment.")

        if restrict_user and not assignment.after_comparing:
            # only the answer from student himself/herself should be returned
            params['author'] = current_user.uuid

        # this query could be further optimized by reduction the selected columns
        query = Answer.query \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('group')) \
            .options(joinedload('score')) \
            .options(undefer_group('counts')) \
            .outerjoin(UserCourse, and_(
                Answer.user_id == UserCourse.user_id,
                UserCourse.course_id == course.id
            )) \
            .add_columns(
                and_(
                    UserCourse != None,
                    UserCourse.course_role.__eq__(CourseRole.instructor),
                    not Answer.comparable
                ).label("instructor_role"),
                and_(
                    UserCourse != None,
                    UserCourse.course_role.__eq__(CourseRole.teaching_assistant),
                    not Answer.comparable
                ).label("ta_role")
            ) \
            .filter(and_(
                Answer.assignment_id == assignment.id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False,
                or_(
                    and_(UserCourse.course_role != CourseRole.dropped, Answer.user_id != None),
                    Answer.group_id != None
                )
            )) \
            .order_by(desc('instructor_role'), desc('ta_role'))

        if params['author']:
            user = User.get_by_uuid_or_404(params['author'])
            group = user.get_course_group(course.id)
            if group:
                query = query.filter(or_(
                    Answer.user_id == user.id,
                    Answer.group_id == group.id
                ))
            else:
                query = query.filter(Answer.user_id == user.id)
        elif params['group']:
            group = Group.get_active_by_uuid_or_404(params['group'])
            query = query.filter(or_(
                UserCourse.group_id == group.id,
                Answer.group_id == group.id
            ))

        if params['ids']:
            query = query.filter(Answer.uuid.in_(params['ids'].split(',')))

        if params['top']:
            query = query.filter(Answer.top_answer == True)

        if params['orderBy'] == 'score':
            # use outer join to include comparable answers that are not yet compared (for non-restricted users)
            query = query.outerjoin(AnswerScore) \
                .filter(Answer.comparable == True) \
                .order_by(AnswerScore.score.desc(), Answer.submission_date.desc(), Answer.created.desc())

            if restrict_user:
                # when orderd by rank, students won't see answers that are not compared (i.e. no score/rank)
                query = query.filter(AnswerScore.score.isnot(None))

            # limit answers up to rank if rank_display_limit is set and current_user is restricted (student)
            if assignment.rank_display_limit and restrict_user:
                score_for_rank = AnswerScore.get_score_for_rank(assignment.id, assignment.rank_display_limit)

                # display answers with score >= score_for_rank
                if score_for_rank != None:
                    # will get all answers with a score greater than or equal to the score for a given rank
                    # the '- 0.00001' fixes floating point precision problems
                    query = query.filter(AnswerScore.score >= score_for_rank - 0.00001)

        else:
            # when ordered by date, non-comparable answers should be on top of the list
            query = query.order_by(Answer.comparable, Answer.submission_date.desc(), Answer.created.desc())

        page = query.paginate(params['page'], params['perPage'], error_out=False)
        # remove label entities from results
        page.items = [answer for (answer, instructor_role, ta_role) in page.items]

        on_answer_list_get.send(
            self,
            event_name=on_answer_list_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        # only include score/rank info if:
        # - requesters are non-restricted users (i.e. instructors / TAs); or,
        # - retrieving answers ordered by score/rank
        include_score = (not restrict_user) or \
            (params['orderBy'] == 'score' and assignment.rank_display_limit)

        return {"objects": marshal(page.items, dataformat.get_answer(restrict_user, include_score=include_score)),
                "page": page.page, "pages": page.pages,
                "total": page.total, "per_page": page.per_page}

    @login_required
    def post(self, course_uuid, assignment_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        if not assignment.answer_grace and not can(MANAGE, assignment):
            abort(403, title="Answer Not Submitted", message="Sorry, the answer deadline has passed. No answers can be submitted after the deadline unless the instructor submits the answer for you.")

        require(CREATE, Answer(course_id=course.id),
            title="Answer Not Submitted",
            message="Answers can be submitted only by those enrolled in the course. Please double-check your enrollment in this course.")
        restrict_user = not can(MANAGE, assignment)

        answer = Answer(assignment_id=assignment.id)

        params = new_answer_parser.parse_args()
        answer.content = params.get("content")
        answer.draft = params.get("draft")

        file_uuid = params.get('file_id')
        attachment = None
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            answer.file_id = attachment.id
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            abort(400, title="Answer Not Submitted", message="Please provide content in the text editor or upload a file and try submitting again.")

        user_uuid = params.get("user_id")
        group_uuid = params.get("group_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and not can(MANAGE, Answer(course_id=course.id)):
            abort(400, title="Answer Not Submitted", message="Only instructors and teaching assistants can submit an answer on behalf of another.")
        if group_uuid and not assignment.enable_group_answers:
            abort(400, title="Answer Not Submitted", message="Group answers are not allowed for this assignment.")
        if group_uuid and not can(MANAGE, Answer(course_id=course.id)):
            abort(400, title="Answer Not Submitted", message="Only instructors and teaching assistants can submit an answer on behalf of a group.")
        if group_uuid and user_uuid:
            abort(400, title="Answer Not Submitted", message="You cannot submit an answer for a user and a group at the same time.")

        user = User.get_by_uuid_or_404(user_uuid) if user_uuid else current_user
        group = Group.get_active_by_uuid_or_404(group_uuid) if group_uuid else None

        if restrict_user and assignment.enable_group_answers and not group:
            group = current_user.get_course_group(course.id)
            if group == None:
                abort(400, title="Answer Not Submitted",
                    message="You are currently not in any group for this course. Please contact your instructor to be added to a group.")

        check_for_existing_answers = False
        if group and assignment.enable_group_answers:
            if group.course_id != course.id:
                abort(400, title="Answer Not Submitted",
                    message="Group answers can be submitted to courses they belong in.")

            answer.user_id = None
            answer.group_id = group.id
            answer.comparable = True
            check_for_existing_answers = True
        else:
            answer.user_id = user.id
            answer.group_id = None

            course_role = User.get_user_course_role(answer.user_id, course.id)

            # only system admin can add answers for themselves to a class without being enrolled in it
            # required for managing comparison examples as system admin
            if (not course_role or course_role == CourseRole.dropped) and current_user.system_role != SystemRole.sys_admin:
                abort(400, title="Answer Not Submitted", message="Answers can be submitted only by those enrolled in the course. Please double-check your enrollment in this course.")

            if course_role == CourseRole.student and assignment.enable_group_answers:
                abort(400, title="Answer Not Submitted", message="Students can only submit group answers for this assignment.")

            # we allow instructor and TA to submit multiple answers for their own,
            # but not for student. Each student can only have one answer.
            if course_role and course_role == CourseRole.student:
                check_for_existing_answers = True
                answer.comparable = True
            else:
                # instructor / TA / Sys Admin can mark the answer as non-comparable, unless the answer is for a student
                answer.comparable = params.get("comparable")

        if check_for_existing_answers:
            # check for answers with user_id or group_id
            prev_answers = Answer.query \
                .filter_by(
                    assignment_id=assignment.id,
                    user_id=answer.user_id,
                    group_id=answer.group_id,
                    active=True
                ) \
                .all()

            # check if there is a previous answer submitted for the student
            non_draft_answers = [prev_answer for prev_answer in prev_answers if not prev_answer.draft]
            if len(non_draft_answers) > 0:
                abort(400, title="Answer Not Submitted", message="An answer has already been submitted for this assignment by you or on your behalf.")

            # check if there is a previous draft answer submitted for the student (soft-delete if present)
            draft_answers = [prev_answer for prev_answer in prev_answers if prev_answer.draft]
            for draft_answer in draft_answers:
                draft_answer.active = False

        # set submission date if answer is being submitted for the first time
        if not answer.draft and not answer.submission_date:
            answer.submission_date = datetime.datetime.utcnow()

        answer.update_attempt(
            params.get('attempt_uuid'),
            params.get('attempt_started', None),
            params.get('attempt_ended', None)
        )

        db.session.add(answer)
        db.session.commit()

        on_answer_create.send(
            self,
            event_name=on_answer_create.name,
            user=current_user,
            course_id=course.id,
            answer=answer,
            data=marshal(answer, dataformat.get_answer(restrict_user)))

        if attachment:
            on_attach_file.send(
                self,
                event_name=on_attach_file.name,
                user=current_user,
                course_id=course.id,
                file=attachment,
                data={'answer_id': answer.id, 'file_id': attachment.id})

        # update course & assignment grade for user if answer is fully submitted
        if not answer.draft:
            if answer.user:
                assignment.calculate_grade(answer.user)
                course.calculate_grade(answer.user)
            elif answer.group:
                assignment.calculate_group_grade(answer.group)
                course.calculate_group_grade(answer.group)

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
            joinedloads=['file', 'user', 'group', 'score']
        )
        require(READ, answer,
            title="Answer Unavailable",
            message="Sorry, your role in this course does not allow you to view this answer.")
        restrict_user = not can(MANAGE, assignment)

        on_answer_get.send(
            self,
            event_name=on_answer_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id, 'answer_id': answer.id})

        # don't include score/rank unless the user is non-restricted
        include_score = not restrict_user

        return marshal(answer, dataformat.get_answer(restrict_user, include_score=include_score))

    @login_required
    def post(self, course_uuid, assignment_uuid, answer_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)

        if not assignment.answer_grace and not can(MANAGE, assignment):
            abort(403, title="Answer Not Submitted", message="Sorry, the answer deadline has passed. No answers can be submitted after the deadline unless the instructor submits the answer for you.")

        answer = Answer.get_active_by_uuid_or_404(answer_uuid)

        old_file = answer.file

        require(EDIT, answer,
            title="Answer Not Saved",
            message="Sorry, your role in this course does not allow you to save this answer.")
        restrict_user = not can(MANAGE, assignment)

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS and answer.user_id in DemoDataFixture.DEFAULT_STUDENT_IDS:
                abort(400, title="Answer Not Saved", message="Sorry, you cannot edit the default student demo answers.")

        params = existing_answer_parser.parse_args()
        # make sure the answer id in the url and the id matches
        if params['id'] != answer_uuid:
            abort(400, title="Answer Not Submitted", message="The answer's ID does not match the URL, which is required in order to save the answer.")

        # modify answer according to new values, preserve original values if values not passed
        answer.content = params.get("content")

        user_uuid = params.get("user_id")
        group_uuid = params.get("group_id")
        # we allow instructor and TA to submit multiple answers for other users in the class
        if user_uuid and user_uuid != answer.user_uuid and not can(MANAGE, answer):
            abort(400, title="Answer Not Submitted", message="Only instructors and teaching assistants can submit an answer on behalf of another.")
        if group_uuid and not assignment.enable_group_answers:
            abort(400, title="Answer Not Submitted", message="Group answers are not allowed for this assignment.")
        if group_uuid and group_uuid != answer.group_uuid and not can(MANAGE, answer):
            abort(400, title="Answer Not Submitted", message="Only instructors and teaching assistants can submit an answer on behalf of a group.")
        if group_uuid and user_uuid:
            abort(400, title="Answer Not Submitted", message="You cannot submit an answer for a user and a group at the same time.")

        user = User.get_by_uuid_or_404(user_uuid) if user_uuid else answer.user
        group = Group.get_active_by_uuid_or_404(group_uuid) if group_uuid else answer.group

        check_for_existing_answers = False
        if group and assignment.enable_group_answers:
            if group.course_id != course.id:
                abort(400, title="Answer Not Submitted",
                    message="Group answers can be submitted to courses they belong in.")

            answer.user_id = None
            answer.group_id = group.id
            answer.comparable = True
            check_for_existing_answers = True
        else:
            answer.user_id = user.id
            answer.group_id = None

            course_role = User.get_user_course_role(answer.user_id, course.id)

            # only system admin can add answers for themselves to a class without being enrolled in it
            # required for managing comparison examples as system admin
            if (not course_role or course_role == CourseRole.dropped) and current_user.system_role != SystemRole.sys_admin:
                abort(400, title="Answer Not Submitted", message="Answers can be submitted only by those enrolled in the course. Please double-check your enrollment in this course.")

            if course_role == CourseRole.student and assignment.enable_group_answers:
                abort(400, title="Answer Not Submitted", message="Students can only submit group answers for this assignment.")

            # we allow instructor and TA to submit multiple answers for their own,
            # but not for student. Each student can only have one answer.
            if course_role and course_role == CourseRole.student:
                check_for_existing_answers = True
                answer.comparable = True
            else:
                # instructor / TA / Sys Admin can mark the answer as non-comparable, unless the answer is for a student
                answer.comparable = params.get("comparable")

        if check_for_existing_answers:
            # check for answers with user_id or group_id
            prev_answers = Answer.query \
                .filter_by(
                    assignment_id=assignment.id,
                    user_id=answer.user_id,
                    group_id=answer.group_id,
                    active=True
                ) \
                .filter(Answer.id != answer.id) \
                .all()

            # check if there is a previous answer submitted for the student
            non_draft_answers = [prev_answer for prev_answer in prev_answers if not prev_answer.draft]
            if len(non_draft_answers) > 0:
                abort(400, title="Answer Not Submitted", message="An answer has already been submitted for this assignment by you or on your behalf.")

            # check if there is a previous draft answer submitted for the student (soft-delete if present)
            draft_answers = [prev_answer for prev_answer in prev_answers if prev_answer.draft]
            for draft_answer in draft_answers:
                draft_answer.active = False

        # can only change draft status while a draft
        if answer.draft:
            answer.draft = params.get("draft")

        file_uuid = params.get('file_id')
        attachment=None
        if file_uuid:
            attachment = File.get_by_uuid_or_404(file_uuid)
            answer.file_id = attachment.id
        else:
            answer.file_id = None

        # non-drafts must have content
        if not answer.draft and not answer.content and not file_uuid:
            abort(400, title="Answer Not Submitted", message="Please provide content in the text editor or upload a file and try submitting again.")

        # set submission date if answer is being submitted for the first time
        if not answer.draft and not answer.submission_date:
            answer.submission_date = datetime.datetime.utcnow()

        answer.update_attempt(
            params.get('attempt_uuid'),
            params.get('attempt_started', None),
            params.get('attempt_ended', None)
        )

        model_changes = get_model_changes(answer)
        db.session.add(answer)
        db.session.commit()

        on_answer_modified.send(
            self,
            event_name=on_answer_modified.name,
            user=current_user,
            course_id=course.id,
            answer=answer,
            data=model_changes)

        if old_file and (not attachment or old_file.id != attachment.id):
            on_detach_file.send(
                self,
                event_name=on_detach_file.name,
                user=current_user,
                course_id=course.id,
                file=old_file,
                answer=answer,
                data={'answer_id': answer.id, 'file_id': old_file.id})

        if attachment and (not old_file or old_file.id != attachment.id):
            on_attach_file.send(
                self,
                event_name=on_attach_file.name,
                user=current_user,
                course_id=course.id,
                file=attachment,
                data={'answer_id': answer.id, 'file_id': attachment.id})

        # update course & assignment grade for user if answer is fully submitted
        if not answer.draft:
            if answer.user:
                assignment.calculate_grade(answer.user)
                course.calculate_grade(answer.user)
            elif answer.group:
                assignment.calculate_group_grade(answer.group)
                course.calculate_group_grade(answer.group)

        return marshal(answer, dataformat.get_answer(restrict_user))

    @login_required
    def delete(self, course_uuid, assignment_uuid, answer_uuid):
        course = Course.get_active_by_uuid_or_404(course_uuid)
        assignment = Assignment.get_active_by_uuid_or_404(assignment_uuid)
        answer = Answer.get_active_by_uuid_or_404(answer_uuid)
        require(DELETE, answer,
            title="Answer Not Deleted",
            message="Sorry, your role in this course does not allow you to delete this answer.")

        if current_app.config.get('DEMO_INSTALLATION', False):
            from data.fixtures import DemoDataFixture
            if assignment.id in DemoDataFixture.DEFAULT_ASSIGNMENT_IDS and answer.user_id in DemoDataFixture.DEFAULT_STUDENT_IDS:
                abort(400, title="Answer Not Deleted", message="Sorry, you cannot delete the default student demo answers.")

        answer.active = False
        db.session.commit()

        # update course & assignment grade for user if answer was fully submitted
        if not answer.draft:
            if answer.user:
                assignment.calculate_grade(answer.user)
                course.calculate_grade(answer.user)
            elif answer.group:
                assignment.calculate_group_grade(answer.group)
                course.calculate_group_grade(answer.group)

        on_answer_delete.send(
            self,
            event_name=on_answer_delete.name,
            user=current_user,
            course_id=course.id,
            answer=answer,
            data={'assignment_id': assignment.id, 'answer_id': answer.id})

        return {'id': answer.uuid}


api.add_resource(AnswerIdAPI, '/<answer_uuid>')


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
            message="Sorry, your role in this course does not allow you to view answers for this assignment.")
        restrict_user = not can(MANAGE, assignment)

        params = user_answer_list_parser.parse_args()

        query = Answer.query \
            .options(joinedload('comments')) \
            .options(joinedload('file')) \
            .options(joinedload('user')) \
            .options(joinedload('group')) \
            .options(joinedload('score')) \
            .filter_by(
                active=True,
                assignment_id=assignment.id,
                course_id=course.id,
                draft=params.get('draft')
            )

        # get group and individual answers for user if applicable
        group = current_user.get_course_group(course.id)
        if group:
            query = query.filter(or_(
                Answer.user_id == current_user.id,
                Answer.group_id == group.id
            ))
        # get just individual answers for user
        else:
            query = query.filter(Answer.user_id == current_user.id)

        answers = query.all()

        on_user_answer_get.send(
            self,
            event_name=on_user_answer_get.name,
            user=current_user,
            course_id=course.id,
            data={'assignment_id': assignment.id})

        return {"objects": marshal(answers, dataformat.get_answer(restrict_user))}


api.add_resource(AnswerUserIdAPI, '/user')

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
            title="Answer Not Added",
            message="Your role in this course does not allow you to add to the list of instructor-picked answers.")

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
