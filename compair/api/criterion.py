from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask_login import login_required, current_user
from flask_restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import or_, and_

from . import dataformat
from compair.core import event, db
from compair.authorization import require, allow
from compair.models import Criterion
from .util import new_restful_api

criterion_api = Blueprint('criterion_api', __name__)
api = new_restful_api(criterion_api)

new_criterion_parser = reqparse.RequestParser()
new_criterion_parser.add_argument('name', type=str, required=True)
new_criterion_parser.add_argument('description', type=str)
new_criterion_parser.add_argument('default', type=bool, default=True)

existing_criterion_parser = reqparse.RequestParser()
existing_criterion_parser.add_argument('id', type=str, required=True)
existing_criterion_parser.add_argument('name', type=str, required=True)
existing_criterion_parser.add_argument('description', type=str)
existing_criterion_parser.add_argument('default', type=bool, default=True)

# events
on_criterion_list_get = event.signal('CRITERION_LIST_GET')
on_criterion_get = event.signal('CRITERION_GET')
on_criterion_update = event.signal('CRITERION_EDIT')
on_criterion_create = event.signal('CRITERION_CREATE')

# /criteria - public + authored/default
# default = want criterion available to all of the author's assignments
class CriteriaAPI(Resource):
    @login_required
    def get(self):
        if allow(MANAGE, Criterion):
            # TODO: revisit at some point (might retrieve to much in the future)
            criteria = Criterion.query \
                .filter_by(active=True) \
                .order_by(Criterion.public.desc(), Criterion.created) \
                .all()
        else:
            criteria = Criterion.query \
                .filter(or_(
                    and_(
                        Criterion.user_id == current_user.id,
                        Criterion.default == True
                    ),
                    Criterion.public == True
                )) \
                .order_by(Criterion.public.desc(), Criterion.created) \
                .all()

        on_criterion_list_get.send(
            self,
            event_name=on_criterion_list_get.name,
            user=current_user)

        return { 'objects': marshal(criteria, dataformat.get_criterion()) }

    @login_required
    def post(self):
        params = new_criterion_parser.parse_args()

        criterion = Criterion(user_id=current_user.id)
        require(CREATE, criterion)

        criterion.name = params.get("name")
        criterion.description = params.get("description", None)
        criterion.default = params.get("default")

        db.session.add(criterion)
        db.session.commit()

        on_criterion_create.send(
            self,
            event_name=on_criterion_create.name,
            user=current_user,
            criterion=criterion,
            data={'criterion': marshal(criterion, dataformat.get_criterion())}
        )

        return marshal(criterion, dataformat.get_criterion())


api.add_resource(CriteriaAPI, '')


# /criteria/:criterion_uuid
class CriteriaIdAPI(Resource):
    @login_required
    def get(self, criterion_uuid):
        criterion = Criterion.get_active_by_uuid_or_404(criterion_uuid)
        require(READ, criterion)

        on_criterion_get.send(
            self,
            event_name=on_criterion_get.name,
            user=current_user
        )

        return marshal(criterion, dataformat.get_criterion())

    @login_required
    def post(self, criterion_uuid):
        criterion = Criterion.get_active_by_uuid_or_404(criterion_uuid)
        require(EDIT, criterion)

        params = existing_criterion_parser.parse_args()

        criterion.name = params.get('name', criterion.name)
        criterion.description = params.get('description', criterion.description)
        criterion.default = params.get('default', criterion.default)

        db.session.commit()

        on_criterion_update.send(
            self,
            event_name=on_criterion_update.name,
            user=current_user,
            criterion=criterion
        )

        return marshal(criterion, dataformat.get_criterion())


api.add_resource(CriteriaIdAPI, '/<criterion_uuid>')
