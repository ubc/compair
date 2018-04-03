import requests

from compair.core import celery, db
from compair.models import Course, LTIMembership
from compair.models.lti_models import MembershipNoValidContextsException, \
    MembershipNoResultsException, MembershipInvalidRequestException
from flask import current_app

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def update_lti_course_membership(self, course_id):
    course = Course.query.get(course_id)
    if course:
        current_app.logger.info("Begin LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)

        # allow MembershipNoValidContextsException exceptions to occur without retrying job
        try:
            LTIMembership.update_membership_for_course(course)
        except MembershipNoValidContextsException as err:
            current_app.logger.warning("Error for LTI Membership update for course with id: "+str(course_id)+" named: "+course.name+". No valid lti contexts are linked to the course")
        except MembershipNoResultsException as err:
            current_app.logger.warning("Error for LTI Membership update for course with id: "+str(course_id)+" named: "+course.name+". The LTI link does not support the membership extension")
        except MembershipInvalidRequestException as err:
            current_app.logger.warning("Error for LTI Membership update for course with id: "+str(course_id)+" named: "+course.name+". The membership request was invalid")

        current_app.logger.info("Completed LTI Membership update for course with id: "+str(course_id)+" named: "+course.name)
    else:
        current_app.logger.info("Failed LTI Membership update for course with id: "+str(course_id)+". record not found.")