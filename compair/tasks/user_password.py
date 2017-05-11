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
        user.password = user_passwords.get(user.id, None)

    db.session.add_all(users)
    db.session.commit()