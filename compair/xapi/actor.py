from tincan import Agent, AgentAccount
from flask import current_app
from compair.models import ThirdPartyType

from .resource_iri import XAPIResourceIRI

class XAPIActor(object):
    @classmethod
    def _generate_compair_account(cls, user):
        return AgentAccount(
            name=user.uuid,
            home_page=XAPIResourceIRI.actor_homepage()
        )

    @classmethod
    def _generate_third_party_account(cls, third_party_user):
        identifier = None
        if third_party_user.third_party_type == ThirdPartyType.saml:
            identifier = current_app.config.get('LRS_ACTOR_ACCOUNT_SAML_IDENTIFIER')
        elif third_party_user.third_party_type == ThirdPartyType.cas:
            identifier = current_app.config.get('LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER')

        homepage = current_app.config.get('LRS_ACTOR_ACCOUNT_THIRD_PARTY_HOMEPAGE')
        name = None

        if not identifier:
            name = third_party_user.unique_identifier
        elif third_party_user.params:
            name = third_party_user.params.get(identifier, None)
            # fix for saml attribute arrays
            if isinstance(name, list):
                name = name[0] if len(name) > 0 else None

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

        if current_app.config.get('LRS_ACTOR_ACCOUNT_USE_THIRD_PARTY'):
            from compair.models import ThirdPartyType, ThirdPartyUser

            third_party_users = user.third_party_auths \
                .order_by(ThirdPartyUser.third_party_type.desc(), ThirdPartyUser.created) \
                .all()

            for third_party_user in third_party_users:
                account = cls._generate_third_party_account(third_party_user)
                if account:
                    actor.account = account
                    break

        # set account to compair account by default
        if not actor.account:
            actor.account = cls._generate_compair_account(user)

        return actor