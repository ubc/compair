from compair.core import celery, db
from compair.manage.database import recreate

# retry in 30 seconds, need to be fast since database might be in a bad state
# if error occurred during database populate (since database drop/create cannot be rolled back)
@celery.task(bind=True, autoretry_for=(Exception,),
    default_retry_delay=30.0, ignore_result=True, store_errors_even_if_ignored=True)
def reset_demo(self):
    recreate(yes=True, default_data=True, sample_data=True)