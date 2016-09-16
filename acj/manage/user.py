"""
    User Management
"""

from flask_script import Manager

from acj.core import db
from acj.models import User

manager = Manager(usage="Manage Users")


@manager.option('password', help='Specify a password.')
@manager.option('username', help='Specify a user.')
def password(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise RuntimeError("User with username {} is not found.".format(username))

    user.password = password

    db.session.add(user)
    db.session.commit()

    print "Password has been updated."
