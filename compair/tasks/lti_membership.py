import requests

from compair.core import celery, db
from compair.models import Course, LTIMembership
from flask import current_app

@celery.task(bind=True, ignore_result=True)
def update_lti_course_membership(self, course_id):
    course = Course.query.get(course_id)
    if course:
        current_app.logger.info("Begin LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)

        try:
            LTIMembership.update_membership_for_course(course)

        except requests.exceptions.ConnectTimeout as error:
            current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". "+str(error))
            if not self.request.is_eager:
                self.retry(error)

        except requests.exceptions.ConnectionError as error:
            current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". "+str(error))
            if not self.request.is_eager:
                self.retry(error)

        current_app.logger.info("Compelted LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)
    else:
        current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". record not found.")