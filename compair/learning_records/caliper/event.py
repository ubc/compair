from flask import request
from flask_login import current_user

from compair.core import impersonation

from caliper import condensor
from .actor import CaliperActor
from .entities import CaliperEntities
from .sensor import CaliperSensor
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord

class CaliperEvent(object):
    @classmethod
    def _defaults(cls, user, course=None):
        caliper_actor = CaliperActor.generate_actor(user)
        if impersonation.is_impersonating() and user.id == current_user.id:
            caliper_actor = CaliperActor.generate_actor(impersonation.get_impersonation_original_user())

        defaults = {
            'context': CaliperSensor._core_context,
            'eventTime': LearningRecord.generate_timestamp(),
            'actor': caliper_actor,
            'edApp': CaliperEntities.compair_app()
        }

        session_extensions = {}
        if impersonation.is_impersonating() and user.id == current_user.id:
            session_extensions["impersonating-as"] = CaliperActor.generate_actor(user).as_dict()
        defaults['session'] = CaliperEntities.session(caliper_actor, request, session_extensions)

        if course:
            #todo add 'Group' which is the course or the group within the course
            defaults['membership'] = CaliperEntities.membership(course, user)

        return defaults


    @classmethod
    def generate_from_params(cls, user, params, course=None):
        event = cls._defaults(user, course=course)
        event.update(params)
        return condensor.from_json_dict(event)
