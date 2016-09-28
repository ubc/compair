# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app
from lti.outcome_request import OutcomeRequest, REPLACE_REQUEST

from . import *

from acj.core import db

class LTIOutcome(object):
    @classmethod
    def update_assignment_grades(cls, acj_assignment):
        from acj.models import CourseRole, AssignmentGrade
        from acj.tasks.lti_outcomes import update_lti_assignment_grades

        lti_resource_links = acj_assignment.lti_resource_links.all()

        # nothing to update if assignment not linked to any lti resources
        if len(lti_resource_links) == 0:
            return

        assignment_grades = AssignmentGrade.query \
            .filter_by(assignment_id=acj_assignment.id) \
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
                assignment_grade_id = user_grades.get(lti_user_resource_link.acj_user_id)

                resource_link_grades.append((lis_result_sourcedid, assignment_grade_id))

            if len(resource_link_grades) == 0:
                continue

            update_lti_assignment_grades.delay(lti_consumer.id, resource_link_grades)

    @classmethod
    def update_user_assignment_grade(cls, acj_assignment, acj_user):
        from acj.models import CourseRole, AssignmentGrade, LTIUser
        from acj.tasks.lti_outcomes import update_lti_assignment_grades

        lti_resource_links = acj_assignment.lti_resource_links.all()

        # nothing to update if assignment not linked to any lti resources
        if len(lti_resource_links) == 0:
            return

        assignment_grade = AssignmentGrade.query \
            .filter_by(
                user_id=acj_user.id,
                assignment_id=acj_assignment.id
            ) \
            .one_or_none()

        # generate requests
        for lti_resource_link in lti_resource_links:
            lti_consumer = lti_resource_link.lti_consumer
            resource_link_grades = []
            if not lti_consumer.lis_outcome_service_url:
                continue

            lti_user_resource_links = lti_resource_link.lti_user_resource_links \
                .join("lti_user") \
                .filter(LTIUser.acj_user_id == acj_user.id) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                assignment_grade_id = assignment_grade.id if assignment_grade else None

                resource_link_grades.append((lis_result_sourcedid, assignment_grade_id))

            if len(resource_link_grades) == 0:
                continue

            update_lti_assignment_grades.delay(lti_consumer.id, resource_link_grades)

    @classmethod
    def update_course_grades(cls, acj_course):
        from acj.models import CourseRole, CourseGrade, \
            LTIResourceLink, LTIUserResourceLink
        from acj.tasks.lti_outcomes import update_lti_course_grades

        lti_contexts = acj_course.lti_contexts.all()

        # nothing to update if course not linked to any lti contexts
        if len(lti_contexts) == 0:
            return

        course_grades = CourseGrade.query \
            .filter_by(course_id=acj_course.id) \
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
                    LTIResourceLink.acj_assignment_id == None
                ) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                course_grade_id = user_grades.get(lti_user_resource_link.acj_user_id)

                lti_context_grades.append((lis_result_sourcedid, course_grade_id))

            if len(lti_context_grades) == 0:
                continue

            update_lti_course_grades.delay(lti_consumer.id, lti_context_grades)

    @classmethod
    def update_user_course_grade(cls, acj_course, acj_user):
        from acj.models import CourseRole, CourseGrade, \
            LTIResourceLink, LTIUserResourceLink
        from acj.tasks.lti_outcomes import update_lti_course_grades

        lti_contexts = acj_course.lti_contexts.all()

        # nothing to update if course not linked to any lti contexts
        if len(lti_contexts) == 0:
            return

        course_grade = CourseGrade.query \
            .filter_by(
                user_id=acj_user.id,
                course_id=acj_course.id
            ) \
            .one_or_none()

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
                    LTIUser.acj_user_id == acj_user.id,
                    LTIResourceLink.lti_context_id == lti_context.id,
                    LTIResourceLink.acj_assignment_id == None
                ) \
                .all()

            for lti_user_resource_link in lti_user_resource_links:
                if (not lti_user_resource_link.lis_result_sourcedid or
                        lti_user_resource_link.course_role != CourseRole.student):
                    continue

                lis_result_sourcedid = lti_user_resource_link.lis_result_sourcedid
                course_grade_id = course_grade.id if course_grade else None

                lti_context_grades.append((lis_result_sourcedid, course_grade_id))

            if len(lti_context_grades) == 0:
                continue

            update_lti_course_grades.delay(lti_consumer.id, lti_context_grades)

    @classmethod
    def post_replace_result(cls, lti_consumer, lis_result_sourcedid, grade):
        """
        grade must be in range: [0.0, 1.0]
        """

        if not lti_consumer.lis_outcome_service_url or not lis_result_sourcedid:
            # cannot send grade if no lis_outcome_service_url or lis_outcome_service_url
            return

        # build outcome request
        request = ACJOutcomeRequest({
            "consumer_key": lti_consumer.oauth_consumer_key,
            "consumer_secret": lti_consumer.oauth_consumer_secret,
            "lis_outcome_service_url": lti_consumer.lis_outcome_service_url,
            "lis_result_sourcedid": lis_result_sourcedid,
        })
        request.post_replace_result(grade)

        if request.was_outcome_post_successful():
            current_app.logger.debug("Successfully grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade))
        else:
            current_app.logger.error("Failed grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade))

class ACJOutcomeRequest(OutcomeRequest):
    # override post_outcome_request in order to use LTI_ENFORCE_SSL
    def post_outcome_request(self, **kwargs):
        '''
        POST an OAuth signed request to the Tool Consumer.
        '''
        import requests
        from requests_oauthlib import OAuth1
        from requests_oauthlib.oauth1_auth import SIGNATURE_TYPE_AUTH_HEADER

        from lti.outcome_response import OutcomeResponse
        from lti.utils import InvalidLTIConfigError

        if not self.has_required_attributes():
            raise InvalidLTIConfigError(
                'OutcomeRequest does not have all required attributes')

        header_oauth = OAuth1(self.consumer_key, self.consumer_secret,
                       signature_type=SIGNATURE_TYPE_AUTH_HEADER,
                       force_include_body=True, **kwargs)

        headers = {'Content-type': 'application/xml'}

        verify = current_app.config.get('LTI_ENFORCE_SSL', True)
        resp = requests.post(self.lis_outcome_service_url, auth=header_oauth,
                             data=self.generate_request_xml(),
                             headers=headers, verify=verify)
        outcome_resp = OutcomeResponse.from_post_response(resp, resp.content)
        self.outcome_response = outcome_resp
        return self.outcome_response
