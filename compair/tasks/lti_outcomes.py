import requests

from compair.core import celery, db
from compair.models import LTIConsumer, LTIOutcome, CourseGrade, AssignmentGrade
from flask import current_app

@celery.task(bind=True, ignore_result=True)
def update_lti_course_grades(self, lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: "+str(lti_consumer.id)+" named: "+lti_consumer.tool_consumer_instance_name)
        for (lis_result_sourcedid, course_grade_id) in sourcedid_and_grades:
            if course_grade_id:
                course_grade = CourseGrade.query.get(course_grade_id)
                grade = course_grade.grade if course_grade else 0.0

                current_app.logger.debug("Posting grade for lis_result_sourcedid: "+lis_result_sourcedid)

                try:
                    LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade)

                except requests.exceptions.ConnectTimeout as error:
                    current_app.logger.error("Failed grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade) + ". "+str(error))
                    if not self.request.is_eager:
                        self.retry(error)

                except requests.exceptions.ConnectionError as error:
                    current_app.logger.error("Failed grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade) + ". "+str(error))
                    if not self.request.is_eager:
                        self.retry(error)

    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: "+str(lti_consumer_id)+". record not found.")

@celery.task(bind=True, ignore_result=True)
def update_lti_assignment_grades(self, lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: "+str(lti_consumer.id)+" named: "+lti_consumer.tool_consumer_instance_name)
        for (lis_result_sourcedid, assignment_grade_id) in sourcedid_and_grades:
            if assignment_grade_id:
                assignment_grade = AssignmentGrade.query.get(assignment_grade_id)
                grade = assignment_grade.grade if assignment_grade else 0.0

                current_app.logger.debug("Posting grade for lis_result_sourcedid: "+lis_result_sourcedid)

                try:
                    LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade)

                except requests.exceptions.ConnectTimeout as error:
                    current_app.logger.error("Failed grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade) + ". "+str(error))
                    if not self.request.is_eager:
                        self.retry(error)

                except requests.exceptions.ConnectionError as error:
                    current_app.logger.error("Failed grade update for lis_result_sourcedid: " + lis_result_sourcedid + " with grade: "+str(grade) + ". "+str(error))
                    if not self.request.is_eager:
                        self.retry(error)
    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: "+str(lti_consumer_id)+". record not found.")