import cProfile
import contextlib
from functools import wraps
import pstats
from enum import Enum
from flask_restful.reqparse import RequestParser

from six import BytesIO, text_type
from flask import request, jsonify
from flask_restful import Api
from flask_sqlalchemy import Model
from sqlalchemy import inspect

from compair.core import db

def pagination(model):
    """
    The decorator for Restful list pagination. It takes the Model for the parameter. For
    paging information, it reads the `page` and `results_per_page` parameters from request
    object. It also injects the queried objects into the get list method. e.g.::

        class UserAPI
            @pagination(User)
            @marshal_with(user_fields)
            def get(self, objects):
                # change objects if necessary here
                return objects

    It can work with marshal_with, but has to be called before it.
    """

    def wrap(func):
        @wraps(func)
        def paging(*args, **kwargs):
            # pagination parameters from GET
            page = request.args.get('page', 1)
            page = int(page)  # they need to be ints
            results_per_page = request.args.get('results_per_page', 30)
            results_per_page = int(results_per_page)
            # calculate offset
            offset = (page - 1) * results_per_page
            # get data
            query_results = model.query.limit(results_per_page).offset(offset).all()
            # query_results_dict = to_dict(query_results, relations_to_remove)
            # need to bundle in the pagination information into the return
            total_pages = model.query.count() / results_per_page  # assumes integer div
            if total_pages < 1:
                total_pages = 1

            kwargs['objects'] = query_results
            objects = func(*args, **kwargs)

            return {
                "num_results": len(objects),
                "objects": objects,
                "page": page,
                "total_pages": total_pages
            }

        return paging

    return wrap


def _unauthorized_override(response):
    return jsonify({
        "title": "Unauthorized",
        "message": "Authentication Required. Please log in again."
    }), 401


def new_restful_api(blueprint):
    """
    Flask-Restful asks for authentication on 401 error through http basic-auth. Since
    we're not using http basic-auth, we have to disable this default handler.
    :param blueprint:
    :return:
    """
    api = Api(blueprint)
    api.unauthorized = _unauthorized_override
    return api


def get_model_changes(model):
    # disable db session autoflush, otherwise changes will be flushed and lost
    with db.session.no_autoflush:
        changes = dict()
        insp = inspect(model)

        # skip no changed model
        if not insp.modified:
            return

        synonyms = insp.mapper.synonyms.keys()
        for attr in insp.attrs:
            # skip synonym attributes, who has problem with .history
            if attr.key in synonyms:
                continue
            if isinstance(attr.value, Model):
                # recursive call on related model
                ret = get_model_changes(attr.value)
                if ret is not None:
                    changes[attr.key] = ret
            elif isinstance(attr.value, list):
                # TODO: fix change tracking for assocated lists
                continue
            else:
                history = attr.history
                if attr.state.modified and history.has_changes():
                    changes[attr.key] = {}
                    if len(history.deleted) > 0:
                        before_value = history.deleted[0]
                        if isinstance(before_value, Enum):
                            before_value = text_type(before_value.value)
                        changes[attr.key]['before'] = before_value
                    if len(history.added) > 0:
                        after_value = history.added[0]
                        if isinstance(after_value, Enum):
                            after_value = text_type(after_value.value)
                        changes[attr.key]['after'] = after_value

    return changes

pagination_parser = RequestParser()
pagination_parser.add_argument('page', type=int, required=False, default=1)
pagination_parser.add_argument('perPage', type=int, required=False, default=20)

# the empty list used when return result is empty
empty_list = {"objects": {},  "page": 1, "pages": 0, "total": 0, "per_page": 20}


@contextlib.contextmanager
def profiled():
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = BytesIO.BytesIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    print(s.getvalue())
