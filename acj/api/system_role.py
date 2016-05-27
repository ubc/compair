from flask import Blueprint
from flask.ext.restful import Resource
from flask_login import login_required, current_user

from acj.core import event
from .util import new_restful_api
from acj.models import SystemRole


system_roles_api = Blueprint('system_roles_api', __name__)

# events
on_system_role_all_get = event.signal('SYSTEM_ROLES_ALL_GET')

# /
class SystemRoleAPI(Resource):
    @login_required
    def get(self):
        system_roles = [
            SystemRole.student.value,
            SystemRole.instructor.value,
            SystemRole.sys_admin.value
        ]

        if current_user.system_role != SystemRole.sys_admin:
            system_roles.pop()

        on_system_role_all_get.send(
            self,
            event_name=on_system_role_all_get.name,
            user=current_user
        )

        return system_roles
        
apiT = new_restful_api(system_roles_api)
apiT.add_resource(SystemRoleAPI, '')