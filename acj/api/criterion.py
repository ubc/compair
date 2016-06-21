from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import or_, and_

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from acj.models import Criterion
from .util import new_restful_api

criterion_api = Blueprint('criterion_api', __name__)
api = new_restful_api(criterion_api)

new_criterion_parser = reqparse.RequestParser()
new_criterion_parser.add_argument('name', type=str, required=True)
new_criterion_parser.add_argument('description', type=str)
new_criterion_parser.add_argument('default', type=bool, default=True)

existing_criterion_parser = reqparse.RequestParser()
existing_criterion_parser.add_argument('id', type=int, required=True)
existing_criterion_parser.add_argument('name', type=str, required=True)
existing_criterion_parser.add_argument('description', type=str)
existing_criterion_parser.add_argument('default', type=bool, default=True)

# events
on_criterion_list_get = event.signal('CRITERION_LIST_GET')
criterion_get = event.signal('CRITERION_GET')
criterion_update = event.signal('CRITERION_EDIT')
criterion_create = event.signal('CRITERION_CREATE')

# /criteria - public + authored/default
# default = want criterion available to all of the author's assignments
class CriteriaAPI(Resource):
    @login_required
    def get(self):
        if allow(MANAGE, Criterion):
            criteria = Criterion.query \
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

        criterion_create.send(
            self,
            event_name=criterion_create.name,
            user=current_user,
            data={'criterion': marshal(criterion, dataformat.get_criterion())}
        )

        return marshal(criterion, dataformat.get_criterion())


api.add_resource(CriteriaAPI, '')


# /criteria/:id
class CriteriaIdAPI(Resource):
    @login_required
    def get(self, criterion_id):
        criterion = Criterion.get_active_or_404(criterion_id)
        require(READ, criterion)

        criterion_get.send(
            self,
            event_name=criterion_get.name,
            user=current_user
        )

        return marshal(criterion, dataformat.get_criterion())

    @login_required
    def post(self, criterion_id):
        criterion = Criterion.get_active_or_404(criterion_id)
        require(EDIT, criterion)

        params = existing_criterion_parser.parse_args()
        criterion.name = params.get('name', criterion.name)
        criterion.description = params.get('description', criterion.description)
        criterion.default = params.get('default', criterion.default)
        db.session.add(criterion)
        db.session.commit()

        criterion_update.send(
            self,
            event_name=criterion_update.name,
            user=current_user
        )

        return marshal(criterion, dataformat.get_criterion())


api.add_resource(CriteriaIdAPI, '/<int:criterion_id>')
