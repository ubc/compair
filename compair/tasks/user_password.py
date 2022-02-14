from compair.core import celery, db
from compair.models import User

@celery.task(bind=True, autoretry_for=(Exception,),
    ignore_result=True, store_errors_even_if_ignored=True)
def set_passwords(self, user_passwords):
    user_ids = user_passwords.keys()

    users = User.query \
        .filter(User.id.in_(user_ids)) \
        .all()

    for user in users:
        # note that user_passwords keys are strings, not ints, due to celery's
        # json serialization, so we need to match type
        user.password = user_passwords.get(str(user.id), None)

    db.session.add_all(users)
    db.session.commit()
