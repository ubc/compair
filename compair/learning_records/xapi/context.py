from tincan import Context, ContextActivities, ActivityList, Activity, Extensions

from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.xapi.activity import XAPIActivity
from compair.learning_records.xapi.object import XAPIObject

class XAPIContext(object):
    @classmethod
    def _add_sis_data(cls, context, course):
        if course.lti_has_sis_data:
            if not context.context_activities:
                context.context_activities = ContextActivities()

            if not context.context_activities.grouping:
                context.context_activities.grouping = ActivityList()

            sis_data = course.lti_sis_data
            context.extensions = Extensions() if not context.extensions else context.extensions
            context.extensions['sis_courses'] = []
            for sis_course_id, sis_section_ids in sis_data.items():
                context.extensions['sis_courses'].append({
                    'id': sis_course_id,
                    'section_ids': sis_section_ids
                })

    @classmethod
    def basic(cls, **kwargs):
        context = Context()

        if kwargs and kwargs.get('registration') != None:
            context.registration = kwargs.get('registration')

        return context

    @classmethod
    def assignment(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is course
            parent=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context

    @classmethod
    def assignment_attempt(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is course
            parent=ActivityList([
                XAPIObject.assignment(assignment)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context



    @classmethod
    def assignment_question(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.assignment(assignment)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context

    @classmethod
    def answer(cls, answer, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment question
            parent=ActivityList([
                XAPIObject.assignment_question(answer.assignment)
            ]),
            # grouping is course + assignment
            grouping=ActivityList([
                XAPIObject.assignment(answer.assignment),
                XAPIObject.course(answer.assignment.course)
            ])
        )

        if answer.attempt_uuid:
            context.context_activities.parent.append(XAPIObject.answer_attempt(answer))

        if answer.group_id != None:
            context.context_activities.parent.append(XAPIObject.group(answer.group))

        cls._add_sis_data(context, answer.assignment.course)
        return context

    @classmethod
    def answer_attempt(cls, answer, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment question
            parent=ActivityList([
                XAPIObject.assignment_question(answer.assignment)
            ]),
            # grouping is course + assignment
            grouping=ActivityList([
                XAPIObject.assignment(answer.assignment),
                XAPIObject.course(answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, answer.assignment.course)
        return context


    @classmethod
    def comparison_question(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment + answer1 + answer2
            parent=ActivityList([
                XAPIObject.assignment(assignment)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context


    @classmethod
    def comparison(cls, comparison, current_comparison, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is comparison question + criterion
            parent=ActivityList([
                XAPIObject.comparison_question(comparison.assignment, current_comparison),
                XAPIObject.answer(comparison.answer1),
                XAPIObject.answer(comparison.answer2),
            ]),
            # grouping is course + assignment + answer1 + answer2
            grouping=ActivityList([
                XAPIObject.assignment(comparison.assignment),
                XAPIObject.course(comparison.assignment.course)
            ])
        )

        if comparison.attempt_uuid and current_comparison:
            context.context_activities.parent.append(XAPIObject.comparison_attempt(comparison, current_comparison))

        cls._add_sis_data(context, comparison.assignment.course)
        return context

    @classmethod
    def comparison_attempt(cls, comparison, current_comparison, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is comparison question + criterion
            parent=ActivityList([
                XAPIObject.comparison_question(comparison.assignment, current_comparison)
            ]),
            # grouping is course + assignment + answer1 + answer2
            grouping=ActivityList([
                XAPIObject.assignment(comparison.assignment),
                XAPIObject.course(comparison.assignment.course)
            ])
        )

        cls._add_sis_data(context, comparison.assignment.course)
        return context


    @classmethod
    def evaluation_question(cls, assignment):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.assignment(answer_comment.answer.assignment),
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context

    @classmethod
    def evaluation_response(cls, answer_comment, evaluation_number, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.evaluation_question(answer_comment.answer.assignment, evaluation_number),
                XAPIObject.answer(answer_comment.answer)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.assignment(answer_comment.answer.assignment),
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        if answer_comment.attempt_uuid and evaluation_number:
            context.context_activities.parent.append(XAPIObject.evaluation_attempt(answer_comment, evaluation_number))

        cls._add_sis_data(context, answer_comment.answer.assignment.course)
        return context

    @classmethod
    def evaluation_attempt(cls, answer_comment, evaluation_number, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.evaluation_question(answer_comment.answer.assignment, evaluation_number)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.assignment(answer_comment.answer.assignment),
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, answer_comment.answer.assignment.course)
        return context



    @classmethod
    def self_evaluation_question(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment + answer
            parent=ActivityList([
                XAPIObject.assignment(assignment),
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context


    @classmethod
    def self_evaluation_response(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is self-evaulation question
            parent=ActivityList([
                XAPIObject.self_evaluation_question(answer_comment.answer.assignment),
                XAPIObject.answer(answer_comment.answer)
            ]),
            # grouping is course + assignment + answer
            grouping=ActivityList([
                XAPIObject.assignment(answer_comment.answer.assignment),
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        if answer_comment.attempt_uuid:
            context.context_activities.parent.append(XAPIObject.self_evaluation_attempt(answer_comment))

        cls._add_sis_data(context, answer_comment.answer.assignment.course)
        return context


    @classmethod
    def self_evaluation_attempt(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.self_evaluation_question(answer_comment.answer.assignment)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.assignment(answer_comment.answer.assignment),
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, answer_comment.answer.assignment.course)
        return context



    @classmethod
    def answer_comment(cls, answer_comment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment question
            parent=ActivityList([
                XAPIObject.answer(answer_comment.answer)
            ]),
            # grouping is course + assignment + assignment question
            grouping=ActivityList([
                XAPIObject.assignment_question(answer_comment.answer.assignment),
                XAPIObject.assignment(answer_comment.answer.assignment),
                XAPIObject.course(answer_comment.answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, answer_comment.answer.assignment.course)
        return context


    @classmethod
    def answer_attachment(cls, answer, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment answer
            parent=ActivityList([
                XAPIObject.answer(answer)
            ]),
            # grouping is course + assignment + assignment question
            grouping=ActivityList([
                XAPIObject.assignment_question(answer.assignment),
                XAPIObject.assignment(answer.assignment),
                XAPIObject.course(answer.assignment.course)
            ])
        )

        cls._add_sis_data(context, answer.assignment.course)
        return context

    @classmethod
    def assignment_attachment(cls, assignment, **kwargs):
        context = cls.basic(**kwargs)

        context.context_activities = ContextActivities(
            # parent is assignment
            parent=ActivityList([
                XAPIObject.assignment(assignment)
            ]),
            # grouping is course
            grouping=ActivityList([
                XAPIObject.course(assignment.course)
            ])
        )

        cls._add_sis_data(context, assignment.course)
        return context