from flask import Blueprint
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask_login import login_required, current_user
from flask_restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import exc, or_, and_, desc, asc
from six import text_type

from . import dataformat
from compair.core import event, db, abort
from compair.authorization import require
from compair.models import LTIConsumer
from .util import new_restful_api, get_model_changes, pagination_parser

lti_consumer_api = Blueprint('lti_consumer_api', __name__)
api = new_restful_api(lti_consumer_api)

def non_blank_text(value):
    if value is None:
        return None
    else:
        return None if text_type(value).strip() == "" else text_type(value)

new_consumer_parser = reqparse.RequestParser()
new_consumer_parser.add_argument('oauth_consumer_key', type=str, required=True, nullable=False)
new_consumer_parser.add_argument('oauth_consumer_secret', type=str)
new_consumer_parser.add_argument('global_unique_identifier_param', type=non_blank_text)
new_consumer_parser.add_argument('student_number_param', type=non_blank_text)
new_consumer_parser.add_argument('custom_param_regex_sanitizer', type=non_blank_text)

existing_consumer_parser = new_consumer_parser.copy()
existing_consumer_parser.add_argument('id', type=str, required=True, nullable=False)
existing_consumer_parser.add_argument('active', type=bool, default=True)

consumer_list_parser = pagination_parser.copy()
consumer_list_parser.add_argument('orderBy', type=str, required=False, default=None)
consumer_list_parser.add_argument('reverse', type=bool, default=False)

# events
on_consumer_list_get = event.signal('LTI_CONSUMER_LIST_GET')
on_consumer_get = event.signal('LTI_CONSUMER_GET')
on_consumer_update = event.signal('LTI_CONSUMER_EDIT')
on_consumer_create = event.signal('LTI_CONSUMER_CREATE')

# /
class ConsumerAPI(Resource):
    @login_required
    def get(self):
        require(MANAGE, LTIConsumer,
            title="Consumers Unavailable",
            message="Sorry, your system role does not allow you to view LTI consumers.")

        params = consumer_list_parser.parse_args()

        query = LTIConsumer.query

        if params['orderBy']:
            if params['reverse']:
                query = query.order_by(desc(params['orderBy']))
            else:
                query = query.order_by(asc(params['orderBy']))
        query = query.order_by(LTIConsumer.created)

        page = query.paginate(params['page'], params['perPage'])

        on_consumer_list_get.send(
            self,
            event_name=on_consumer_list_get.name,
            user=current_user)

        return {'objects': marshal(page.items, dataformat.get_lti_consumer()),
            "page": page.page, "pages": page.pages, "total": page.total, "per_page": page.per_page}

    @login_required
    def post(self):
        params = new_consumer_parser.parse_args()

        consumer = LTIConsumer()
        require(CREATE, consumer,
            title="Consumer Not Saved",
            message="Sorry, your system role does not allow you to save LTI consumers.")

        consumer.oauth_consumer_key = params.get("oauth_consumer_key")
        consumer.oauth_consumer_secret = params.get("oauth_consumer_secret")
        consumer.global_unique_identifier_param = params.get("global_unique_identifier_param")
        consumer.student_number_param = params.get("student_number_param")
        consumer.custom_param_regex_sanitizer = params.get("custom_param_regex_sanitizer")

        try:
            db.session.add(consumer)
            db.session.commit()
            on_consumer_create.send(
                self,
                event_name=on_consumer_create.name,
                user=current_user,
                consumer=consumer,
                data={'consumer': marshal(consumer, dataformat.get_lti_consumer())}
            )
        except exc.IntegrityError:
            db.session.rollback()
            abort(409, title="Consumer Not Saved", message="An LTI consumer with the same consumer key already exists. Please double-check the consumer key and try saving again.")

        return marshal(consumer, dataformat.get_lti_consumer(include_sensitive=True))


api.add_resource(ConsumerAPI, '')


# /:consumer_uuid
class ConsumerIdAPI(Resource):
    @login_required
    def get(self, consumer_uuid):
        consumer = LTIConsumer.get_by_uuid_or_404(consumer_uuid)
        require(READ, consumer,
            title="Consumer Unavailable",
            message="Sorry, your system role does not allow you to view LTI consumers.")

        on_consumer_get.send(
            self,
            event_name=on_consumer_get.name,
            user=current_user
        )

        return marshal(consumer, dataformat.get_lti_consumer(include_sensitive=True))

    @login_required
    def post(self, consumer_uuid):
        consumer = LTIConsumer.get_by_uuid_or_404(consumer_uuid)
        require(EDIT, consumer,
            title="Consumer Not Saved",
            message="Sorry, your system role does not allow you to save LTI consumers.")

        params = existing_consumer_parser.parse_args()

        # make sure the course id in the url and the course id in the params match
        if params['id'] != consumer_uuid:
            abort(400, title="Consumer Not Saved", message="The LTI consumer ID does not match the URL, which is required in order to save the LTI consumer.")

        consumer.oauth_consumer_key = params.get("oauth_consumer_key")
        consumer.oauth_consumer_secret = params.get("oauth_consumer_secret")
        consumer.global_unique_identifier_param = params.get("global_unique_identifier_param")
        consumer.student_number_param = params.get("student_number_param")
        consumer.custom_param_regex_sanitizer = params.get("custom_param_regex_sanitizer")
        consumer.active = params.get("active")

        try:
            db.session.commit()
            on_consumer_update.send(
                self,
                event_name=on_consumer_update.name,
                user=current_user,
                consumer=consumer
            )
        except exc.IntegrityError:
            db.session.rollback()
            abort(409, title="Consumer Not Saved", message="An LTI consumer with the same consumer key already exists. Please double-check the consumer key and try saving again.")

        return marshal(consumer, dataformat.get_lti_consumer(include_sensitive=True))


api.add_resource(ConsumerIdAPI, '/<consumer_uuid>')
