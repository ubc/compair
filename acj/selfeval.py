from flask import Blueprint, current_app
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal

from . import dataformat
from .core import event
from .models import SelfEvaluationTypes
from .util import new_restful_api

selfeval_api = Blueprint('selfeval_api', __name__)
api = new_restful_api(selfeval_api)

# events
selfevaltype_get = event.signal('SELFEVAL_TYPE_GET')

#/
class SelfEvalTypeRootAPI(Resource):
	@login_required
	def get(self):
		types = SelfEvaluationTypes.query.\
			order_by(SelfEvaluationTypes.id.desc()).all()
		return {"types": marshal(types, dataformat.getSelfEvalTypes())}
api.add_resource(SelfEvalTypeRootAPI, '')