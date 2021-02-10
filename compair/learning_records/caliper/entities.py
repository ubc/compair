# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime
import pytz
import caliper
from six import text_type

from flask import current_app, session as sess
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.caliper.actor import CaliperActor

from compair.models import WinningAnswer, ScoringAlgorithm, CourseRole, \
    SystemRole
from caliper.constants import CALIPER_SYSIDTYPES as CALIPER_SYSTEM_TYPES

class CaliperEntities(object):
    @classmethod
    def _basic_content_extension(cls, content):
        return {
            "content": LearningRecord.trim_text_to_size_limit(content),
            "characterCount": LearningRecord.character_count(content) if content else 0,
            "wordCount": LearningRecord.word_count(content) if content else 0
        }

    @classmethod
    def _basic_attempt(cls, attempt_mixin_object):
        duration = None
        if attempt_mixin_object.attempt_duration:
            duration = attempt_mixin_object.attempt_duration

        startedAtTime = None
        if attempt_mixin_object.attempt_started:
            startedAtTime = attempt_mixin_object.attempt_started.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        endedAtTime = None
        if attempt_mixin_object.attempt_ended:
            endedAtTime = attempt_mixin_object.attempt_ended.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        return (duration, startedAtTime, endedAtTime)

    @classmethod
    def compair_app(cls):
        return caliper.entities.SoftwareApplication(
            id=ResourceIRI.compair(),
            name="ComPAIR",
            description="The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.",
            version=text_type(current_app.config.get('COMPAIR_VERSION', ''))
        )


    @classmethod
    def criterion(cls, criterion):
        return caliper.entities.DigitalResource(
            id=ResourceIRI.criterion(criterion.uuid),
            name=LearningRecord.trim_text_to_size_limit(criterion.name),
            description=LearningRecord.trim_text_to_size_limit(criterion.description),
            dateCreated=criterion.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=criterion.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def membership(cls, course, user):
        roles = []
        extensions = {}

        course_role = user.get_course_role(course.id)
        if course_role in [CourseRole.instructor, CourseRole.teaching_assistant]:
            roles.append("Instructor")
        if course_role == CourseRole.teaching_assistant:
            roles.append("Instructor#TeachingAssistant")
        if course_role == CourseRole.student:
            roles.append("Learner")
        if user.system_role == SystemRole.sys_admin:
            roles.append("Administrator")

        if course.lti_has_sis_data:
            sis_data = course.lti_sis_data
            extensions['sis_courses'] = []
            for sis_course_id, sis_section_ids in sis_data.items():
                extensions['sis_courses'].append({
                    'id': sis_course_id,
                    'section_ids': sis_section_ids
                })

        return caliper.entities.Membership(
            id=ResourceIRI.user_membership(course.uuid, user.uuid),
            member=CaliperActor.generate_actor(user),
            organization=ResourceIRI.course(course.uuid),
            roles=roles if len(roles) > 0 else None,
            status="Active" if course_role != CourseRole.dropped else "Inactive",
            extensions=extensions
        )

    @classmethod
    def group(cls, group):
        members = [
            CaliperActor.generate_actor(uc.user) for uc in group.user_courses.all()
        ]

        return caliper.entities.Group(
            id=ResourceIRI.group(group.course_uuid, group.uuid),
            name=group.name,
            subOrganizationOf=ResourceIRI.course(group.course_uuid),
            members=members,
            dateCreated=group.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=group.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        )

    @classmethod
    def session(cls, caliper_actor, request=None, extensions={}):
        if sess.get('login_method') != None:
            extensions["login_method"] = sess.get('login_method')
        if request.environ.get('HTTP_REFERER'):
            extensions["referer"] = request.environ.get('HTTP_REFERER')

        return caliper.entities.Session(
            id=ResourceIRI.user_session(sess.get('session_id', '')),
            user=caliper_actor,
            client=CaliperEntities.client(request),
            dateCreated=sess.get('start_at'),
            startedAtTime=sess.get('start_at'),
            endedAtTime=sess.get('end_at') if sess.get('end_at') else None,
            extensions=extensions
        )

    @classmethod
    def client(cls, request):
        if not request:
            return None

        return caliper.entities.SoftwareApplication(
            id=ResourceIRI.user_client(sess.get('session_id', '')),
            userAgent=text_type(request.environ.get('HTTP_USER_AGENT', '')),
            ipAddress=text_type(request.environ.get('REMOTE_ADDR', '')),
            host=text_type(request.environ.get('HTTP_HOST', '')),
        )


    @classmethod
    def course(cls, course):
        otherIdentifiers = []
        if course.lti_linked:
            for lti_context in course.lti_contexts:
                lti_consumer = lti_context.lti_consumer

                otherIdentifiers.append(caliper.entities.SystemIdentifier(
                    identifier=lti_context.context_id,
                    identifierType=CALIPER_SYSTEM_TYPES['LTI_CONTEXT_ID'],
                    source=lti_consumer.tool_consumer_instance_url,
                    extensions={
                        "oauth_consumer_key": lti_consumer.oauth_consumer_key,
                        "tool_consumer_instance_guid": lti_consumer.tool_consumer_instance_guid,
                        "tool_consumer_instance_name": lti_consumer.tool_consumer_instance_name,
                        "lis_course_offering_sourcedid": lti_context.lis_course_offering_sourcedid,
                        "lis_course_section_sourcedid": lti_context.lis_course_section_sourcedid,
                    }
                ))

        return caliper.entities.CourseOffering(
            id=ResourceIRI.course(course.uuid),
            academicSession=course.term,
            name=LearningRecord.trim_text_to_size_limit(course.name),
            dateCreated=course.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=course.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            otherIdentifiers=otherIdentifiers
        )



    @classmethod
    def assignment(cls, assignment):
        items = []
        description = None

        if assignment.description:
            description = LearningRecord.trim_text_to_size_limit(assignment.description)

        items.append(caliper.entities.AssessmentItem(
            id=ResourceIRI.assignment_question(assignment.course_uuid, assignment.uuid)
        ))
        for index in range(assignment.number_of_comparisons):
            current = index + 1
            items.append(caliper.entities.AssessmentItem(
                id=ResourceIRI.comparison_question(assignment.course_uuid, assignment.uuid, current)
            ))
            items.append(caliper.entities.AssessmentItem(
                id=ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, (current * 2) - 1)
            ))
            items.append(caliper.entities.AssessmentItem(
                id=ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, (current * 2))
            ))
        if assignment.enable_self_evaluation:
            items.append(caliper.entities.AssessmentItem(
                id=ResourceIRI.self_evaluation_question(assignment.course_uuid, assignment.uuid)
            ))

        return caliper.entities.Assessment(
            id=ResourceIRI.assignment(assignment.course_uuid, assignment.uuid),
            name=LearningRecord.trim_text_to_size_limit(assignment.name),
            description=description,
            dateToStartOn=assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            isPartOf=CaliperEntities.course(assignment.course),
            items=items,
            dateCreated=assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )


    @classmethod
    def assignment_attempt(cls, assignment, attempt_mixin_object, user):
        (duration, startedAtTime, endedAtTime) = cls._basic_attempt(attempt_mixin_object)

        return caliper.entities.Attempt(
            id=ResourceIRI.assignment_attempt(assignment.course_uuid, assignment.uuid, attempt_mixin_object.attempt_uuid),
            assignee=CaliperActor.generate_actor(user),
            assignable=CaliperEntities.assignment(assignment),
            duration=duration,
            startedAtTime=startedAtTime,
            endedAtTime=endedAtTime
        )


    @classmethod
    def assignment_question(cls, assignment):
        description = None
        if assignment.description:
            description = LearningRecord.trim_text_to_size_limit(assignment.description)

        return caliper.entities.AssessmentItem(
            id=ResourceIRI.assignment_question(assignment.course_uuid, assignment.uuid),
            name=LearningRecord.trim_text_to_size_limit(assignment.name),
            description=description,
            dateToStartOn=assignment.answer_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateToSubmit=assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            isPartOf=CaliperEntities.assignment(assignment),
            dateCreated=assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def answer(cls, answer):
        attempt = None
        extensions = {
            "isDraft": answer.draft,
        }

        if answer.attempt_uuid:
            attempt = CaliperEntities.answer_attempt(answer)

        extensions.update(cls._basic_content_extension(answer.content))

        if answer.score:
            score = answer.score
            score_details = {
                "algorithm": score.scoring_algorithm.value,
                "score": score.score,
                "wins": score.wins,
                "loses": score.loses,
                "rounds": score.rounds,
                "opponents": score.opponents,
                "criteria": {}
            }

            if score.scoring_algorithm == ScoringAlgorithm.true_skill:
                score_details['mu'] = score.variable1
                score_details['sigma'] = score.variable2

            extensions["scoreDetails"] = score_details

            for criterion_score in answer.criteria_scores:
                score_details = {
                    "score": criterion_score.score,
                    "wins": criterion_score.wins,
                    "loses": criterion_score.loses,
                    "rounds": criterion_score.rounds,
                    "opponents": criterion_score.opponents,
                }

                if criterion_score.scoring_algorithm == ScoringAlgorithm.true_skill:
                    score_details["mu"] = criterion_score.variable1
                    score_details["sigma"] = criterion_score.variable2

                extensions["scoreDetails"]["criteria"][ResourceIRI.criterion(criterion_score.criterion_uuid)] = score_details

        return caliper.entities.Response(
            id=ResourceIRI.answer(answer.course_uuid, answer.assignment_uuid, answer.uuid),
            attempt=attempt,
            dateCreated=answer.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=answer.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            extensions=extensions
        )

    @classmethod
    def answer_attempt(cls, answer):
        (duration, startedAtTime, endedAtTime) = cls._basic_attempt(answer)

        assignee = None
        extensions = {}

        # Caliper v1.1, v1.2 doesn't easily support tracking group submissions
        # might be able to use assignee in v1.3 https://github.com/IMSGlobal/caliper-spec/issues/535
        if answer.group_id != None:
            extensions['group'] = CaliperEntities.group(answer.group).as_dict()
        else:
            assignee = CaliperActor.generate_actor(answer.user)

        return caliper.entities.Attempt(
            id=ResourceIRI.answer_attempt(answer.course_uuid, answer.assignment_uuid, answer.attempt_uuid),
            assignee=assignee,
            assignable=CaliperEntities.assignment_question(answer.assignment),
            duration=duration,
            startedAtTime=startedAtTime,
            endedAtTime=endedAtTime,
            extensions=extensions
        )




    @classmethod
    def comparison_question(cls, assignment, comparison_number):
        dateToStartOn = assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        dateToSubmit = None
        if assignment.compare_start and assignment.compare_end:
            dateToStartOn = assignment.compare_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            dateToSubmit = assignment.compare_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        return caliper.entities.AssessmentItem(
            id=ResourceIRI.comparison_question(assignment.course_uuid, assignment.uuid, comparison_number),
            name="Assignment comparison #"+str(int(comparison_number)),
            dateToStartOn=dateToStartOn,
            dateToSubmit=dateToSubmit,
            isPartOf=CaliperEntities.assignment(assignment),
            dateCreated=assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def comparison(cls, comparison, current_comparison=None):
        attempt = None
        extensions = {
            "pairingAlgorithm": comparison.pairing_algorithm.value,
            "winner": "Undecided",
            "criteria": {},
            "answers": [
                ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid),
                ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)
            ],
            "completed": comparison.completed
        }

        if comparison.winner == WinningAnswer.draw:
            extensions["winner"] = "Draw"
        elif comparison.winner == WinningAnswer.answer1:
            extensions["winner"] = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
        elif comparison.winner == WinningAnswer.answer2:
            extensions["winner"] = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)

        if comparison.attempt_uuid and current_comparison:
            attempt = CaliperEntities.comparison_attempt(comparison, current_comparison)

        for comparison_criterion in comparison.comparison_criteria:
            winner = "Undecided"
            if comparison_criterion.winner == WinningAnswer.answer1:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
            elif comparison_criterion.winner == WinningAnswer.answer2:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)

            extensions["criteria"][ResourceIRI.criterion(comparison_criterion.criterion_uuid)] = winner

        return caliper.entities.Response(
            id=ResourceIRI.comparison(comparison.course_uuid, comparison.assignment_uuid, comparison.uuid),
            attempt=attempt,
            dateCreated=comparison.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=comparison.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            extensions=extensions
        )

    @classmethod
    def comparison_attempt(cls, comparison, current_comparison):
        (duration, startedAtTime, endedAtTime) = cls._basic_attempt(comparison)

        return caliper.entities.Attempt(
            id=ResourceIRI.comparison_attempt(comparison.course_uuid, comparison.assignment_uuid, current_comparison, comparison.attempt_uuid),
            assignee=CaliperActor.generate_actor(comparison.user),
            assignable=CaliperEntities.comparison_question(comparison.assignment, current_comparison),
            duration=duration,
            startedAtTime=startedAtTime,
            endedAtTime=endedAtTime
        )





    @classmethod
    def evaluation_question(cls, assignment, evaluation_number):
        dateToStartOn = assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        dateToSubmit = None
        description = None
        if assignment.compare_start and assignment.compare_end:
            dateToStartOn = assignment.compare_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            dateToSubmit = assignment.compare_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        if assignment.peer_feedback_prompt:
            description = LearningRecord.trim_text_to_size_limit(assignment.peer_feedback_prompt)

        return caliper.entities.AssessmentItem(
            id=ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, evaluation_number),
            name="Assignment Answer Evaluation #"+str(evaluation_number),
            description=description,
            dateToStartOn=dateToStartOn,
            dateToSubmit=dateToSubmit,
            isPartOf=CaliperEntities.assignment(assignment),
            dateCreated=assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def evaluation_response(cls, answer_comment, evaluation_number):
        attempt = None
        extensions = {
            "isDraft": answer_comment.draft
        }

        if answer_comment.attempt_uuid:
            attempt = CaliperEntities.evaluation_attempt(answer_comment, evaluation_number)

        extensions.update(cls._basic_content_extension(answer_comment.content))

        return caliper.entities.Response(
            id=ResourceIRI.evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            attempt=attempt,
            dateCreated=answer_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=answer_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            extensions=extensions
        )

    @classmethod
    def evaluation_attempt(cls, answer_comment, evaluation_number):
        (duration, startedAtTime, endedAtTime) = cls._basic_attempt(answer_comment)

        return caliper.entities.Attempt(
            id=ResourceIRI.evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                evaluation_number, answer_comment.attempt_uuid),
            assignee=CaliperActor.generate_actor(answer_comment.user),
            assignable=CaliperEntities.evaluation_question(answer_comment.answer.assignment, evaluation_number),
            duration=duration,
            startedAtTime=startedAtTime,
            endedAtTime=endedAtTime
        )




    @classmethod
    def self_evaluation_question(cls, assignment):
        dateToStartOn = assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        dateToSubmit = None
        description = None
        if assignment.self_eval_start and assignment.self_eval_end:
            dateToStartOn = assignment.self_eval_start.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            dateToSubmit = assignment.self_eval_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        elif assignment.compare_start and assignment.compare_end:
            dateToStartOn = assignment.answer_end.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        if assignment.self_eval_instructions:
            description = LearningRecord.trim_text_to_size_limit(assignment.self_eval_instructions)

        return caliper.entities.AssessmentItem(
            id=ResourceIRI.self_evaluation_question(assignment.course_uuid, assignment.uuid),
            name="Assignment self-evaluation",
            description=description,
            dateToStartOn=dateToStartOn,
            dateToSubmit=dateToSubmit,
            isPartOf=CaliperEntities.assignment(assignment),
            dateCreated=assignment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=assignment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def self_evaluation_response(cls, answer_comment):
        attempt = None
        extensions = {
            "isDraft": answer_comment.draft
        }

        if answer_comment.attempt_uuid:
            attempt = CaliperEntities.self_evaluation_attempt(answer_comment)

        extensions.update(cls._basic_content_extension(answer_comment.content))

        return caliper.entities.Response(
            id=ResourceIRI.self_evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            attempt=attempt,
            dateCreated=answer_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=answer_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            extensions=extensions
        )

    @classmethod
    def self_evaluation_attempt(cls, answer_comment):
        (duration, startedAtTime, endedAtTime) = cls._basic_attempt(answer_comment)

        return caliper.entities.Attempt(
            id=ResourceIRI.self_evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.attempt_uuid),
            assignee=CaliperActor.generate_actor(answer_comment.user),
            assignable=CaliperEntities.self_evaluation_question(answer_comment.answer.assignment),
            duration=duration,
            startedAtTime=startedAtTime,
            endedAtTime=endedAtTime
        )



    @classmethod
    def answer_comment(cls, answer_comment):
        return caliper.entities.Comment(
            id=ResourceIRI.answer_comment(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            commenter=CaliperActor.generate_actor(answer_comment.user),
            commentedOn=CaliperEntities.answer(answer_comment.answer),
            value=LearningRecord.trim_text_to_size_limit(answer_comment.content),
            dateCreated=answer_comment.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=answer_comment.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            extensions={
                "type": answer_comment.comment_type.value,
                "isDraft": answer_comment.draft,
                "characterCount": LearningRecord.character_count(answer_comment.content) if answer_comment.content else 0,
                "wordCount": LearningRecord.word_count(answer_comment.content) if answer_comment.content else 0
            }
        )


    @classmethod
    def report(cls, file_name, mimetype):
        return caliper.entities.Document(
            id=ResourceIRI.report(file_name),
            name=file_name,
            mediaType=mimetype
        )

    @classmethod
    def assignment_attachment(cls, assignment, file, mimetype):
        return caliper.entities.Document(
            id=ResourceIRI.attachment(file.name),
            name=file.alias,
            mediaType=mimetype,
            isPartOf=CaliperEntities.assignment(assignment),
            dateCreated=file.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=file.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    @classmethod
    def answer_attachment(cls, answer, file, mimetype):
        return caliper.entities.Document(
            id=ResourceIRI.attachment(file.name),
            name=file.alias,
            mediaType=mimetype,
            isPartOf=CaliperEntities.answer(answer),
            dateCreated=file.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=file.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )