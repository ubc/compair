# -*- coding: utf-8 -*-
#
from __future__ import (absolute_import, division, print_function, unicode_literals)
from future.standard_library import install_aliases
install_aliases()

import json
import caliper
from caliper import condensor

from compair.tasks import emit_lrs_caliper_event

from caliper.constants import CALIPER_VERSION

from flask import current_app, request
from .actor import CaliperActor
from compair.models import CaliperLog
from compair.core import db
from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.resource_iri import ResourceIRI
from six import text_type, string_types

class CaliperSensor(LearningRecord):
    _version = CALIPER_VERSION

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
            sensor_id = ResourceIRI.compair(),
            config_options = cls._get_config()
        )

    @classmethod
    def emit(cls, event):
        if not cls.enabled():
            return

        caliper_log = CaliperLog(
            event=event.as_json(),
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
