import datetime
import pytz

from flask import request
from flask_login import current_user

from tincan import RemoteLRS, Statement, Agent, AgentAccount, Verb, \
    Activity, ActivityDefinition, ActivityList, Extensions, \
    Context, ContextActivities, LanguageMap, StateDocument

from compair.core import impersonation

from .actor import XAPIActor
from .extension import XAPIExtension
from .activity import XAPIActivity
from .resource_iri import XAPIResourceIRI

class XAPIStatement(object):
    @classmethod
    def _add_default(cls, user, statement):
        if not statement.timestamp:
            statement.timestamp = datetime.datetime.now().replace(tzinfo=pytz.utc).isoformat()

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

        statement.context.platform = XAPIResourceIRI.compair()

        if request and request.environ.get('HTTP_USER_AGENT'):
            if not statement.context.extensions:
                statement.context.extensions = Extensions()
            browser_info_key = XAPIExtension.context_extensions.get('browser information')
            statement.context.extensions[browser_info_key] = request.environ.get('HTTP_USER_AGENT')

        if request and request.environ.get('HTTP_REFERER'):
            if not statement.context.extensions:
                statement.context.extensions = Extensions()
            referer_key = XAPIExtension.context_extensions.get('referer')
            statement.context.extensions[referer_key] = request.environ.get('HTTP_REFERER')

        if impersonation.is_impersonating() and user.id == current_user.id:
            if not statement.context.extensions:
                statement.context.extensions = Extensions()
            impersonating_as_key = XAPIExtension.context_extensions.get('impersonating as')
            statement.context.extensions[impersonating_as_key] = XAPIActor.generate_actor(user)

        return statement


    @classmethod
    def generate_from_params(cls, user, params):
        statement = Statement(params)
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
