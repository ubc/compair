from acj.core import celery, db
from acj.models import User

@celery.task(ignore_result=True)
def set_passwords(user_passwords):
    user_ids = user_passwords.keys()

    users = User.query \
        .filter(User.id.in_(user_ids)) \
        .all()

    for user in users:
        user.password = user_passwords.get(user.id, None)

    db.session.add_all(users)
    db.session.commit()