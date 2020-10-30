from tincan import Agent, AgentAccount
from flask import current_app
from compair.models import ThirdPartyType

from compair.learning_records.resource_iri import ResourceIRI

class XAPIActor(object):
    @classmethod
    def _generate_compair_account(cls, user):
        return AgentAccount(
            name=user.uuid,
            home_page=ResourceIRI.actor_homepage()
        )

    @classmethod
    def _generate_global_unique_identifier_account(cls, user):
        name = user.global_unique_identifier
        homepage = current_app.config.get('LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE')
        if not name or not homepage:
            return None

        if not homepage.endswith('/'):
            homepage += '/'

        return AgentAccount(
            name=name,
            home_page=homepage
        )

    @classmethod
    def generate_actor(cls, user):
        actor = Agent(
            name=user.fullname
        )

        if current_app.config.get('LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'):
            account = cls._generate_global_unique_identifier_account(user)
            if account:
                actor.account = account

        # set account to compair account by default
        if not actor.account:
            actor.account = cls._generate_compair_account(user)

        return actor