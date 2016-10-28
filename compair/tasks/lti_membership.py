from compair.core import celery, db
from compair.models import Course, LTIMembership
from flask import current_app

@celery.task(ignore_result=True)
def update_lti_course_membership(course_id):
    course = Course.query.get(course_id)
    if course:
        current_app.logger.info("Begin LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)
        LTIMembership.update_membership_for_course(course)
        current_app.logger.info("Compelted LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)
    else:
        current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". record not found.")