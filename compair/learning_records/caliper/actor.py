# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)

import caliper
import datetime
import pytz
from flask import current_app

from compair.learning_records.resource_iri import ResourceIRI
from caliper.constants import CALIPER_SYSIDTYPES as CALIPER_SYSTEM_TYPES

class CaliperActor(object):
    @classmethod
    def _generate_other_identifiers(cls, user):
        otherIdentifiers = []
        # add other lti user id identifiers
        if user.lti_linked:
            for lti_user in user.lti_user_links.all():
                lti_consumer = lti_user.lti_consumer

                otherIdentifiers.append(caliper.entities.SystemIdentifier(
                    identifier=lti_user.user_id,
                    identifierType=CALIPER_SYSTEM_TYPES['LTI_USERID'],
                    source=lti_consumer.tool_consumer_instance_url,
                    extensions={
                        "oauth_consumer_key": lti_user.oauth_consumer_key,
                        "global_unique_identifier": lti_user.global_unique_identifier,
                        "student_number": lti_user.student_number,
                        "lis_person_sourcedid": lti_user.lis_person_sourcedid,
                    }
                ))

        # add third party auths
        if user.has_third_party_auth:
            for third_party_user in user.third_party_auths.all():
                otherIdentifiers.append(caliper.entities.SystemIdentifier(
                    identifier=third_party_user.unique_identifier,
                    identifierType=CALIPER_SYSTEM_TYPES['SYSTEM_ID'],
                    extensions={
                        "third_party_type": third_party_user.third_party_type.value,
                        "_params": third_party_user._params,
                    }
                ))
        return otherIdentifiers

    @classmethod
    def _generate_compair_account(cls, user):
        return caliper.entities.Person(
            id=ResourceIRI.actor_homepage()+user.uuid,
            name=user.fullname,
            dateCreated=user.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=user.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            otherIdentifiers=cls._generate_other_identifiers(user)
        )

    @classmethod
    def _generate_global_unique_identifier_account(cls, user):
        external_id = user.global_unique_identifier
        homepage = current_app.config.get('LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE')
        if not external_id or not homepage:
            return cls._generate_compair_account(user)

        if not homepage.endswith('/'):
            homepage += '/'

        return caliper.entities.Person(
            id=homepage+external_id,
            name=user.fullname,
            dateCreated=user.created.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            dateModified=user.modified.replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            otherIdentifiers=cls._generate_other_identifiers(user) + [
                caliper.entities.SystemIdentifier(
                    identifier=external_id,
                    identifierType=CALIPER_SYSTEM_TYPES['SIS_SOURCEDID'],
                    source=homepage
                ),
                caliper.entities.SystemIdentifier(
                    identifier=user.uuid,
                    identifierType=CALIPER_SYSTEM_TYPES['SYSTEM_ID'],
                    source=ResourceIRI.compair()
                )
            ]
        )

    @classmethod
    def generate_actor(cls, user):
        actor = None
        if current_app.config.get('LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'):
            actor = cls._generate_global_unique_identifier_account(user)

        # set account to compair account by default
        if not actor:
            actor = cls._generate_compair_account(user)

        return actor

