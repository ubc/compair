# A barebones example of how to start an API module

from flask import Blueprint
from flask.ext.login import login_required
from flask.ext.restful import Resource

from .util import new_restful_api


# First declare a Flask Blueprint for this module
example_api = Blueprint('example_api', __name__)
# Then pack the blueprint into a Flask-Restful API
api = new_restful_api(example_api)


# declare an API URL
# /
class ExampleRootAPI(Resource):
	@login_required
	def get(self):
		pass
api.add_resource(ExampleRootAPI, '')
