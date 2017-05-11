import json
import socket

from compair.core import celery
from compair.xapi import XAPI
from flask import current_app

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def send_lrs_statements(self, statements):
    try:
        statements = [json.loads(statement) for statement in statements]
        XAPI._send_lrs_statements(statements)
    except socket.error as error:
        # don't raise connection refused error when in eager mode
        if error.errno != socket.errno.ECONNREFUSED:
            return

        raise error