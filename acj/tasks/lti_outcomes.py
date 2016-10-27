from acj.core import celery, db
from acj.models import LTIConsumer, LTIOutcome, CourseGrade, AssignmentGrade
from flask import current_app

@celery.task(ignore_result=True)
def update_lti_course_grades(lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: "+str(lti_consumer.id)+" named: "+lti_consumer.tool_consumer_instance_name)
        for (lis_result_sourcedid, course_grade_id) in sourcedid_and_grades:
            course_grade = CourseGrade.query.find(course_grade_id)
            grade = course_grade.grade if course_grade else 0.0

            current_app.logger.debug("Posting grade for lis_result_sourcedid: "+lis_result_sourcedid)
            LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade)
    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: "+str(lti_consumer_id)+". record not found.")

@celery.task(ignore_result=True)
def update_lti_assignment_grades(lti_consumer_id, sourcedid_and_grades):
    lti_consumer = LTIConsumer.query.get(lti_consumer_id)
    if lti_consumer:
        current_app.logger.info("Begin LTI Outcomes grade update for lti_consumer: "+str(lti_consumer.id)+" named: "+lti_consumer.tool_consumer_instance_name)
        for (lis_result_sourcedid, assignment_grade_id) in sourcedid_and_grades:
            assignment_grade = AssignmentGrade.query.find(assignment_grade_id)
            grade = assignment_grade.grade if assignment_grade else 0.0

            current_app.logger.debug("Posting grade for lis_result_sourcedid: "+lis_result_sourcedid)
            LTIOutcome.post_replace_result(lti_consumer, lis_result_sourcedid, grade)
    else:
        current_app.logger.info("Failed LTI Outcomes grade update for lti_consumer with id: "+str(lti_consumer_id)+". record not found.")