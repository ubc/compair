import requests

from compair.core import celery, db
from compair.models import LTIConsumer, LTIOutcome, CourseGrade, AssignmentGrade
from flask import current_app

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def update_lti_course_grades(self, lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: {} named: {}".format(lti_consumer.id, lti_consumer.tool_consumer_instance_name))
        for (lis_result_sourcedid, course_grade_id) in sourcedid_and_grades:
            if course_grade_id:
                course_grade = CourseGrade.query.get(course_grade_id)
                grade = 0.0
                submittedAt = None
                if course_grade:
                    grade = course_grade.grade
                    # This is timezone unaware, so we have to add a timezone to
                    # it (to properly follow iso 8601). We convert it to the
                    # compair server timezone, on the assumption that the
                    # compair server timezone is the same as mariadb's
                    # timezone.
                    submittedAt = course_grade.modified.astimezone().isoformat()

                current_app.logger.debug("Posting grade for lis_result_sourcedid: {}".format(lis_result_sourcedid))
                current_app.logger.debug("Submitted At Time: {}".format(submittedAt))

                LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade, submittedAt)

    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: {}. record not found.".format(lti_consumer_id))

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def update_lti_assignment_grades(self, lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: {} named: {}".format(lti_consumer.id, lti_consumer.tool_consumer_instance_name))
        for (lis_result_sourcedid, assignment_grade_id) in sourcedid_and_grades:
            if assignment_grade_id:
                assignment_grade = AssignmentGrade.query.get(assignment_grade_id)
                grade = 0.0
                submittedAt = None
                if assignment_grade:
                    grade = assignment_grade.grade
                    submittedAt = assignment_grade.modified.astimezone().isoformat()

                current_app.logger.debug("Posting grade for lis_result_sourcedid: {}".format(lis_result_sourcedid))
                current_app.logger.debug("Submitted At Time: {}".format(submittedAt))

                LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade, submittedAt)
    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: {}. record not found.".format(lti_consumer_id))
