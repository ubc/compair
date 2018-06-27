# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)

import mimetypes
import caliper

from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord

from compair.learning_records.xapi import XAPIActivity, XAPIActor, XAPIContext, \
    XAPIObject, XAPIResult, XAPIStatement, XAPIVerb, XAPI
from compair.learning_records.caliper import CaliperSensor, CaliperEntities, CaliperEvent, \
    CaliperActor

from compair.models import AnswerCommentType, File

from compair.api import on_get_file
from compair.api.file import  on_attach_file, on_detach_file
from compair.api.users import on_user_modified
from compair.api.answer_comment import on_answer_comment_create, on_answer_comment_modified, on_answer_comment_delete
from compair.api.answer import on_answer_create, on_answer_modified, on_answer_delete
from compair.api.assignment import on_assignment_create, on_assignment_modified, on_assignment_delete
from compair.api.comparison import on_comparison_update
from compair.api.course import on_course_create, on_course_duplicate, on_course_modified, on_course_delete
from compair.api.criterion import on_criterion_create, on_criterion_update
from compair.api.login import on_login_with_method, on_logout

def capture_events():
    # authentication events
    on_login_with_method.connect(learning_record_on_login_with_method)
    on_logout.connect(learning_record_on_logout)

    # file events
    on_get_file.connect(learning_record_on_get_file)
    on_attach_file.connect(learning_record_on_attach_file)
    on_detach_file.connect(learning_record_on_detach_file)

    # user events
    on_user_modified.connect(learning_record_on_user_modified)

    # answer comment events
    on_answer_comment_create.connect(learning_record_on_answer_comment_create)
    on_answer_comment_modified.connect(learning_record_on_answer_comment_modified)
    on_answer_comment_delete.connect(learning_record_on_answer_comment_delete)

    # answer events
    on_answer_create.connect(learning_record_on_answer_create)
    on_answer_modified.connect(learning_record_on_answer_modified)
    on_answer_delete.connect(learning_record_on_answer_delete)

    # assignment events
    on_assignment_create.connect(learning_record_on_assignment_create)
    on_assignment_modified.connect(learning_record_on_assignment_modified)
    on_assignment_delete.connect(learning_record_on_assignment_delete)

    # comparison events
    on_comparison_update.connect(learning_record_on_comparison_update)

    # course events
    on_course_create.connect(learning_record_on_course_create)
    on_course_duplicate.connect(learning_record_on_course_create)
    on_course_modified.connect(learning_record_on_course_modified)
    on_course_delete.connect(learning_record_on_course_delete)

    # criterion events
    on_criterion_create.connect(learning_record_on_criterion_create)
    on_criterion_update.connect(learning_record_on_criterion_update)

# on_login_with_method
# logged in to compair
def learning_record_on_login_with_method(sender, user, **extra):
    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('logged in'),
            object=XAPIObject.compair(),
            context=XAPIContext.basic(),
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.SessionEvent(
            action=caliper.constants.CALIPER_ACTIONS["LOGGED_IN"],
            profile=caliper.constants.CALIPER_PROFILES['SESSION'],
            object=CaliperEntities.compair_app(),
            **CaliperEvent._defaults(user)
        ))

# on_logout
# logged in to compair
def learning_record_on_logout(sender, user, **extra):
    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('logged out'),
            object=XAPIObject.compair()
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.SessionEvent(
            action=caliper.constants.CALIPER_ACTIONS["LOGGED_OUT"],
            profile=caliper.constants.CALIPER_PROFILES['SESSION'],
            object=CaliperEntities.compair_app(),
            **CaliperEvent._defaults(user)
        ))

# on_get_file
# download report (report)
# download assignment_attachment (attachment with assignment)
# download answer_attachment (attachment with answer)
def learning_record_on_get_file(sender, user, **extra):
    file_type = extra.get('file_type')
    file_name = extra.get('file_name')
    mimetype, encoding = mimetypes.guess_type(file_name)

    # only send when file_type is report
    if file_type and file_type == 'report':
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('downloaded'),
                object=XAPIObject.report(file_name, mimetype)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.ResourceManagementEvent(
                action=caliper.constants.CALIPER_ACTIONS["DOWNLOADED"],
                profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
                object=CaliperEntities.report(file_name, mimetype),
                **CaliperEvent._defaults(user)
            ))

    elif file_type and file_type == 'attachment':
        file_record = File.query.filter_by(name=file_name).first()
        if file_record:
            assignment = file_record.assignments.first()
            answer = file_record.answers.first()

            if assignment:
                if XAPI.enabled():
                    XAPI.emit(XAPIStatement.generate(
                        user=user,
                        verb=XAPIVerb.generate('downloaded'),
                        object=XAPIObject.assignment_attachment(file_record, mimetype),
                        context=XAPIContext.assignment_attachment(assignment)
                    ))

                if CaliperSensor.enabled():
                    CaliperSensor.emit(caliper.events.ResourceManagementEvent(
                        action=caliper.constants.CALIPER_ACTIONS["DOWNLOADED"],
                        profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
                        object=CaliperEntities.assignment_attachment(assignment, file_record, mimetype),
                        **CaliperEvent._defaults(user, course=assignment.course)
                    ))

            elif answer:
                if XAPI.enabled():
                    XAPI.emit(XAPIStatement.generate(
                        user=user,
                        verb=XAPIVerb.generate('downloaded'),
                        object=XAPIObject.answer_attachment(file_record, mimetype),
                        context=XAPIContext.answer_attachment(answer)
                    ))

                if CaliperSensor.enabled():
                    CaliperSensor.emit(caliper.events.ResourceManagementEvent(
                        action=caliper.constants.CALIPER_ACTIONS["DOWNLOADED"],
                        profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
                        object=CaliperEntities.answer_attachment(answer, file_record, mimetype),
                        **CaliperEvent._defaults(user, course=answer.assignment.course)
                    ))

# on_attach_file
# attach assignment_attachment (attachment with assignment)
# attach answer_attachment (attachment with answer)
def learning_record_on_attach_file(sender, user, **extra):
    file_record = extra.get('file')
    mimetype, encoding = mimetypes.guess_type(file_record.name)

    assignment = file_record.assignments.first()
    answer = file_record.answers.first()

    if assignment:
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('attached'),
                object=XAPIObject.assignment_attachment(file_record, mimetype),
                context=XAPIContext.assignment_attachment(assignment)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["ATTACHED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.assignment_attachment(assignment, file_record, mimetype),
                **CaliperEvent._defaults(user, course=assignment.course)
            ))

    elif answer:
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('attached'),
                object=XAPIObject.answer_attachment(file_record, mimetype),
                context=XAPIContext.answer_attachment(answer)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["ATTACHED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.answer_attachment(answer, file_record, mimetype),
                **CaliperEvent._defaults(user, course=answer.assignment.course)
            ))


# on_detach_file
# attach assignment_attachment (attachment with assignment)
# attach answer_attachment (attachment with answer)
def learning_record_on_detach_file(sender, user, **extra):
    file_record = extra.get('file')
    mimetype, encoding = mimetypes.guess_type(file_record.name)

    assignment = extra.get('assignment')
    answer = extra.get('answer')

    if assignment:
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('removed'),
                object=XAPIObject.assignment_attachment(file_record, mimetype),
                context=XAPIContext.assignment_attachment(assignment)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["REMOVED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.assignment_attachment(assignment, file_record, mimetype),
                **CaliperEvent._defaults(user, course=assignment.course)
            ))

    elif answer:
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('removed'),
                object=XAPIObject.answer_attachment(file_record, mimetype),
                context=XAPIContext.answer_attachment(answer)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["REMOVED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.answer_attachment(answer, file_record, mimetype),
                **CaliperEvent._defaults(user, course=answer.assignment.course)
            ))

# on_user_modified
# updated user_profile
def learning_record_on_user_modified(sender, user, **extra):
    changes = extra.get('data', {}).get('changes')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIActor.generate_actor(user),
            result=XAPIResult.basic(changes=changes) if changes else None
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperActor.generate_actor(user),
            extensions={
                "changes": changes
            },
            **CaliperEvent._defaults(user)
        ))

# on_answer_comment_create
# commented answer_comment (public & private)
def learning_record_on_answer_comment_create(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    if answer_comment.comment_type == AnswerCommentType.evaluation:
        evaluation_number = extra.get('evaluation_number')

        if XAPI.enabled():
            if not answer_comment.draft:
                XAPI.emit(XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('commented'),
                    object=XAPIObject.answer_comment(answer_comment),
                    context=XAPIContext.answer_comment(answer_comment, registration=answer_comment.attempt_uuid),
                    result=XAPIResult.basic_content(answer_comment.content)
                ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('completed'),
                object=XAPIObject.evaluation_response(answer_comment),
                context=XAPIContext.evaluation_response(answer_comment, evaluation_number, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic_attempt(answer_comment, answer_comment.content, success=True, completion=not answer_comment.draft)
            ))


        if CaliperSensor.enabled():
            if not answer_comment.draft:
                CaliperSensor.emit(caliper.events.FeedbackEvent(
                    action=caliper.constants.CALIPER_ACTIONS["COMMENTED"],
                    profile=caliper.constants.CALIPER_PROFILES['FEEDBACK'],
                    object=CaliperEntities.answer(answer_comment.answer),
                    generated=CaliperEntities.answer_comment(answer_comment),
                    **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                ))

            CaliperSensor.emit(caliper.events.AssessmentItemEvent(
                action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.evaluation_question(answer_comment.answer.assignment, evaluation_number),
                generated=CaliperEntities.evaluation_response(answer_comment, evaluation_number),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

    elif answer_comment.comment_type == AnswerCommentType.self_evaluation:
        if XAPI.enabled():
            if not answer_comment.draft:
                XAPI.emit(XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('commented'),
                    object=XAPIObject.answer_comment(answer_comment),
                    context=XAPIContext.answer_comment(answer_comment, registration=answer_comment.attempt_uuid),
                    result=XAPIResult.basic_content(answer_comment.content)
                ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('completed'),
                object=XAPIObject.self_evaluation_response(answer_comment),
                context=XAPIContext.self_evaluation_response(answer_comment, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic_attempt(answer_comment, answer_comment.content, success=True, completion=not answer_comment.draft)
            ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('submitted'),
                object=XAPIObject.assignment_attempt(answer_comment.answer.assignment, answer_comment),
                context=XAPIContext.assignment_attempt(answer_comment.answer.assignment, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic(success=True, completion=not answer_comment.draft)
            ))

        if CaliperSensor.enabled():
            if not answer_comment.draft:
                CaliperSensor.emit(caliper.events.FeedbackEvent(
                    action=caliper.constants.CALIPER_ACTIONS["COMMENTED"],
                    profile=caliper.constants.CALIPER_PROFILES['FEEDBACK'],
                    object=CaliperEntities.answer(answer_comment.answer),
                    generated=CaliperEntities.answer_comment(answer_comment),
                    **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                ))

            CaliperSensor.emit(caliper.events.AssessmentItemEvent(
                action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.self_evaluation_question(answer_comment.answer.assignment),
                generated=CaliperEntities.self_evaluation_response(answer_comment),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

            CaliperSensor.emit(caliper.events.AssessmentEvent(
                action=caliper.constants.CALIPER_ACTIONS["SUBMITTED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.assignment(answer_comment.answer.assignment),
                generated=CaliperEntities.assignment_attempt(answer_comment.answer.assignment, answer_comment, answer_comment.user),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

            CaliperSensor.emit(caliper.events.ToolUseEvent(
                action=caliper.constants.CALIPER_ACTIONS["USED"],
                profile=caliper.constants.CALIPER_PROFILES['TOOL_USE'],
                object=CaliperEntities.compair_app(),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

    else:
        # (public or private)

        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('commented'),
                object=XAPIObject.answer_comment(answer_comment),
                context=XAPIContext.answer_comment(answer_comment),
                result=XAPIResult.basic_content(answer_comment.content)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.FeedbackEvent(
                action=caliper.constants.CALIPER_ACTIONS["COMMENTED"],
                profile=caliper.constants.CALIPER_PROFILES['FEEDBACK'],
                object=CaliperEntities.answer(answer_comment.answer),
                generated=CaliperEntities.answer_comment(answer_comment),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))


# on_answer_comment_modified
# drafted evaluation_response (evaluation draft)
# commented evaluation_response (evaluation not draft)
# drafted self_evaluation + suspended self_evaluation_question (self_evaluation draft)
# submitted self_evaluation + completed self_evaluation_question (self_evaluation not draft)
# updated answer_comment (public & private)
def learning_record_on_answer_comment_modified(sender, user, **extra):
    answer_comment = extra.get('answer_comment')
    was_draft = extra.get('was_draft')

    if answer_comment.comment_type == AnswerCommentType.evaluation:
        evaluation_number = extra.get('evaluation_number')

        if XAPI.enabled():
            if not answer_comment.draft:
                XAPI.emit(XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('commented' if was_draft else 'updated'),
                    object=XAPIObject.answer_comment(answer_comment),
                    context=XAPIContext.answer_comment(answer_comment, registration=answer_comment.attempt_uuid),
                    result=XAPIResult.basic_content(answer_comment.content)
                ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('completed'),
                object=XAPIObject.evaluation_response(answer_comment),
                context=XAPIContext.evaluation_response(answer_comment, evaluation_number, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic_attempt(answer_comment, answer_comment.content, success=True, completion=not answer_comment.draft)
            ))


        if CaliperSensor.enabled():
            if not answer_comment.draft:
                if was_draft:
                    CaliperSensor.emit(caliper.events.FeedbackEvent(
                        action=caliper.constants.CALIPER_ACTIONS["COMMENTED"],
                        profile=caliper.constants.CALIPER_PROFILES['FEEDBACK'],
                        object=CaliperEntities.answer(answer_comment.answer),
                        generated=CaliperEntities.answer_comment(answer_comment),
                        **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                    ))
                else:
                    CaliperSensor.emit(caliper.events.Event(
                        action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
                        profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                        object=CaliperEntities.answer_comment(answer_comment),
                        **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                    ))

            CaliperSensor.emit(caliper.events.AssessmentItemEvent(
                action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.evaluation_question(answer_comment.answer.assignment, evaluation_number),
                generated=CaliperEntities.evaluation_response(answer_comment, evaluation_number),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

    elif answer_comment.comment_type == AnswerCommentType.self_evaluation:
        if XAPI.enabled():
            if not answer_comment.draft:
                XAPI.emit(XAPIStatement.generate(
                    user=user,
                    verb=XAPIVerb.generate('commented' if was_draft else 'updated'),
                    object=XAPIObject.answer_comment(answer_comment),
                    context=XAPIContext.answer_comment(answer_comment, registration=answer_comment.attempt_uuid),
                    result=XAPIResult.basic_content(answer_comment.content)
                ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('completed'),
                object=XAPIObject.self_evaluation_response(answer_comment),
                context=XAPIContext.self_evaluation_response(answer_comment, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic_attempt(answer_comment, answer_comment.content, success=True, completion=not answer_comment.draft)
            ))

            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('submitted'),
                object=XAPIObject.assignment_attempt(answer_comment.answer.assignment, answer_comment),
                context=XAPIContext.assignment_attempt(answer_comment.answer.assignment, registration=answer_comment.attempt_uuid),
                result=XAPIResult.basic(success=True, completion=not answer_comment.draft)
            ))

        if CaliperSensor.enabled():
            if not answer_comment.draft:
                if was_draft:
                    CaliperSensor.emit(caliper.events.FeedbackEvent(
                        action=caliper.constants.CALIPER_ACTIONS["COMMENTED"],
                        profile=caliper.constants.CALIPER_PROFILES['FEEDBACK'],
                        object=CaliperEntities.answer(answer_comment.answer),
                        generated=CaliperEntities.answer_comment(answer_comment),
                        **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                    ))
                else:
                    CaliperSensor.emit(caliper.events.Event(
                        action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
                        profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                        object=CaliperEntities.answer_comment(answer_comment),
                        **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
                    ))


            CaliperSensor.emit(caliper.events.AssessmentItemEvent(
                action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.self_evaluation_question(answer_comment.answer.assignment),
                generated=CaliperEntities.self_evaluation_response(answer_comment),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

            CaliperSensor.emit(caliper.events.AssessmentEvent(
                action=caliper.constants.CALIPER_ACTIONS["SUBMITTED"],
                profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
                object=CaliperEntities.assignment(answer_comment.answer.assignment),
                generated=CaliperEntities.assignment_attempt(answer_comment.answer.assignment, answer_comment, answer_comment.user),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

            CaliperSensor.emit(caliper.events.ToolUseEvent(
                action=caliper.constants.CALIPER_ACTIONS["USED"],
                profile=caliper.constants.CALIPER_PROFILES['TOOL_USE'],
                object=CaliperEntities.compair_app(),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))

    else:
        # (public or private)

        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('updated'),
                object=XAPIObject.answer_comment(answer_comment),
                context=XAPIContext.answer_comment(answer_comment),
                result=XAPIResult.basic_content(answer_comment.content)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.answer_comment(answer_comment),
                **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
            ))


# on_answer_comment_delete
# deleted evaluation_response (evaluation)
# deleted self_evaluation (self_evaluation)
# deleted answer_comment (public & private)
def learning_record_on_answer_comment_delete(sender, user, **extra):
    answer_comment = extra.get('answer_comment')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('archived'),
            object=XAPIObject.answer_comment(answer_comment),
            context=XAPIContext.answer_comment(answer_comment)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["ARCHIVED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperEntities.answer_comment(answer_comment),
            **CaliperEvent._defaults(user, course=answer_comment.answer.assignment.course)
        ))


# on_answer_create
# drafted answer_solution + suspended assignment_question (draft)
# submitted answer_solution + completed assignment_question (not draft)
def learning_record_on_answer_create(sender, user, **extra):
    answer = extra.get('answer')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('completed'),
            object=XAPIObject.answer(answer),
            context=XAPIContext.answer(answer, registration=answer.attempt_uuid),
            result=XAPIResult.basic_attempt(answer, answer.content, success=True, completion=not answer.draft)
        ))

        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.assignment_attempt(answer.assignment, answer),
            context=XAPIContext.assignment_attempt(answer.assignment, registration=answer.attempt_uuid),
            result=XAPIResult.basic(success=True, completion=not answer.draft)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.AssessmentItemEvent(
            action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.assignment_question(answer.assignment),
            generated=CaliperEntities.answer(answer),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.AssessmentEvent(
            action=caliper.constants.CALIPER_ACTIONS["SUBMITTED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.assignment(answer.assignment),
            generated=CaliperEntities.assignment_attempt(answer.assignment, answer, user),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.ToolUseEvent(
            action=caliper.constants.CALIPER_ACTIONS["USED"],
            profile=caliper.constants.CALIPER_PROFILES['TOOL_USE'],
            object=CaliperEntities.compair_app(),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))

# on_answer_modified
# drafted answer_solution + suspended assignment_question (draft)
# submitted answer_solution + completed assignment_question (not draft)
def learning_record_on_answer_modified(sender, user, **extra):
    answer = extra.get('answer')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('completed'),
            object=XAPIObject.answer(answer),
            context=XAPIContext.answer(answer, registration=answer.attempt_uuid),
            result=XAPIResult.basic_attempt(answer, answer.content, success=True, completion=not answer.draft)
        ))

        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.assignment_attempt(answer.assignment, answer),
            context=XAPIContext.assignment_attempt(answer.assignment, registration=answer.attempt_uuid),
            result=XAPIResult.basic(success=True, completion=not answer.draft)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.AssessmentItemEvent(
            action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.assignment_question(answer.assignment),
            generated=CaliperEntities.answer(answer),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.AssessmentEvent(
            action=caliper.constants.CALIPER_ACTIONS["SUBMITTED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.assignment(answer.assignment),
            generated=CaliperEntities.assignment_attempt(answer.assignment, answer, user),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.ToolUseEvent(
            action=caliper.constants.CALIPER_ACTIONS["USED"],
            profile=caliper.constants.CALIPER_PROFILES['TOOL_USE'],
            object=CaliperEntities.compair_app(),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))


# on_answer_delete
# deleted answer_solution
def learning_record_on_answer_delete(sender, user, **extra):
    answer = extra.get('answer')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('archived'),
            object=XAPIObject.answer(answer),
            context=XAPIContext.answer(answer)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["ARCHIVED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperEntities.answer(answer),
            **CaliperEvent._defaults(user, course=answer.assignment.course)
        ))


# on_assignment_create
# authored assignment_assessment
def learning_record_on_assignment_create(sender, user, **extra):
    assignment = extra.get('assignment')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('authored'),
            object=XAPIObject.assignment(assignment),
            context=XAPIContext.assignment(assignment)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.ResourceManagementEvent(
            action=caliper.constants.CALIPER_ACTIONS["CREATED"],
            profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
            object=CaliperEntities.assignment(assignment),
            **CaliperEvent._defaults(user, course=assignment.course)
        ))


# on_assignment_modified
# updated assignment_assessment
def learning_record_on_assignment_modified(sender, user, **extra):
    assignment = extra.get('assignment')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.assignment(assignment),
            context=XAPIContext.assignment(assignment)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.ResourceManagementEvent(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
            object=CaliperEntities.assignment(assignment),
            **CaliperEvent._defaults(user, course=assignment.course)
        ))


# on_assignment_delete
# deleted assignment_assessment
def learning_record_on_assignment_delete(sender, user, **extra):
    assignment = extra.get('assignment')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('archived'),
            object=XAPIObject.assignment(assignment),
            context=XAPIContext.assignment(assignment)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.ResourceManagementEvent(
            action=caliper.constants.CALIPER_ACTIONS["ARCHIVED"],
            profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
            object=CaliperEntities.assignment(assignment),
            **CaliperEvent._defaults(user, course=assignment.course)
        ))


# on_comparison_update
# drafted comparison_solution(s) + suspended comparison_question (not completed)
# submitted comparison_solution(s) + completed comparison_question (completed)
# evaluated answer_evaluation(s) (completed and was not comparison example)
def learning_record_on_comparison_update(sender, user, **extra):
    assignment = extra.get('assignment')
    comparison = extra.get('comparison')
    is_comparison_example = extra.get('is_comparison_example')

    comparison_count = assignment.completed_comparison_count_for_user(user.id)
    current_comparison = comparison_count if comparison.completed else comparison_count + 1

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('completed'),
            object=XAPIObject.comparison(comparison),
            context=XAPIContext.comparison(comparison, current_comparison, registration=comparison.attempt_uuid),
            result=XAPIResult.comparison(comparison, success=True, completion=comparison.completed)
        ))

        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('submitted'),
            object=XAPIObject.assignment_attempt(comparison.assignment, comparison),
            context=XAPIContext.assignment_attempt(comparison.assignment, registration=comparison.attempt_uuid),
            result=XAPIResult.basic(success=True, completion=comparison.completed)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.AssessmentItemEvent(
            action=caliper.constants.CALIPER_ACTIONS["COMPLETED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.comparison_question(comparison.assignment, current_comparison),
            generated=CaliperEntities.comparison(comparison, current_comparison),
            **CaliperEvent._defaults(user, course=comparison.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.AssessmentEvent(
            action=caliper.constants.CALIPER_ACTIONS["SUBMITTED"],
            profile=caliper.constants.CALIPER_PROFILES['ASSESSMENT'],
            object=CaliperEntities.assignment(comparison.assignment),
            generated=CaliperEntities.assignment_attempt(comparison.assignment, comparison, user),
            **CaliperEvent._defaults(user, course=comparison.assignment.course)
        ))

        CaliperSensor.emit(caliper.events.ToolUseEvent(
            action=caliper.constants.CALIPER_ACTIONS["USED"],
            profile=caliper.constants.CALIPER_PROFILES['TOOL_USE'],
            object=CaliperEntities.compair_app(),
            **CaliperEvent._defaults(user, course=comparison.assignment.course)
        ))


    if not is_comparison_example and comparison.completed:
        if XAPI.enabled():
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('ranked'),
                object=XAPIObject.answer(comparison.answer1),
                context=XAPIContext.answer(comparison.answer1, registration=comparison.attempt_uuid),
                result=XAPIResult.answer_score(comparison.answer1, comparison.answer1.score)
            ))
            XAPI.emit(XAPIStatement.generate(
                user=user,
                verb=XAPIVerb.generate('ranked'),
                object=XAPIObject.answer(comparison.answer2),
                context=XAPIContext.answer(comparison.answer2, registration=comparison.attempt_uuid),
                result=XAPIResult.answer_score(comparison.answer2, comparison.answer2.score)
            ))

        if CaliperSensor.enabled():
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["RANKED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.answer(comparison.answer1),
                **CaliperEvent._defaults(user, course=comparison.assignment.course)
            ))
            CaliperSensor.emit(caliper.events.Event(
                action=caliper.constants.CALIPER_ACTIONS["RANKED"],
                profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
                object=CaliperEntities.answer(comparison.answer2),
                **CaliperEvent._defaults(user, course=comparison.assignment.course)
            ))




# on_course_create
# authored course
def learning_record_on_course_create(sender, user, **extra):
    course = extra.get('course')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('authored'),
            object=XAPIObject.course(course)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["CREATED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperEntities.course(course),
            **CaliperEvent._defaults(user, course=course)
        ))

# on_course_modified
# updated course
def learning_record_on_course_modified(sender, user, **extra):
    course = extra.get('course')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.course(course)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperEntities.course(course),
            **CaliperEvent._defaults(user, course=course)
        ))


# on_course_delete
# updated course
def learning_record_on_course_delete(sender, user, **extra):
    course = extra.get('course')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('archived'),
            object=XAPIObject.course(course)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.Event(
            action=caliper.constants.CALIPER_ACTIONS["ARCHIVED"],
            profile=caliper.constants.CALIPER_PROFILES['GENERAL'],
            object=CaliperEntities.course(course),
            **CaliperEvent._defaults(user, course=course)
        ))


# on_criterion_create
# authored criterion_question
def learning_record_on_criterion_create(sender, user, **extra):
    criterion = extra.get('criterion')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('authored'),
            object=XAPIObject.criterion(criterion)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.ResourceManagementEvent(
            action=caliper.constants.CALIPER_ACTIONS["CREATED"],
            profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
            object=CaliperEntities.criterion(criterion),
            **CaliperEvent._defaults(user)
        ))


# on_criterion_update
# updated criterion_question
def learning_record_on_criterion_update(sender, user, **extra):
    criterion = extra.get('criterion')

    if XAPI.enabled():
        XAPI.emit(XAPIStatement.generate(
            user=user,
            verb=XAPIVerb.generate('updated'),
            object=XAPIObject.criterion(criterion)
        ))

    if CaliperSensor.enabled():
        CaliperSensor.emit(caliper.events.ResourceManagementEvent(
            action=caliper.constants.CALIPER_ACTIONS["MODIFIED"],
            profile=caliper.constants.CALIPER_PROFILES['RESOURCE_MANAGEMENT'],
            object=CaliperEntities.criterion(criterion),
            **CaliperEvent._defaults(user)
        ))