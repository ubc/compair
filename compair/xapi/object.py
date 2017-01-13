from tincan import  Activity, ActivityDefinition, LanguageMap, Extensions

from .resource_iri import XAPIResourceIRI
from .activity import XAPIActivity
from .extension import XAPIExtension

class XAPIObject(object):
    @classmethod
    def compair(cls):
        return Activity(
            id=XAPIResourceIRI.compair(),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('service'),
                name=LanguageMap({ 'en-US': "ComPAIR" })
            )
        )

    @classmethod
    def user_profile(cls, user):
        return Activity(
            id=XAPIResourceIRI.user_profile(user.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('user profile'),
                name=LanguageMap({ 'en-US': "user profile" })
            )
        )

    @classmethod
    def course(cls, course):
        activity = Activity(
            id=XAPIResourceIRI.course(course.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('course'),
                name=LanguageMap({ 'en-US': course.name })
            )
        )
        if course.description:
            activity.definition.description = LanguageMap({ 'en-US': course.description })

        return activity

    @classmethod
    def assignment(cls, assignment):
        activity = Activity(
            id=XAPIResourceIRI.assignment(assignment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('assessment'),
                name=LanguageMap({ 'en-US': assignment.name })
            )
        )
        if assignment.description:
            activity.definition.description = LanguageMap({ 'en-US': assignment.description })

        return activity

    @classmethod
    def assignment_question(cls, assignment):
        activity = Activity(
            id=XAPIResourceIRI.assignment_question(assignment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': assignment.name }),
                description=LanguageMap({ 'en-US': assignment.description })
            )
        )
        if assignment.description:
            activity.definition.description = LanguageMap({ 'en-US': assignment.description })

        return activity

    @classmethod
    def comparison_question(cls, comparison, comparison_number, pairing_algorithm):
        activity = Activity(
            id=XAPIResourceIRI.comparison_question(comparison.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': "Assignment comparison #"+str(int(comparison_number)) }),
                extensions=Extensions()
            )
        )

        activity.definition.extensions[XAPIExtension.object_extensions.get('comparison')] = comparison_number
        activity.definition.extensions[XAPIExtension.object_extensions.get('pair algorithm')] = pairing_algorithm

        return activity

    @classmethod
    def criterion(cls, criterion):
        activity = Activity(
            id=XAPIResourceIRI.criterion(criterion.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': criterion.name })
            )
        )
        if criterion.description:
            activity.definition.description = LanguageMap({ 'en-US': criterion.description })

        return activity

    @classmethod
    def self_evaluation_question(cls, answer_comment):
        return Activity(
            id=XAPIResourceIRI.self_evaluation_question(answer_comment.assignment_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('question'),
                name=LanguageMap({ 'en-US': "Assignment self-evaluation" })
            )
        )

    @classmethod
    def answer(cls, answer):
        return Activity(
            id=XAPIResourceIRI.answer(answer.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                name=LanguageMap({ 'en-US': "Assignment answer" })
            )
        )

    @classmethod
    def answer_evaluation(cls, answer, comparison):
        return cls.answer(answer)

    @classmethod
    def answer_evaluation_on_criterion(cls, answer, comparison_criterion):
        return Activity(
            id=XAPIResourceIRI.answer_criterion(answer.uuid, comparison_criterion.criterion_uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                name=LanguageMap({ 'en-US': "Assignment answer based on criterion" })
            )
        )

    @classmethod
    def answer_comment(cls, answer_comment):
        return Activity(
            id=XAPIResourceIRI.answer_comment(answer_comment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('comment'),
                name=LanguageMap({ 'en-US': "Assignment answer comment" })
            )
        )

    @classmethod
    def assignment_comment(cls, assignment_comment):
        return Activity(
            id=XAPIResourceIRI.assignment_comment(assignment_comment.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('comment'),
                name=LanguageMap({ 'en-US': "Assignment comment" })
            )
        )

    @classmethod
    def answer_evaluation_comment(cls, answer_comment):
        activity = cls.answer_comment(answer_comment)
        activity.definition.name = LanguageMap({ 'en-US': "Assignment answer evaluation comment" })
        return activity

    @classmethod
    def self_evaluation(cls, answer_comment):
        activity = cls.answer_comment(answer_comment)
        activity.definition.type = XAPIActivity.activity_types.get('review')
        activity.definition.name = LanguageMap({ 'en-US': "Assignment self-evaluation review" })
        return activity

    @classmethod
    def answer_attachment(cls, file):
        return Activity(
            id=XAPIResourceIRI.attachment(file.name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': "Assignment answer attachment" })
            )
        )

    @classmethod
    def assignment_attachment(cls, file):
        return Activity(
            id=XAPIResourceIRI.attachment(file.name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': "Assignment attachment" })
            )
        )

    @classmethod
    def report(cls, file_name):
        return Activity(
            id=XAPIResourceIRI.report(file_name),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('file'),
                name=LanguageMap({ 'en-US': "Report" })
            )
        )

    @classmethod
    def comparison(cls, comparison):
        return Activity(
            id=XAPIResourceIRI.comparison(comparison.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                name=LanguageMap({ 'en-US': "Assignment comparison" })
            )
        )

    @classmethod
    def comparison_criterion(cls, comparison, comparison_criterion):
        return Activity(
            id=XAPIResourceIRI.comparison_criterion(comparison_criterion.uuid),
            definition=ActivityDefinition(
                type=XAPIActivity.activity_types.get('solution'),
                name=LanguageMap({ 'en-US': "Assignment criterion comparison" })
            )
        )