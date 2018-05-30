"""
    User Management
"""

from flask_script import Manager

from compair.core import db
from compair.models import User, ThirdPartyUser, ThirdPartyType, \
    LTIUser
from flask import current_app

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

    print("Password has been updated.")

@manager.command
def generate_global_unique_identifiers():
    # we will attempt to fill global_unique_identifier in for users currently missing one

    # get all users who currently do not have no global_unique_identifier set
    users = User.query \
        .filter_by(global_unique_identifier=None) \
        .all()

    print("{} user(s) with no global unique identifier found.".format(
        len(users)
    ))

    if len(users) > 0:
        update_count = 0
        for user in users:
            lti_user = user.lti_user_links \
                .filter(LTIUser.global_unique_identifier != None) \
                .first()

            if lti_user:
                user.global_unique_identifier = lti_user.global_unique_identifier
                update_count += 1
                continue

            third_party_users = user.third_party_auths.all()

            for third_party_user in third_party_users:
                if third_party_user.global_unique_identifier:
                    user.global_unique_identifier = third_party_user.global_unique_identifier
                    update_count += 1
                    break

        print("Adding global unique identifiers for {} user(s).".format(
            update_count
        ))
        db.session.commit()

    print("Done")