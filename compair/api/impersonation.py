from copy import copy
from flask import Blueprint, current_app
from flask_login import current_user, login_required
from flask_restful import Resource, marshal

from compair.models import User
from compair.core import abort, impersonation, event
from .util import new_restful_api
from . import dataformat

impersonation_api = Blueprint('impersonation_api', __name__)
IMPERSONATION_API_BASE_URL = '/api/impersonate'

# events
on_impersonation_started = event.signal('IMPERSONATION_STARTED')
on_impersonation_stopped = event.signal('IMPERSONATION_STOPPED')

class ImpersonationAPI(Resource):
    @login_required
    def post(self, user_uuid):
        if not current_app.config.get('IMPERSONATION_ENABLED', False):
            abort(404, title="Impersonation not supported", message="Impersonation function not enabled")

        original_user = User.query.get(current_user.id)
        impersonate_as_uuid = user_uuid
        impersonate_as_user = User.get_by_uuid_or_404(impersonate_as_uuid)
        if not impersonation.can_impersonate(impersonate_as_user.get_id()):
            abort(400, title="Impersonation Failed", message="Cannot perform impersonation")

        impersonation_success = impersonation.start_impersonation(impersonate_as_user.get_id())

        # if successful, from this point on, current_user is no longer the original user

        if not impersonation_success:
            abort(400, title="Impersonation Failed", message="Cannot perform impersonation")

        on_impersonation_started.send(
            self,
            event_name=on_impersonation_started.name,
            user=original_user,
            data={ 'impersonate_as': impersonate_as_user.id })
        # user is impersonating. treat as restrict_user when calling dataformat
        return { 'impersonate_as' : marshal(impersonate_as_user, dataformat.get_user(True)) }

class ImpersonationRootAPI(Resource):
    @login_required
    def get(self):
        if not current_app.config.get('IMPERSONATION_ENABLED', False) or not impersonation.is_impersonating():
            return {'impersonating' : False}

        original_user = impersonation.get_impersonation_original_user()
        impersonate_as_user = current_user
        if original_user is None or impersonate_as_user is None:
            # something went wrong...
            abort(503, title="Cannot check impersonation status", \
                message="Sorry, cannot find information on impersonation status")

        # user is impersonating. treat as restrict_user when calling dataformat
        return { \
            'impersonating' : True,
            'original_user' : marshal(original_user, dataformat.get_user(True))
        }

    @login_required
    def delete(self):
        if not current_app.config.get('IMPERSONATION_ENABLED', False) or not impersonation.is_impersonating():
            abort(404, title="Cannot stop impersonation", message="Sorry, you can't perform that action")

        original_user_id = impersonation.get_impersonation_original_user_id()
        impersonate_as_user_id = impersonation.get_impersonation_act_as_user_id()
        original_user = User.query.get(original_user_id)
        impersonate_as_user = User.query.get(impersonate_as_user_id)
        if original_user is None or impersonate_as_user is None:
            abort(404, title="Cannot stop impersonation", \
                message="Cannot find corresponding information to stop impersonation")

        on_impersonation_stopped.send(
            self,
            event_name=on_impersonation_stopped.name,
            user=original_user,
            data={ 'impersonate_as': impersonate_as_user.id })

        impersonation.end_impersonation()
        return {'success': True}

api = new_restful_api(impersonation_api)
api.add_resource(ImpersonationAPI, '/<user_uuid>')
api.add_resource(ImpersonationRootAPI, '')
