import requests

from compair.core import celery, db
from compair.models import Course, LTIMembership
from flask import current_app

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def update_lti_course_membership(self, course_id):
    course = Course.query.get(course_id)
    if course:
        current_app.logger.info("Begin LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)

        LTIMembership.update_membership_for_course(course)

        current_app.logger.info("Compelted LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)
    else:
        current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". record not found.")