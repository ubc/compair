from flask import request, session as sess
from flask_login import current_user

from tincan import Statement, ActivityList, \
    Extensions, Context, ContextActivities

from compair.core import impersonation

from .actor import XAPIActor
from .activity import XAPIActivity
from .context import XAPIContext
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.learning_record import LearningRecord

class XAPIStatement(object):
    @classmethod
    def _add_default(cls, user, statement):
        if not statement.timestamp:
            statement.timestamp = LearningRecord.generate_timestamp()

        if impersonation.is_impersonating() and user.id == current_user.id:
            statement.actor = XAPIActor.generate_actor(impersonation.get_impersonation_original_user())
        else:
            statement.actor = XAPIActor.generate_actor(user)

        # add default context info
        if not statement.context:
            statement.context = Context()

        if not statement.context.context_activities:
            statement.context.context_activities = ContextActivities()

        if not statement.context.context_activities.category:
            statement.context.context_activities.category = ActivityList()

        statement.context.context_activities.category.append(
            XAPIActivity.compair_source()
        )

        statement.context.platform = ResourceIRI.compair()
        if not statement.context.extensions:
            statement.context.extensions = Extensions()

        statement.context.extensions['http://id.tincanapi.com/extension/session-info'] = {
            'id': ResourceIRI.user_session(sess.get('session_id', '')),
            'start_at': sess.get('start_at'),
            'login_method': sess.get('login_method'),
        }
        if sess.get('end_at'):
            statement.context.extensions['http://id.tincanapi.com/extension/session-info']['end_at'] = sess.get('end_at')

        if impersonation.is_impersonating() and user.id == current_user.id:
            statement.context.extensions['http://id.tincanapi.com/extension/session-info']['impersonating-as'] = XAPIActor.generate_actor(user).as_version()

        statement.context.extensions['http://id.tincanapi.com/extension/browser-info'] = {}

        if request and request.environ.get('HTTP_USER_AGENT'):
            statement.context.extensions['http://id.tincanapi.com/extension/browser-info']['user-agent'] = request.environ.get('HTTP_USER_AGENT')

        if request and request.environ.get('HTTP_REFERER'):
            statement.context.extensions['http://id.tincanapi.com/extension/browser-info']['referer'] = request.environ.get('HTTP_REFERER')

        return statement


    @classmethod
    def generate_from_params(cls, user, params, course=None):
        statement = Statement(params)
        if course:
            XAPIContext._add_sis_data(statement.context, course)
        return cls._add_default(user, statement)

    @classmethod
    def generate(cls, user, verb, object, context=None, result=None, timestamp=None):
        statement = Statement(
            verb=verb,
            object=object,
            context=context,
            result=result,
            timestamp=timestamp
        )
        return cls._add_default(user, statement)
