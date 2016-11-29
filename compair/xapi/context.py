from tincan import Context, ContextActivities, ActivityList, Activity, Extensions

from .resource_iri import XAPIResourceIRI
from .activity import XAPIActivity
from .extension import XAPIExtension

class XAPIContext(object):
    @classmethod
    def basic(cls, **kwargs):
        context = Context()

        if kwargs:
            if kwargs.get('registration') != None:
                context.registration = kwargs.get('registration')

        return context

    @classmethod
    def login(cls, login_method, **kwargs):
        context = cls.basic(**kwargs)

        if login_method:
            context.extensions = Extensions()
            context.extensions[XAPIExtension.context_extensions.get('login method')] = login_method

        return context

    @classmethod
    def assignment(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is course
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.course(assignment.course_uuid))
            ])
        )

        return context

    @classmethod
    def assignment_question(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment(assignment.uuid))
            ]),
            # grouping is course
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(assignment.course_uuid))
            ])
        )

        return context

    @classmethod
    def comparison_question(cls, comparisons, **kwargs):
        context = cls.basic(**kwargs)

        comparison = comparisons[0]

        context.context_activities = ContextActivities(
            # parent is assignment + answer1 + answer2
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment(comparison.assignment_uuid)),
                Activity(id=XAPIResourceIRI.answer(comparison.answer1_uuid)),
                Activity(id=XAPIResourceIRI.answer(comparison.answer2_uuid))
            ]),
            # grouping is course
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(comparison.course_uuid))
            ])
        )

        for comparison in comparisons:
            context.context_activities.grouping.append(
                Activity(id=XAPIResourceIRI.criterion(comparison.criterion_uuid))
            )

        return context

    @classmethod
    def self_evaluation_question(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment + answer
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment(answer_comment.assignment_uuid)),
                Activity(id=XAPIResourceIRI.answer(answer_comment.answer_uuid))
            ]),
            # grouping is course
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer_comment.course_uuid))
            ])
        )

        return context

    @classmethod
    def answer(cls, answer, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment question
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment_question(answer.assignment_uuid))
            ]),
            # grouping is course + assignment
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(answer.assignment_uuid))
            ])
        )

        return context

    @classmethod
    def answer_evaluation(cls, answer, comparison, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is answer + criterion
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.answer(answer.uuid)),
                Activity(id=XAPIResourceIRI.criterion(comparison.criterion_uuid))
            ]),
            # grouping is course + assignment + assignment question
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(answer.assignment_uuid)),
                Activity(id=XAPIResourceIRI.assignment_question(answer.assignment_uuid))
            ]),
            # other is comparison + comparison question
            other=ActivityList([
                Activity(id=XAPIResourceIRI.comparison(comparison.uuid)),
                Activity(id=XAPIResourceIRI.comparison_question(
                    comparison.assignment_uuid, comparison.answer1_uuid, comparison.answer2_uuid))
            ])
        )

        return context

    @classmethod
    def answer_comment(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment question
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.answer(answer_comment.answer_uuid)),
            ]),
            # grouping is course + assignment + assignment question
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer_comment.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(answer_comment.assignment_uuid)),
                Activity(id=XAPIResourceIRI.assignment_question(answer_comment.assignment_uuid))
            ])
        )

        return context

    @classmethod
    def assignment_comment(cls, assignment_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment(assignment_comment.assignment_uuid)),
            ]),
            # grouping is course
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(assignment_comment.course_uuid))
            ])
        )

        return context

    @classmethod
    def answer_attachment(cls, answer, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment answer
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.answer(answer.uuid))
            ]),
            # grouping is course + assignment + assignment question
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(answer.assignment_uuid)),
                Activity(id=XAPIResourceIRI.assignment_question(answer.assignment_uuid))
            ])
        )

        return context

    @classmethod
    def assignment_attachment(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.assignment(assignment.uuid))
            ]),
            # grouping is course
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(assignment.course_uuid))
            ])
        )

        return context

    @classmethod
    def comparison(cls, comparison, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is comparison question + criterion
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.comparison_question(
                    comparison.assignment_uuid, comparison.answer1_uuid, comparison.answer2_uuid)),
                Activity(id=XAPIResourceIRI.criterion(comparison.criterion_uuid)),
            ]),
            # grouping is course + assignment + answer1 + answer2
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(comparison.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(comparison.assignment_uuid)),
                Activity(id=XAPIResourceIRI.answer(comparison.answer1_uuid)),
                Activity(id=XAPIResourceIRI.answer(comparison.answer2_uuid))
            ])
        )

        return context

    @classmethod
    def self_evaluation(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is self-evaulation question
            parent=ActivityList([
                Activity(id=XAPIResourceIRI.self_evaluation_question(answer_comment.assignment_uuid))
            ]),
            # grouping is course + assignment + answer
            grouping=ActivityList([
                Activity(id=XAPIResourceIRI.course(answer_comment.course_uuid)),
                Activity(id=XAPIResourceIRI.assignment(answer_comment.assignment_uuid)),
                Activity(id=XAPIResourceIRI.answer(answer_comment.answer_uuid))
            ])
        )

        return context