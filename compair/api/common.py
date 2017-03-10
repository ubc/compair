import time

from flask import Blueprint
from flask_restful import Resource
from flask_login import login_required

from .util import new_restful_api

timer_api = Blueprint('timer_api', __name__)

class TimerAPI(Resource):
    @login_required
    def get(self):
        return {'date': int(round(time.time() * 1000))}

api = new_restful_api(timer_api)

api.add_resource(TimerAPI, '')