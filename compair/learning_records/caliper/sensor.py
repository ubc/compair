# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)

import json
import caliper
from caliper import condensor

from compair.tasks import emit_lrs_caliper_event

from caliper.constants import CALIPER_VERSION, CALIPER_CORE_CONTEXT

from flask import current_app, request
from .actor import CaliperActor
from compair.models import CaliperLog
from compair.core import db
from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.resource_iri import ResourceIRI
from six import text_type

class CaliperSensor(LearningRecord):
    _version = CALIPER_VERSION
    _core_context = CALIPER_CORE_CONTEXT

    @classmethod
    def enabled(cls):
        return current_app.config.get('CALIPER_ENABLED')

    @classmethod
    def storing_locally(cls):
        return current_app.config.get('LRS_CALIPER_HOST') == 'local'

    @classmethod
    def _get_config(cls):
        return caliper.HttpOptions(
            host=text_type(current_app.config.get('LRS_CALIPER_HOST')),
            auth_scheme='Bearer',
            api_key=text_type(current_app.config.get('LRS_CALIPER_API_KEY'))
        )

    @classmethod
    def _get_sensor(cls):
        return caliper.build_sensor_from_config(
            sensor_id = text_type(ResourceIRI.compair()),
            config_options = cls._get_config()
        )

    @classmethod
    def emit(cls, event):
        if not cls.enabled():
            return

        # remove empty fields
        event_dict = json.loads(event.as_json())
        cls._remove_empty_fields(event_dict)

        caliper_log = CaliperLog(
            event=json.dumps(event_dict),
            transmitted=cls.storing_locally()
        )
        db.session.add(caliper_log)
        db.session.commit()

        if not cls.storing_locally():
            emit_lrs_caliper_event.delay(caliper_log.id)

    @classmethod
    def _emit_to_lrs(cls, event_json):
        if not cls.enabled:
            return
        # should only be called by delayed task emit_lrs_caliper_event

        sensor = cls._get_sensor()
        event = condensor.from_json_dict(event_json)

        sensor.send(event)

        # TODO find way to log bad requests

    @classmethod
    def _remove_empty_fields(cls, event_dict):
        # this is done in order to trim down all the empty fields that Caliper will throw in
        keys_to_delete = []
        for k, v in event_dict.items():
            if isinstance(v, dict):
                # recursively remove empty fields
                cls._remove_empty_fields(v)

                if len(v.keys()) == 0:
                    keys_to_delete.append(k)
            elif isinstance(v, list):
                list_index_to_remove = []
                # remove empty fields from list objects
                for index, v2 in enumerate(v):
                    if isinstance(v2, dict):
                        cls._remove_empty_fields(v2)
                        if len(v2.keys()) == 0:
                            list_index_to_remove.append(index)

                for index in reversed(list_index_to_remove):
                    del v[index]

                # remove empty lists
                if len(v) == 0:
                    keys_to_delete.append(k)
            elif v == None:
                keys_to_delete.append(k)

        for k in keys_to_delete:
            del event_dict[k]
