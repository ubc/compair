# only import from compair.xapi

from .activity import XAPIActivity
from .actor import XAPIActor
from .context import XAPIContext
from .extension import XAPIExtension
from .object import XAPIObject
from .resource_iri import XAPIResourceIRI
from .result import XAPIResult
from .statement import XAPIStatement
from .verb import XAPIVerb
from .xapi import XAPI

from compair.models import AnswerCommentType, File

from compair.api import on_get_file
from compair.api.users import on_user_modified
from compair.api.answer_comment import on_answer_comment_create, on_answer_comment_modified, on_answer_comment_delete
from compair.api.answer import on_answer_modified, on_answer_delete, on_answer_flag
from compair.api.assignment import on_assignment_create, on_assignment_modified, on_assignment_delete
from compair.api.comparison import on_comparison_update
from compair.api.course import on_course_create, on_course_duplicate, on_course_modified, on_course_delete
from compair.api.criterion import on_criterion_create, on_criterion_update
from compair.api.login import on_login_with_method, on_logout

from flask_restful.reqparse import RequestParser
tracking_parser = RequestParser()
tracking_parser.add_argument('tracking', type=dict, default=dict())

def capture_xapi_events():
    # authentication events
    on_login_with_method.connect(xapi_on_login_with_method)
    on_logout.connect(xapi_on_logout)

    # file events
    on_get_file.connect(xapi_on_get_file)

    # user events
    on_user_modified.connect(xapi_on_user_modified)

    # answer comment events
    on_answer_comment_create.connect(xapi_on_answer_comment_create)
    on_answer_comment_modified.connect(xapi_on_answer_comment_modified)
    on_answer_comment_delete.connect(xapi_on_answer_comment_delete)

    # answer events
    on_answer_modified.connect(xapi_on_answer_modified)
    on_answer_delete.connect(xapi_on_answer_delete)
    on_answer_flag.connect(xapi_on_answer_flag)

    # assignment events
    on_assignment_create.connect(xapi_on_assignment_create)
    on_assignment_modified.connect(xapi_on_assignment_modified)
    on_assignment_delete.connect(xapi_on_assignment_delete)

    # comparison events
    on_comparison_update.connect(xapi_on_comparison_update)

    # course events
    on_course_create.connect(xapi_on_course_create)
    on_course_duplicate.connect(xapi_on_course_create)
    on_course_modified.connect(xapi_on_course_modified)
    on_course_delete.connect(xapi_on_course_delete)

    # criterion events
    on_criterion_create.connect(xapi_on_criterion_create)
    on_criterion_update.connect(xapi_on_criterion_update)


def _get_tracking_params():
    params = tracking_parser.parse_args()
    return params.get('tracking')

# on_login_with_method
# logged in to compair
def xapi_on_login_with_method(sender, user, **extra):
    login_method = extra.get('login_method')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('logged in'),
        object=XAPIObject.compair(),
        context=XAPIContext.login(login_method),
    )
    XAPI.send_statement(statement)


# on_logout
# logged in to compair
def xapi_on_logout(sender, user, **extra):
    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('logged out'),
        object=XAPIObject.compair()
    )
    XAPI.send_statement(statement)


# on_get_file
# download report (report)
# download assignment_attachment (attachment with assignment)
# download answer_attachment (attachment with answer)
def xapi_on_get_file(sender, user, **extra):
    file_type = extra.get('file_type')
    file_name = extra.get('file_name')

    # only send when file_type is report
    if file_type and file_type == 'report':
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('downloaded'),
            object=XAPIObject.report(file_name)
        )
        XAPI.send_statement(statement)
    elif file_type and file_type == 'attachment':
        file_record = File.query.filter_by(name=file_name).first()
        if file_record:
            assignment = file_record.assignments.first()
            answer = file_record.answers.first()
            if assignment:
                statement = XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('downloaded'),
                    object=XAPIObject.assignment_attachment(file_record),
                    context=XAPIContext.assignment_attachment(assignment)
                )
                XAPI.send_statement(statement)
            elif answer:
                statement = XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('downloaded'),
                    object=XAPIObject.answer_attachment(file_record),
                    context=XAPIContext.answer_attachment(answer)
                )
                XAPI.send_statement(statement)


# on_user_modified
# updated user_profile
def xapi_on_user_modified(sender, user, **extra):
    changes = extra.get('data', {}).get('changes')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('updated'),
        object=XAPIObject.user_profile(user),
        result=XAPIResult.basic(changes=changes) if changes else None
    )
    XAPI.send_statement(statement)


# on_answer_comment_create
# commented answer_comment (public & private)
def xapi_on_answer_comment_create(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    if answer_comment.comment_type in [AnswerCommentType.public, AnswerCommentType.private]:
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('commented'),
            object=XAPIObject.answer_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment),
            result=XAPIResult.answer_comment(answer_comment)
        )
        XAPI.send_statement(statement)


# on_answer_comment_modified
# drafted answer_evaluation_comment (evaluation draft)
# commented answer_evaluation_comment (evaluation not draft)
# drafted self_evaluation + suspended self_evaluation_question (self_evaluation draft)
# submitted self_evaluation + completed self_evaluation_question (self_evaluation not draft)
# updated answer_comment (public & private)
def xapi_on_answer_comment_modified(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    if answer_comment.comment_type == AnswerCommentType.evaluation:
        tracking = _get_tracking_params() # only evaluation and self_evaluation
        registration = tracking.get('registration') # only evaluation and self_evaluation

        verb = XAPIVerb.generate('drafted' if answer_comment.draft else 'commented')
        statement = XAPIStatement.generate(
            user=user,
            verb=verb,
            object=XAPIObject.answer_evaluation_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment, registration=registration),
            result=XAPIResult.answer_comment(answer_comment)
        )
        XAPI.send_statement(statement)

    elif answer_comment.comment_type == AnswerCommentType.self_evaluation:
        tracking = _get_tracking_params() # only evaluation and self_evaluation
        registration = tracking.get('registration') # only evaluation and self_evaluation
        duration = tracking.get('duration') # only self_evaluation
        statements = []

        verb = XAPIVerb.generate('drafted' if answer_comment.draft else 'submitted')
        statement = XAPIStatement.generate(
            user=user,
            verb=verb,
            object=XAPIObject.self_evaluation(answer_comment),
            context=XAPIContext.self_evaluation(answer_comment, registration=registration),
            result=XAPIResult.self_evaluation(answer_comment, success=True if not answer_comment.draft else None)
        )
        statements.append(statement)

        verb = XAPIVerb.generate('suspended' if answer_comment.draft else 'completed')
        statement = XAPIStatement.generate(
            user=user,
            verb=verb,
            object=XAPIObject.self_evaluation_question(answer_comment),
            context=XAPIContext.self_evaluation_question(answer_comment, registration=registration),
            result=XAPIResult.basic(duration=duration, success=True, completion=not answer_comment.draft)
        )
        statements.append(statement)

        for statement in statements:
            XAPI.send_statement(statement)
    else:
        # (public or private)
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.answer_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment),
            result=XAPIResult.answer_comment(answer_comment)
        )
        XAPI.send_statement(statement)


# on_answer_comment_delete
# deleted answer_evaluation_comment (evaluation)
# deleted self_evaluation (self_evaluation)
# deleted answer_comment (public & private)
def xapi_on_answer_comment_delete(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    if answer_comment.comment_type == AnswerCommentType.evaluation:
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('deleted'),
            object=XAPIObject.answer_evaluation_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment)
        )
        XAPI.send_statement(statement)
    elif answer_comment.comment_type == AnswerCommentType.self_evaluation:
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('deleted'),
            object=XAPIObject.self_evaluation(answer_comment),
            context=XAPIContext.self_evaluation(answer_comment)
        )
        XAPI.send_statement(statement)
    else:
        # (public or private)
        statement = XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('deleted'),
            object=XAPIObject.answer_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment)
        )
        XAPI.send_statement(statement)


# on_answer_modified
# drafted answer_solution + suspended assignment_question (draft)
# ubmitted answer_solution + completed assignment_question (not draft)
def xapi_on_answer_modified(sender, user, **extra):
    answer = extra.get('answer')
    assignment = extra.get('assignment')

    tracking = _get_tracking_params()
    registration = tracking.get('registration')
    duration = tracking.get('duration')

    statements = []

    verb = XAPIVerb.generate('drafted' if answer.draft else 'submitted')
    statement = XAPIStatement.generate(
        user=user,
        verb=verb,
        object=XAPIObject.answer(answer),
        context=XAPIContext.answer(answer, registration=registration),
        result=XAPIResult.answer(answer, includeAttachment=True, success=True if not answer.draft else None)
    )
    statements.append(statement)

    verb = XAPIVerb.generate('suspended' if answer.draft else 'completed')
    statement = XAPIStatement.generate(
        user=user,
        verb=verb,
        object=XAPIObject.assignment_question(assignment),
        context=XAPIContext.assignment_question(assignment, registration=registration),
        result=XAPIResult.basic(duration=duration, success=True, completion=not answer.draft)
    )
    statements.append(statement)

    for statement in statements:
        XAPI.send_statement(statement)

# on_answer_delete
# deleted answer_solution
def xapi_on_answer_delete(sender, user, **extra):
    answer = extra.get('answer')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('deleted'),
        object=XAPIObject.answer(answer),
        context=XAPIContext.answer(answer)
    )
    XAPI.send_statement(statement)

# on_answer_flag
# flagged answer_solution
def xapi_on_answer_flag(sender, user, **extra):
    answer = extra.get('answer')

    tracking = _get_tracking_params()
    registration = tracking.get('registration')

    verb = XAPIVerb.generate('flagged' if answer.flagged else 'unflagged')
    statement = XAPIStatement.generate(
        user=user,
        verb=verb,
        object=XAPIObject.answer(answer),
        context=XAPIContext.answer(answer, registration=registration)
    )
    XAPI.send_statement(statement)


# on_assignment_create
# authored assignment_assessment
def xapi_on_assignment_create(sender, user, **extra):
    assignment = extra.get('assignment')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('authored'),
        object=XAPIObject.assignment(assignment),
        context=XAPIContext.assignment(assignment)
    )
    XAPI.send_statement(statement)


# on_assignment_modified
# updated assignment_assessment
def xapi_on_assignment_modified(sender, user, **extra):
    assignment = extra.get('assignment')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('updated'),
        object=XAPIObject.assignment(assignment),
        context=XAPIContext.assignment(assignment)
    )
    XAPI.send_statement(statement)


# on_assignment_delete
# deleted assignment_assessment
def xapi_on_assignment_delete(sender, user, **extra):
    assignment = extra.get('assignment')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('deleted'),
        object=XAPIObject.assignment(assignment),
        context=XAPIContext.assignment(assignment)
    )
    XAPI.send_statement(statement)


# on_comparison_update
# drafted comparison_solution(s) + suspended comparison_question (not completed)
# submitted comparison_solution(s) + completed comparison_question (completed)
# evaluated answer_evaluation(s) (completed and was not comparison example)
def xapi_on_comparison_update(sender, user, **extra):
    assignment = extra.get('assignment')
    comparison = extra.get('comparison')
    is_comparison_example = extra.get('is_comparison_example')

    tracking = _get_tracking_params()
    registration = tracking.get('registration')
    duration = tracking.get('duration')

    comparison_count = assignment.completed_comparison_count_for_user(user.id)
    current_comparison = comparison_count+1
    completed = comparison.completed

    statements = []

    verb = XAPIVerb.generate('drafted' if not completed else 'submitted')
    statement = XAPIStatement.generate(
        user=user,
        verb=verb,
        object=XAPIObject.comparison(comparison),
        context=XAPIContext.comparison(comparison, registration=registration),
        result=XAPIResult.comparison(comparison, success=True if completed else None)
    )
    statements.append(statement)
    for comparison_criterion in comparison.comparison_criteria:
        statement = XAPIStatement.generate(
            user=user,
            verb=verb,
            object=XAPIObject.comparison_criterion(comparison, comparison_criterion),
            context=XAPIContext.comparison_criterion(comparison, comparison_criterion, registration=registration),
            result=XAPIResult.comparison_criterion(comparison, comparison_criterion, success=True if completed else None)
        )
        statements.append(statement)

    verb = XAPIVerb.generate('suspended' if not completed else 'completed')
    statement = XAPIStatement.generate(
        user=user,
        verb=verb,
        object=XAPIObject.comparison_question(comparison, current_comparison, assignment.pairing_algorithm.value),
        context=XAPIContext.comparison_question(comparison, registration=registration),
        result=XAPIResult.basic(duration=duration, success=True, completion=completed)
    )
    statements.append(statement)

    if not is_comparison_example and completed:
        for answer in [comparison.answer1, comparison.answer2]:
            statement = XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('evaluated'),
                object=XAPIObject.answer_evaluation(answer, comparison),
                context=XAPIContext.answer_evaluation(answer, comparison, registration=registration),
                result=XAPIResult.answer_evaluation(answer, answer.score)
            )
            statements.append(statement)

            for criterion_score in answer.criteria_scores:
                comparison_criterion = next((
                    comparison_criterion for comparison_criterion in comparison.comparison_criteria \
                    if comparison_criterion.criterion_id == criterion_score.criterion_id
                ), None )

                if comparison_criterion:
                    statement = XAPIStatement.generate(
                        user=user,
                        verb=XAPIVerb.generate('evaluated'),
                        object=XAPIObject.answer_evaluation_on_criterion(answer, comparison_criterion),
                        context=XAPIContext.answer_evaluation_on_criterion(answer, comparison_criterion, registration=registration),
                        result=XAPIResult.answer_evaluation_on_criterion(answer, criterion_score)
                    )
                    statements.append(statement)

    for statement in statements:
        XAPI.send_statement(statement)


# on_course_create
# authored course
def xapi_on_course_create(sender, user, **extra):
    course = extra.get('course')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('authored'),
        object=XAPIObject.course(course)
    )
    XAPI.send_statement(statement)


# on_course_modified
# updated course
def xapi_on_course_modified(sender, user, **extra):
    course = extra.get('course')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('updated'),
        object=XAPIObject.course(course)
    )
    XAPI.send_statement(statement)


# on_course_delete
# updated course
def xapi_on_course_delete(sender, user, **extra):
    course = extra.get('course')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('deleted'),
        object=XAPIObject.course(course)
    )
    XAPI.send_statement(statement)


# on_criterion_create
# authored criterion_question
def xapi_on_criterion_create(sender, user, **extra):
    criterion = extra.get('criterion')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('authored'),
        object=XAPIObject.criterion(criterion)
    )
    XAPI.send_statement(statement)


# on_criterion_update
# updated criterion_question
def xapi_on_criterion_update(sender, user, **extra):
    criterion = extra.get('criterion')

    statement = XAPIStatement.generate(
        user=user,
        verb=XAPIVerb.generate('updated'),
        object=XAPIObject.criterion(criterion)
    )
    XAPI.send_statement(statement)