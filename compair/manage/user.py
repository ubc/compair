"""
    User Management
"""

import click
from flask.cli import AppGroup

from compair.core import db
from compair.models import User, ThirdPartyUser, ThirdPartyType, LTIUser


user_cli = AppGroup('user', help="Manage Users")

@user_cli.command('password')
@click.argument('username')
@click.argument('password')
def password(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise RuntimeError(f"User with username {username} is not found.")

    user.password = password

    db.session.add(user)
    db.session.commit()

    print("Password has been updated.")

@user_cli.command('generate-global-unique-identifiers')
def generate_global_unique_identifiers():
    # we will attempt to fill global_unique_identifier in for users currently missing one

    # get all users who currently do not have no global_unique_identifier set
    users = User.query \
        .filter_by(global_unique_identifier=None) \
        .all()

    print(f"{len(users)} user(s) with no global unique identifier found.")

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

        print(f"Adding global unique identifiers for {update_count} user(s).")
        db.session.commit()

    print("Done")