from tincan import Agent, AgentAccount
from flask import current_app

from .resource_iri import XAPIResourceIRI

class XAPIActor(object):
    @classmethod
    def _generate_compair_account(cls, user):
        return AgentAccount(
            name=user.uuid,
            home_page=XAPIResourceIRI.actor_homepage()
        )

    @classmethod
    def _generate_cas_account(cls, cas_user):
        identifier = current_app.config.get('LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER')
        homepage = current_app.config.get('LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE')
        name = None

        if not identifier:
            name = cas_user.unique_identifier
        elif cas_user.params:
            name = cas_user.params.get(identifier, None)

        if not (name and homepage):
            return None

        return AgentAccount(
            name=name,
            home_page=homepage
        )

    @classmethod
    def generate_actor(cls, user):
        actor = Agent(
            name=user.fullname
        )

        if current_app.config.get('LRS_ACTOR_ACCOUNT_USE_CAS'):
            from compair.models import ThirdPartyType

            cas_user = user.third_party_auths \
                .filter_by(third_party_type=ThirdPartyType.cas) \
                .first()

            if cas_user:
                actor.account = cls._generate_cas_account(cas_user)

        # set account to compair account by default
        if not actor.account:
            actor.account = cls._generate_compair_account(user)

        return actor