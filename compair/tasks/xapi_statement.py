from compair.core import celery
from compair.xapi import XAPI

@celery.task(ignore_result=True)
def send_lrs_statements(statements):
    XAPI._send_lrs_statements(statements)