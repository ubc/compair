from tincan import  Activity, ActivityDefinition, LanguageMap, Extensions

import pytz

from flask import current_app
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.xapi.actor import XAPIActor
from compair.learning_records.xapi.activity import XAPIActivity

class XAPIObject(object):
    @classmethod
    def _basic_attempt(cls, attempt_mixin_object):
        ret = {}

        if attempt_mixin_object.attempt_duration:
            ret["duration"] = attempt_mixin_object.attempt_duration

        if attempt_mixin_object.attempt_started:
            ret["startedAtTime"] = attempt_mixin_object.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        if attempt_mixin_object.attempt_ended:
            ret["endedAtTime"] = attempt_mixin_object.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        return ret

    @classmethod
    def compair(cls):
        activity = Activity(
            id=ResourceIRI.compair(),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('service'),
                name=LanguageMap({ 'en-US': "ComPAIR" }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/version'] = current_app.config.get('COMPAIR_VERSION')

        return activity

    @classmethod
    def criterion(cls, criterion):
        activity = Activity(
            id=ResourceIRI.criterion(criterion.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(criterion.name) })
            )
        )
        if criterion.description:
            activity.definition.description = LanguageMap({
                'en-US': LearningRecord.trim_text_to_size_limit(criterion.description)
            })

        return activity


    @classmethod
    def course(cls, course):
        activity = Activity(
            id=ResourceIRI.course(course.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('course'),
                name=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(course.name) })
            )
        )

        return activity

    @classmethod
    def group(cls, group):
        activity = Activity(
            id=ResourceIRI.group(group.course_uuid, group.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('group'),
                name=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(group.name) }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/members'] = [
            XAPIActor.generate_actor(uc.user) for uc in group.user_courses.all()
        ]

        return activity

    @classmethod
    def assignment(cls, assignment):
        activity = Activity(
            id=ResourceIRI.assignment(assignment.course_uuid, assignment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('assessment'),
                name=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(assignment.name) })
            )
        )
        if assignment.description:
            activity.definition.description = LanguageMap({
                'en-US': LearningRecord.trim_text_to_size_limit(assignment.description)
            })

        return activity

    @classmethod
    def assignment_attempt(cls, assignment, attempt_mixin_object):
        activity = Activity(
            id=ResourceIRI.assignment_attempt(assignment.course_uuid, assignment.uuid, attempt_mixin_object.attempt_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('attempt'),
                extensions=Extensions()
            )
        )
        activity.definition.extensions["http://id.tincanapi.com/extension/attempt"] = cls._basic_attempt(attempt_mixin_object)

        return activity

    @classmethod
    def assignment_question(cls, assignment):
        activity = Activity(
            id=ResourceIRI.assignment_question(assignment.course_uuid, assignment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(assignment.name) })
            )
        )
        if assignment.description:
            activity.definition.description = LanguageMap({
                'en-US': LearningRecord.trim_text_to_size_limit(assignment.description)
            })

        return activity

    @classmethod
    def answer(cls, answer):
        activity = Activity(
            id=ResourceIRI.answer(answer.course_uuid, answer.assignment_uuid, answer.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/isDraft'] = answer.draft

        return activity

    @classmethod
    def answer_attempt(cls, answer):
        activity = Activity(
            id=ResourceIRI.answer_attempt(answer.course_uuid, answer.assignment_uuid, answer.attempt_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('attempt'),
                extensions=Extensions()
            )
        )
        activity.definition.extensions["http://id.tincanapi.com/extension/attempt"] = cls._basic_attempt(answer)

        return activity


    @classmethod
    def comparison_question(cls, assignment, comparison_number):
        return Activity(
            id=ResourceIRI.comparison_question(assignment.course_uuid, assignment.uuid, comparison_number),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': "Assignment comparison #"+str(comparison_number) })
            )
        )

    @classmethod
    def comparison(cls, comparison):
        activity = Activity(
            id=ResourceIRI.comparison(comparison.course_uuid, comparison.assignment_uuid, comparison.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                name=LanguageMap({ 'en-US': "Assignment comparison" }),
                extensions=Extensions()
            )
        )

        activity.definition.extensions['http://id.tincanapi.com/extension/completed'] = comparison.completed

        return activity

    @classmethod
    def comparison_attempt(cls, comparison, current_comparison):
        activity = Activity(
            id=ResourceIRI.comparison_attempt(comparison.course_uuid, comparison.assignment_uuid,
                current_comparison, comparison.attempt_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('attempt'),
                extensions=Extensions()
            )
        )
        activity.definition.extensions["http://id.tincanapi.com/extension/attempt"] = cls._basic_attempt(comparison)

        return activity



    @classmethod
    def evaluation_question(cls, assignment, evaluation_number):
        activity = Activity(
            id=ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, evaluation_number),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': "Assignment Answer Evaluation #"+str(evaluation_number) }),
            )
        )
        if assignment.peer_feedback_prompt:
            activity.definition.description = LanguageMap({
                'en-US': LearningRecord.trim_text_to_size_limit(assignment.peer_feedback_prompt)
            })

        return activity

    @classmethod
    def evaluation_response(cls, answer_comment):
        activity = Activity(
            id=ResourceIRI.evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                description=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(answer_comment.content) }),
                extensions=Extensions()
            )
        )

        activity.definition.extensions['http://id.tincanapi.com/extension/isDraft'] = answer_comment.draft

        return activity

    @classmethod
    def evaluation_attempt(cls, answer_comment, evaluation_number):
        activity = Activity(
            id=ResourceIRI.evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                evaluation_number, answer_comment.attempt_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('attempt'),
                description=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(answer_comment.content) }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions["http://id.tincanapi.com/extension/attempt"] = cls._basic_attempt(answer_comment)

        return activity



    @classmethod
    def self_evaluation_question(cls, assignment):
        return Activity(
            id=ResourceIRI.self_evaluation_question(assignment.course_uuid, assignment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': "Assignment self-evaluation" })
            )
        )

    @classmethod
    def self_evaluation_response(cls, answer_comment):
        activity = Activity(
            id=ResourceIRI.self_evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                extensions=Extensions()
            )
        )

        activity.definition.extensions['http://id.tincanapi.com/extension/isDraft'] = answer_comment.draft

        return activity

    @classmethod
    def self_evaluation_attempt(cls, answer_comment):
        activity = Activity(
            id=ResourceIRI.self_evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.attempt_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('attempt'),
                description=LanguageMap({ 'en-US': LearningRecord.trim_text_to_size_limit(answer_comment.content) }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions["http://id.tincanapi.com/extension/attempt"] = cls._basic_attempt(answer_comment)

        return activity



    @classmethod
    def answer_comment(cls, answer_comment):
        activity = Activity(
            id=ResourceIRI.answer_comment(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('comment'),
                name=LanguageMap({ 'en-US': "Assignment answer comment" }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/type'] = answer_comment.comment_type.value
        activity.definition.extensions['http://id.tincanapi.com/extension/isDraft'] = answer_comment.draft

        return activity


    @classmethod
    def answer_attachment(cls, file, mimetype):
        activity = Activity(
            id=ResourceIRI.attachment(file.name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': file.alias if file.alias else "" }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/mime-type'] = mimetype

        return activity

    @classmethod
    def assignment_attachment(cls, file, mimetype):
        activity = Activity(
            id=ResourceIRI.attachment(file.name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': file.alias if file.alias else "" }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/mime-type'] = mimetype

        return activity

    @classmethod
    def report(cls, file_name, mimetype):
        activity = Activity(
            id=ResourceIRI.report(file_name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': file_name if file_name else "" }),
                extensions=Extensions()
            )
        )
        activity.definition.extensions['http://id.tincanapi.com/extension/mime-type'] = mimetype

        return activity