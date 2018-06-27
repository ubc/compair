# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)
from future.standard_library import install_aliases
install_aliases()

import datetime
import pytz

from flask import current_app, session as sess
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.caliper.actor import CaliperActor

from compair.models import WinningAnswer, ScoringAlgorithm, CourseRole, \
    SystemRole
from caliper.constants import ENTITY_TYPES as CALIPER_ENTITY_TYPES

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
        ret = {}

        if attempt_mixin_object.attempt_duration:
            ret["duration"] = attempt_mixin_object.attempt_duration

        if attempt_mixin_object.attempt_started:
            ret["startedAtTime"] = attempt_mixin_object.attempt_started.replace(tzinfo=pytz.utc).isoformat()

        if attempt_mixin_object.attempt_ended:
            ret["endedAtTime"] = attempt_mixin_object.attempt_ended.replace(tzinfo=pytz.utc).isoformat()

        return ret

    @classmethod
    def compair_app(cls):
        return {
            "id": ResourceIRI.compair(),
            "type": CALIPER_ENTITY_TYPES["SOFTWARE_APPLICATION"],
            "name": "ComPAIR",
            "description": "The ComPAIR learning application pairs student answers for deeper learning through comparison of peer work.",
            "version": current_app.config.get('COMPAIR_VERSION')
        }


    @classmethod
    def criterion(cls, criterion):
        return {
            "id": ResourceIRI.criterion(criterion.uuid),
            "type": CALIPER_ENTITY_TYPES["ENTITY"],
            "name": LearningRecord.trim_text_to_size_limit(criterion.name),
            "description": LearningRecord.trim_text_to_size_limit(criterion.description),
            "dateCreated": criterion.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": criterion.modified.replace(tzinfo=pytz.utc).isoformat(),
        }

    @classmethod
    def membership(cls, course, user):
        membership = {
            "id": ResourceIRI.user_membership(course.uuid, user.uuid),
            "type": CALIPER_ENTITY_TYPES["MEMBERSHIP"],
            "member": CaliperActor.generate_actor(user),
            "organization": ResourceIRI.course(course.uuid),
            "status": "Active",
            "extensions": {}
        }

        roles = []
        course_role = user.get_course_role(course.id)
        if course_role in [CourseRole.instructor, CourseRole.teaching_assistant]:
            roles.append("Instructor")
        if course_role == CourseRole.teaching_assistant:
            roles.append("Instructor#TeachingAssistant")
        if course_role == CourseRole.student:
            roles.append("Learner")
        if user.system_role == SystemRole.sys_admin:
            roles.append("Administrator")

        if len(roles) > 0:
            membership["roles"] = roles

        if course_role == CourseRole.dropped:
            membership['status'] = "Inactive"

        if course.lti_has_sis_data:
            sis_data = course.lti_sis_data
            membership['extensions']['sis_courses'] = []
            membership['extensions']['sis_sections'] = []
            for sis_course_id, sis_section_ids in sis_data.items():
                membership['extensions']['sis_courses'].append(ResourceIRI.sis_course(sis_course_id))

                for sis_section_id in sis_section_ids:
                    membership['extensions']['sis_sections'].append(ResourceIRI.sis_section(sis_course_id, sis_section_id))

            sis_course_id = list(sis_data.keys())[0]
            sis_section_id = sis_data[sis_course_id][0]
            membership['organization'] = cls.course_section(sis_course_id, sis_section_id)

        return membership

    @classmethod
    def course_section(cls, sis_course_id, sis_section_id):
        return {
            "id": ResourceIRI.sis_section(sis_course_id, sis_section_id),
            "type": CALIPER_ENTITY_TYPES["COURSE_SECTION"],
            "subOrganizationOf": cls.course_offerring(sis_course_id)
        }

    @classmethod
    def course_offerring(cls, sis_course_id):
        return {
            "id": ResourceIRI.sis_course(sis_course_id),
            "type": CALIPER_ENTITY_TYPES["COURSE_OFFERING"]
        }

    @classmethod
    def session(cls, caliper_actor):
        session = {
            "id": ResourceIRI.user_session(sess.get('session_id', '')),
            "type": CALIPER_ENTITY_TYPES["SESSION"],
            "user": caliper_actor,
            "dateCreated": sess.get('start_at'),
            "startedAtTime": sess.get('start_at')
        }

        if sess.get('login_method') != None:
            session["extensions"] = {
                "login_method": sess.get('login_method')
            }

        if sess.get('end_at'):
            session["endedAtTime"] = sess.get('end_at')

        return session

    @classmethod
    def course(cls, course):
        ret = {
            "id": ResourceIRI.course(course.uuid),
            "type": CALIPER_ENTITY_TYPES["COURSE_OFFERING"],
            "academicSession": course.term,
            "name": LearningRecord.trim_text_to_size_limit(course.name),
            "dateCreated": course.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": course.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {}
        }

        if course.lti_linked:
            ret["extensions"]["ltiContexts"] = []
            for lti_context in course.lti_contexts:
                lti_consumer = lti_context.lti_consumer

                ret["extensions"]["ltiContexts"].append({
                    "oauth_consumer_key": lti_consumer.oauth_consumer_key,
                    "tool_consumer_instance_guid": lti_consumer.tool_consumer_instance_guid,
                    "tool_consumer_instance_name": lti_consumer.tool_consumer_instance_name,
                    "tool_consumer_instance_url": lti_consumer.tool_consumer_instance_url,
                    "lis_course_offering_sourcedid": lti_context.lis_course_offering_sourcedid,
                    "lis_course_section_sourcedid": lti_context.lis_course_section_sourcedid,
                    "context_id": lti_context.context_id
                })

        return ret



    @classmethod
    def assignment(cls, assignment):
        ret = {
            "id": ResourceIRI.assignment(assignment.course_uuid, assignment.uuid),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT"],
            "name": LearningRecord.trim_text_to_size_limit(assignment.name),
            "dateToStartOn": assignment.answer_start.replace(tzinfo=pytz.utc).isoformat(),
            "isPartOf": CaliperEntities.course(assignment.course),
            "items": [],
            "dateCreated": assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": assignment.modified.replace(tzinfo=pytz.utc).isoformat()
        }

        ret["items"].append({
            "id": ResourceIRI.assignment_question(assignment.course_uuid, assignment.uuid),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"]
        })

        for index in range(assignment.number_of_comparisons):
            current = index + 1
            ret["items"].append({
                "id": ResourceIRI.comparison_question(assignment.course_uuid, assignment.uuid, current),
                "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"]
            })
            ret["items"].append({
                "id": ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, (current * 2) - 1),
                "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"]
            })
            ret["items"].append({
                "id": ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, (current * 2)),
                "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"]
            })

        if assignment.enable_self_evaluation:
            ret["items"].append({
                "id": ResourceIRI.self_evaluation_question(assignment.course_uuid, assignment.uuid),
                "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"]
            })

        if assignment.description:
            ret["description"] = LearningRecord.trim_text_to_size_limit(assignment.description)

        return ret


    @classmethod
    def assignment_attempt(cls, assignment, attempt_mixin_object, user):
        ret = {
            "id": ResourceIRI.assignment_attempt(assignment.course_uuid, assignment.uuid, attempt_mixin_object.attempt_uuid),
            "type": CALIPER_ENTITY_TYPES["ATTEMPT"],
            "assignee": CaliperActor.generate_actor(user),
            "assignable": CaliperEntities.assignment(assignment),
        }
        ret.update(cls._basic_attempt(attempt_mixin_object))

        return ret


    @classmethod
    def assignment_question(cls, assignment):
        ret = {
            "id": ResourceIRI.assignment_question(assignment.course_uuid, assignment.uuid),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"],
            "name": LearningRecord.trim_text_to_size_limit(assignment.name),
            "dateToStartOn": assignment.answer_start.replace(tzinfo=pytz.utc).isoformat(),
            "dateToSubmit": assignment.answer_end.replace(tzinfo=pytz.utc).isoformat(),
            "isPartOf": CaliperEntities.assignment(assignment),
            "dateCreated": assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": assignment.modified.replace(tzinfo=pytz.utc).isoformat()
        }

        if assignment.description:
            ret["description"] = LearningRecord.trim_text_to_size_limit(assignment.description)

        return ret

    @classmethod
    def answer(cls, answer):
        ret = {
            "id": ResourceIRI.answer(answer.course_uuid, answer.assignment_uuid, answer.uuid),
            "type": CALIPER_ENTITY_TYPES["RESPONSE"],
            "dateCreated": answer.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": answer.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "isDraft": answer.draft
            }
        }
        ret["extensions"].update(cls._basic_content_extension(answer.content))

        if answer.attempt_uuid:
            ret["attempt"] = CaliperEntities.answer_attempt(answer)

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

            ret["extensions"]["scoreDetails"] = score_details

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

                ret["extensions"]["scoreDetails"]["criteria"][ResourceIRI.criterion(criterion_score.criterion_uuid)] = score_details


        return ret

    @classmethod
    def answer_attempt(cls, answer):
        ret = {
            "id": ResourceIRI.answer_attempt(answer.course_uuid, answer.assignment_uuid, answer.attempt_uuid),
            "type": CALIPER_ENTITY_TYPES["ATTEMPT"],
            "assignee": CaliperActor.generate_actor(answer.user),
            "assignable": CaliperEntities.assignment_question(answer.assignment),
        }
        ret.update(cls._basic_attempt(answer))

        return ret




    @classmethod
    def comparison_question(cls, assignment, comparison_number):
        ret = {
            "id": ResourceIRI.comparison_question(assignment.course_uuid, assignment.uuid, comparison_number),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"],
            "name": "Assignment comparison #"+str(int(comparison_number)),
            "isPartOf": CaliperEntities.assignment(assignment),
            "dateCreated": assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": assignment.modified.replace(tzinfo=pytz.utc).isoformat()
        }

        if assignment.compare_start and assignment.compare_end:
            ret["dateToStartOn"] = assignment.compare_start.replace(tzinfo=pytz.utc).isoformat()
            ret["dateToSubmit"] = assignment.compare_end.replace(tzinfo=pytz.utc).isoformat()
        else:
            ret["dateToStartOn"] = assignment.answer_end.replace(tzinfo=pytz.utc).isoformat()

        return ret

    @classmethod
    def comparison(cls, comparison, current_comparison=None):

        winner = "Undecided"
        if comparison.winner == WinningAnswer.draw:
            winner = "Draw"
        elif comparison.winner == WinningAnswer.answer1:
            winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
        elif comparison.winner == WinningAnswer.answer2:
            winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)

        ret = {
            "id": ResourceIRI.comparison(comparison.course_uuid, comparison.assignment_uuid, comparison.uuid),
            "type": CALIPER_ENTITY_TYPES["RESPONSE"],
            "dateCreated": comparison.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": comparison.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "pairingAlgorithm": comparison.pairing_algorithm.value,
                "winner": winner,
                "criteria": {},
                "answers": [
                    ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid),
                    ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)
                ],
                "completed": comparison.completed
            }
        }

        for comparison_criterion in comparison.comparison_criteria:
            winner = "Undecided"
            if comparison_criterion.winner == WinningAnswer.answer1:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
            elif comparison_criterion.winner == WinningAnswer.answer2:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)

            ret["extensions"]["criteria"][ResourceIRI.criterion(comparison_criterion.criterion_uuid)] = winner

        if comparison.attempt_uuid and current_comparison:
            ret["attempt"] = CaliperEntities.comparison_attempt(comparison, current_comparison)

        return ret

    @classmethod
    def comparison_attempt(cls, comparison, current_comparison):
        ret = {
            "id": ResourceIRI.comparison_attempt(comparison.course_uuid, comparison.assignment_uuid, current_comparison, comparison.attempt_uuid),
            "type": CALIPER_ENTITY_TYPES["ATTEMPT"],
            "assignee": CaliperActor.generate_actor(comparison.user),
            "assignable": CaliperEntities.comparison_question(comparison.assignment, current_comparison),
        }
        ret.update(cls._basic_attempt(comparison))

        return ret





    @classmethod
    def evaluation_question(cls, assignment, evaluation_number):
        ret = {
            "id": ResourceIRI.evaluation_question(assignment.course_uuid, assignment.uuid, evaluation_number),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"],
            "name": "Assignment Answer Evaluation #"+str(evaluation_number),
            "isPartOf": CaliperEntities.assignment(assignment),
            "dateCreated": assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": assignment.modified.replace(tzinfo=pytz.utc).isoformat()
        }

        if assignment.compare_start and assignment.compare_end:
            ret["dateToStartOn"] = assignment.compare_start.replace(tzinfo=pytz.utc).isoformat()
            ret["dateToSubmit"] = assignment.compare_end.replace(tzinfo=pytz.utc).isoformat()
        else:
            ret["dateToStartOn"] = assignment.answer_end.replace(tzinfo=pytz.utc).isoformat()

        if assignment.peer_feedback_prompt:
            ret["description"] = LearningRecord.trim_text_to_size_limit(assignment.peer_feedback_prompt)

        return ret

    @classmethod
    def evaluation_response(cls, answer_comment, evaluation_number):
        ret = {
            "id": ResourceIRI.evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            "type": CALIPER_ENTITY_TYPES["RESPONSE"],
            "dateCreated": answer_comment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": answer_comment.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "isDraft": answer_comment.draft
            }
        }
        ret["extensions"].update(cls._basic_content_extension(answer_comment.content))

        if answer_comment.attempt_uuid:
            ret["attempt"] = CaliperEntities.evaluation_attempt(answer_comment, evaluation_number)

        return ret

    @classmethod
    def evaluation_attempt(cls, answer_comment, evaluation_number):
        ret = {
            "id": ResourceIRI.evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                evaluation_number, answer_comment.attempt_uuid),
            "type": CALIPER_ENTITY_TYPES["ATTEMPT"],
            "assignee": CaliperActor.generate_actor(answer_comment.user),
            "assignable": CaliperEntities.evaluation_question(answer_comment.answer.assignment, evaluation_number),
        }
        ret.update(cls._basic_attempt(answer_comment))

        return ret




    @classmethod
    def self_evaluation_question(cls, assignment):
        ret = {
            "id": ResourceIRI.self_evaluation_question(assignment.course_uuid, assignment.uuid),
            "type": CALIPER_ENTITY_TYPES["ASSESSMENT_ITEM"],
            "name": "Assignment self-evaluation",
            "isPartOf": CaliperEntities.assignment(assignment),
            "dateCreated": assignment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": assignment.modified.replace(tzinfo=pytz.utc).isoformat(),
        }

        if assignment.self_eval_instructions:
            ret["description"] = LearningRecord.trim_text_to_size_limit(assignment.self_eval_instructions)

        if assignment.self_eval_start and assignment.self_eval_end:
            ret["dateToStartOn"] = assignment.self_eval_start.replace(tzinfo=pytz.utc).isoformat()
            ret["dateToSubmit"] = assignment.self_eval_end.replace(tzinfo=pytz.utc).isoformat()
        elif assignment.compare_start and assignment.compare_end:
            ret["dateToStartOn"] = assignment.answer_end.replace(tzinfo=pytz.utc).isoformat()
        else:
            ret["dateToStartOn"] = assignment.answer_end.replace(tzinfo=pytz.utc).isoformat()

        return ret

    @classmethod
    def self_evaluation_response(cls, answer_comment):
        ret = {
            "id": ResourceIRI.self_evaluation_response(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            "type": CALIPER_ENTITY_TYPES["RESPONSE"],
            "dateCreated": answer_comment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": answer_comment.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "isDraft": answer_comment.draft
            }
        }
        ret["extensions"].update(cls._basic_content_extension(answer_comment.content))

        if answer_comment.attempt_uuid:
            ret["attempt"] = CaliperEntities.self_evaluation_attempt(answer_comment)

        return ret

    @classmethod
    def self_evaluation_attempt(cls, answer_comment):
        ret = {
            "id": ResourceIRI.self_evaluation_attempt(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.attempt_uuid),
            "type": CALIPER_ENTITY_TYPES["ATTEMPT"],
            "assignee": CaliperActor.generate_actor(answer_comment.user),
            "assignable": CaliperEntities.self_evaluation_question(answer_comment.answer.assignment),
        }
        ret.update(cls._basic_attempt(answer_comment))

        return ret



    @classmethod
    def answer_comment(cls, answer_comment):
        #TODO: this isn't in the Caliper spec yet
        return {
            "id": ResourceIRI.answer_comment(answer_comment.course_uuid, answer_comment.assignment_uuid,
                answer_comment.answer_uuid, answer_comment.uuid),
            "type": "Comment",
            "commenter": CaliperActor.generate_actor(answer_comment.user),
            "commented": CaliperEntities.answer(answer_comment.answer),
            "value": LearningRecord.trim_text_to_size_limit(answer_comment.content),
            "dateCreated": answer_comment.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": answer_comment.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "type": answer_comment.comment_type.value,
                "isDraft": answer_comment.draft,
                "characterCount": LearningRecord.character_count(answer_comment.content) if answer_comment.content else 0,
                "wordCount": LearningRecord.word_count(answer_comment.content) if answer_comment.content else 0
            }
        }


    @classmethod
    def report(cls, file_name, mimetype):
        return  {
            "id": ResourceIRI.report(file_name),
            "type": CALIPER_ENTITY_TYPES["DOCUMENT"],
            "name": file_name,
            "mediaType": mimetype,
        }

    @classmethod
    def assignment_attachment(cls, assignment, file, mimetype):
        return  {
            "id": ResourceIRI.attachment(file.name),
            "type": CALIPER_ENTITY_TYPES["DOCUMENT"],
            "name": file.alias,
            "mediaType": mimetype,
            "isPartOf": CaliperEntities.assignment(assignment),
            "dateCreated": file.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": file.modified.replace(tzinfo=pytz.utc).isoformat()
        }

    @classmethod
    def answer_attachment(cls, answer, file, mimetype):
        return  {
            "id": ResourceIRI.attachment(file.name),
            "type": CALIPER_ENTITY_TYPES["DOCUMENT"],
            "name": file.alias,
            "mediaType": mimetype,
            "isPartOf": CaliperEntities.answer(answer),
            "dateCreated": file.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": file.modified.replace(tzinfo=pytz.utc).isoformat()
        }