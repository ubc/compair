import json
import socket

from compair.core import celery
from compair.xapi import XAPI
from flask import current_app

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def send_lrs_statement(self, statement_string):
    try:
        XAPI._send_lrs_statement(json.loads(statement_string))
    except socket.error as error:
        # don't raise connection refused error when in eager mode
        if error.errno != socket.errno.ECONNREFUSED:
            return

        raise error