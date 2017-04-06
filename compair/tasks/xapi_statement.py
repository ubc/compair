import json

from compair.core import celery
from compair.xapi import XAPI

@celery.task(bind=True, ignore_result=True)
def send_lrs_statements(self, statements):
    statements = [json.loads(statement) for statement in statements]
    XAPI._send_lrs_statements(statements)