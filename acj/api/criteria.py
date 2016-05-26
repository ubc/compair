from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import or_, and_
from sqlalchemy.orm import load_only, contains_eager

from . import dataformat
from acj.core import event, db
from acj.authorization import require, allow
from acj.models import Criteria
from .util import new_restful_api

criteria_api = Blueprint('criteria_api', __name__)
api = new_restful_api(criteria_api)

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
on_criteria_list_get = event.signal('CRITERIA_LIST_GET')
criteria_get = event.signal('CRITERIA_GET')
criteria_update = event.signal('CRITERIA_EDIT')
criteria_create = event.signal('CRITERIA_CREATE')

# /criteria - public + authored/default
# default = want criterion available to all of the author's assignments
class CriteriaAPI(Resource):
    @login_required
    def get(self):
        if allow(MANAGE, Criteria):
            criteria = Criteria.query \
                .order_by(Criteria.public.desc(), Criteria.created) \
                .all()
        else:
            criteria = Criteria.query \
                .filter(or_(
                    and_(
                        Criteria.user_id == current_user.id, 
                        Criteria.default == True
                    ), 
                    Criteria.public == True
                )) \
                .order_by(Criteria.public.desc(), Criteria.created) \
                .all()

        on_criteria_list_get.send(
            self,
            event_name=on_criteria_list_get.name,
            user=current_user)

        return { 'objects': marshal(criteria, dataformat.get_criteria()) }

    @login_required
    def post(self):
        params = new_criterion_parser.parse_args()
        
        criterion = Criteria(user_id=current_user.id)
        require(CREATE, criterion)
        
        criterion.name = params.get("name")
        criterion.description = params.get("description", None)
        criterion.default = params.get("default")
        
        db.session.add(criterion)
        db.session.commit()

        criteria_create.send(
            self,
            event_name=criteria_create.name,
            user=current_user,
            data={'criterion': marshal(criterion, dataformat.get_criteria())}
        )

        return marshal(criterion, dataformat.get_criteria())


api.add_resource(CriteriaAPI, '')


# /criteria/:id
class CriteriaIdAPI(Resource):
    @login_required
    def get(self, criteria_id):
        criterion = Criteria.get_active_or_404(criteria_id)
        require(READ, criterion)

        criteria_get.send(
            self,
            event_name=criteria_get.name,
            user=current_user
        )

        return marshal(criterion, dataformat.get_criteria())

    @login_required
    def post(self, criteria_id):
        criterion = Criteria.get_active_or_404(criteria_id)
        require(EDIT, criterion)
        
        params = existing_criterion_parser.parse_args()
        criterion.name = params.get('name', criterion.name)
        criterion.description = params.get('description', criterion.description)
        criterion.default = params.get('default', criterion.default)
        db.session.add(criterion)
        db.session.commit()

        criteria_update.send(
            self,
            event_name=criteria_update.name,
            user=current_user
        )

        return marshal(criterion, dataformat.get_criteria())


api.add_resource(CriteriaIdAPI, '/<int:criteria_id>')
