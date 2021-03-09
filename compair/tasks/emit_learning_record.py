import json
import socket
import datetime
from sqlalchemy import and_, or_

from compair.core import celery
from flask import current_app
from compair.models import CaliperLog, XAPILog
from compair.core import db

@celery.task(bind=True, autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 1},
    ignore_result=True, store_errors_even_if_ignored=True)
def emit_lrs_xapi_statement(self, xapi_log_id):
    from compair.learning_records import XAPI

    xapi_log = XAPILog.query \
        .filter_by(
            id=xapi_log_id,
            transmitted=False
        ) \
        .one_or_none()

    if xapi_log:
        try:
            XAPI._emit_to_lrs(json.loads(xapi_log.statement))
        except socket.error as error:
            # don't raise connection refused error when in eager mode
            if error.errno != socket.errno.ECONNREFUSED:
                current_app.logger.error("emit_lrs_xapi_statement connection refused: "+socket.error.strerror)
                return
            raise error

        XAPILog.query \
            .filter_by(id=xapi_log_id) \
            .delete()
        db.session.commit()

@celery.task(bind=True, autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 1},
    ignore_result=True, store_errors_even_if_ignored=True)
def emit_lrs_caliper_event(self, caliper_log_id):
    from compair.learning_records import CaliperSensor

    caliper_log = CaliperLog.query \
        .filter_by(
            id=caliper_log_id,
            transmitted=False
        ) \
        .one_or_none()

    if caliper_log:
        try:
            CaliperSensor._emit_to_lrs(json.loads(caliper_log.event))
        except socket.error as error:
            # don't raise connection refused error when in eager mode
            if error.errno != socket.errno.ECONNREFUSED:
                current_app.logger.error("emit_lrs_caliper_event connection refused: "+socket.error.strerror)
                return
            raise error

        CaliperLog.query \
            .filter_by(id=caliper_log_id) \
            .delete()
        db.session.commit()


@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def resend_learning_records(self):
    from compair.learning_records import XAPI, CaliperSensor

    # only re-send learning records that have last started over an hour ago
    # (this is to try and prevent sending duplicates if possible)
    one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

    if XAPI.enabled() and not XAPI.storing_locally():
        xapi_logs = XAPILog.query \
            .filter(and_(
                XAPILog.transmitted == False,
                XAPILog.modified <= one_hour_ago
            )) \
            .all()

        for xapi_log in xapi_logs:
            emit_lrs_xapi_statement(xapi_log.id)

    if CaliperSensor.enabled() and not CaliperSensor.storing_locally():
        caliper_logs = CaliperLog.query \
            .filter(and_(
                CaliperLog.transmitted == False,
                CaliperLog.modified <= one_hour_ago
            )) \
            .all()

        for caliper_log in caliper_logs:
            emit_lrs_caliper_event(caliper_log.id)
