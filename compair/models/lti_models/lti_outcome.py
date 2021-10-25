# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app
from lti.outcome_request import OutcomeRequest, REPLACE_REQUEST

from . import *

from compair.core import db

class LTIOutcome(object):
    @classmethod
    def update_assignment_grades(cls, compair_assignment):
        from compair.models import CourseRole, AssignmentGrade
        from compair.tasks import update_lti_assignment_grades

        # don't update until passed the answer start date
        if not compair_assignment.available:
            return

        lti_resource_links = compair_assignment.lti_resource_links.all()

        # nothing to update if assignment not linked to any lti resources
        if len(lti_resource_links) == 0:
            return

        assignment_grades = AssignmentGrade.query \
            .filter_by(assignment_id=compair_assignment.id) \
            .all()

        # nothing to update if assignment doesn't have any grades
        if len(assignment_grades) == 0:
            return

        user_grades = {
            assignment_grade.user_id: assignment_grade.id \
                for assignment_grade in assignment_grades
        }

        # generate requests
        for lti_resource_link in lti_resource_links:
            lti_consumer = lti_resource_link.lti_consumer
            resource_link_grades = []
            if not lti_consumer.lis_outcome_service_url:
                continue

            lti_user_resource_links = lti_resource_link.lti_user_resource_links.all()
            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                assignment_grade_id = user_grades.get(lti_user_resource_link.compair_user_id)

                resource_link_grades.append((lis_result_sourcedid, assignment_grade_id))

            if len(resource_link_grades) == 0:
                continue

            update_lti_assignment_grades.delay(lti_consumer.id, resource_link_grades)

    @classmethod
    def update_assignment_user_grade(cls, compair_assignment, compair_user_id):
        cls.update_assignment_users_grades(compair_assignment, [compair_user_id])

    @classmethod
    def update_assignment_users_grades(cls, compair_assignment, compair_user_ids):
        from compair.models import CourseRole, AssignmentGrade, LTIUser
        from compair.tasks import update_lti_assignment_grades

        lti_resource_links = compair_assignment.lti_resource_links.all()

        # nothing to update if assignment not linked to any lti resources
        if len(lti_resource_links) == 0:
            return

        if len(compair_user_ids) == 0:
            return

        assignment_grades = AssignmentGrade.query \
            .filter_by(assignment_id=compair_assignment.id) \
            .filter(AssignmentGrade.user_id.in_(compair_user_ids)) \
            .all()

        # nothing to update if assignment doesn't have any grades
        if len(assignment_grades) == 0:
            return

        user_grades = {
            assignment_grade.user_id: assignment_grade.id \
                for assignment_grade in assignment_grades
        }

        # generate requests
        for lti_resource_link in lti_resource_links:
            lti_consumer = lti_resource_link.lti_consumer
            resource_link_grades = []
            if not lti_consumer.lis_outcome_service_url:
                continue

            lti_user_resource_links = lti_resource_link.lti_user_resource_links \
                .join("lti_user") \
                .filter(LTIUser.compair_user_id.in_(compair_user_ids)) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                assignment_grade_id = user_grades.get(lti_user_resource_link.compair_user_id)

                resource_link_grades.append((lis_result_sourcedid, assignment_grade_id))

            if len(resource_link_grades) == 0:
                continue

            update_lti_assignment_grades.delay(lti_consumer.id, resource_link_grades)

    @classmethod
    def update_course_grades(cls, compair_course):
        from compair.models import CourseRole, CourseGrade, \
            LTIResourceLink, LTIUserResourceLink
        from compair.tasks import update_lti_course_grades

        lti_contexts = compair_course.lti_contexts.all()

        # nothing to update if course not linked to any lti contexts
        if len(lti_contexts) == 0:
            return

        course_grades = CourseGrade.query \
            .filter_by(course_id=compair_course.id) \
            .all()

        # nothing to update if course doesn't have any grades
        if len(course_grades) == 0:
            return

        user_grades = {
            course_grade.user_id: course_grade.id \
                for course_grade in course_grades
        }

        # generate requests
        for lti_context in lti_contexts:
            lti_consumer = lti_context.lti_consumer
            lti_context_grades = []
            if not lti_consumer.lis_outcome_service_url:
                continue

            lti_user_resource_links = LTIUserResourceLink.query \
                .join("lti_resource_link") \
                .filter(
                    LTIResourceLink.lti_context_id == lti_context.id,
                    LTIResourceLink.compair_assignment_id == None
                ) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                course_grade_id = user_grades.get(lti_user_resource_link.compair_user_id)

                lti_context_grades.append((lis_result_sourcedid, course_grade_id))

            if len(lti_context_grades) == 0:
                continue

            update_lti_course_grades.delay(lti_consumer.id, lti_context_grades)

    @classmethod
    def update_course_user_grade(cls, compair_course, compair_user_id):
        cls.update_course_users_grade(compair_course, [compair_user_id])

    @classmethod
    def update_course_users_grade(cls, compair_course, compair_user_ids):
        from compair.models import CourseRole, CourseGrade, \
            LTIResourceLink, LTIUserResourceLink
        from compair.tasks import update_lti_course_grades

        lti_contexts = compair_course.lti_contexts.all()

        # nothing to update if course not linked to any lti contexts
        if len(lti_contexts) == 0:
            return

        if len(compair_user_ids) == 0:
            return

        course_grades = CourseGrade.query \
            .filter_by(course_id=compair_course.id) \
            .filter(CourseGrade.user_id.in_(compair_user_ids)) \
            .all()

        # nothing to update if course doesn't have any grades
        if len(course_grades) == 0:
            return

        user_grades = {
            course_grade.user_id: course_grade.id for course_grade in course_grades
        }

        # generate requests
        for lti_context in lti_contexts:
            lti_consumer = lti_context.lti_consumer
            lti_context_grades = []
            if not lti_consumer.lis_outcome_service_url:
                continue

            lti_user_resource_links = LTIUserResourceLink.query \
                .join("lti_resource_link") \
                .join("lti_user") \
                .filter(
                    LTIUser.compair_user_id.in_(compair_user_ids),
                    LTIResourceLink.lti_context_id == lti_context.id,
                    LTIResourceLink.compair_assignment_id == None
                ) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                course_grade_id = user_grades.get(lti_user_resource_link.compair_user_id)

                lti_context_grades.append((lis_result_sourcedid, course_grade_id))

            if len(lti_context_grades) == 0:
                continue

            update_lti_course_grades.delay(lti_consumer.id, lti_context_grades)

    @classmethod
    def post_replace_result(cls, lti_consumer, lis_result_sourcedid, grade, submittedAt=None):
        """
        grade must be in range: [0.0, 1.0]
        """

        if not lti_consumer.lis_outcome_service_url:
            current_app.logger.error("Failed grade update for lis_result_sourcedid: {} ... no lis_outcome_service_url".format(lis_result_sourcedid))
            return False
        elif not lis_result_sourcedid:
            current_app.logger.error("Failed grade update ... no lis_result_sourcedid")
            return False
        elif grade < 0.0 or grade > 1.0:
            current_app.logger.error("Failed grade update for lis_result_sourcedid: {} grade not in [0.0, 1.0]: {}".format(lis_result_sourcedid, grade))
            return False

        # build outcome request
        request = OutcomeRequest({
            "consumer_key": lti_consumer.oauth_consumer_key,
            "consumer_secret": lti_consumer.oauth_consumer_secret,
            "lis_outcome_service_url": lti_consumer.lis_outcome_service_url,
            "lis_result_sourcedid": lis_result_sourcedid,
            "submittedAt": submittedAt,
        })
        request.post_replace_result(grade)

        if request.was_outcome_post_successful():
            current_app.logger.debug("Successfully grade update for lis_result_sourcedid: {} with grade: {}".format(lis_result_sourcedid, grade))
        else:
            current_app.logger.error("Failed grade update for lis_result_sourcedid: {} with grade: {}".format(lis_result_sourcedid, grade))

        return request.was_outcome_post_successful()
