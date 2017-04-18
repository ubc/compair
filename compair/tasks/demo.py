from compair.core import celery, db
from compair.manage.database import reset_demo as _reset_demo

@celery.task(bind=True, ignore_result=True)
def reset_demo(self):
    _reset_demo(yes=True)