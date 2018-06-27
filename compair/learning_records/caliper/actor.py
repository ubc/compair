# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)
from future.standard_library import install_aliases
install_aliases()

import datetime
import pytz
from flask import current_app

from compair.learning_records.resource_iri import ResourceIRI
from caliper.constants import ENTITY_TYPES as CALIPER_ENTITY_TYPES

class CaliperActor(object):
    @classmethod
    def _generate_compair_account(cls, user):
        return {
            "id": ResourceIRI.actor_homepage()+user.uuid,
            "type": CALIPER_ENTITY_TYPES["PERSON"],
            "name": user.fullname,
            "dateCreated": user.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": user.modified.replace(tzinfo=pytz.utc).isoformat(),
        }

    @classmethod
    def _generate_global_unique_identifier_account(cls, user):
        external_id = user.global_unique_identifier
        homepage = current_app.config.get('LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE')
        if not external_id or not homepage:
            return cls._generate_compair_account(user)

        if not homepage.endswith('/'):
            homepage += '/'

        return {
            "id": homepage+external_id,
            "type": CALIPER_ENTITY_TYPES["PERSON"],
            "name": user.fullname,
            "dateCreated": user.created.replace(tzinfo=pytz.utc).isoformat(),
            "dateModified": user.modified.replace(tzinfo=pytz.utc).isoformat(),
            "extensions": {
                "externalUserId": external_id,
                "edAppUserId": user.uuid
            }
        }

    @classmethod
    def generate_actor(cls, user):
        actor = None
        if current_app.config.get('LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER'):
            actor = cls._generate_global_unique_identifier_account(user)

        # set account to compair account by default
        if not actor:
            actor = cls._generate_compair_account(user)
        return actor

