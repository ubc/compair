import datetime
import pytz

from flask import request

from tincan import RemoteLRS, Statement, Agent, AgentAccount, Verb, \
    Activity, ActivityDefinition, ActivityList, Extensions, \
    Context, ContextActivities, LanguageMap, StateDocument

from .actor import XAPIActor
from .extension import XAPIExtension
from .activity import XAPIActivity

class XAPIStatement(object):
    @classmethod
    def _add_default(cls, user, statement):
        if not statement.timestamp:
            statement.timestamp = datetime.datetime.now().replace(tzinfo=pytz.utc).isoformat()

        statement.actor = XAPIActor.generate_actor(user)

        # add default context info
        if not statement.context:
            statement.context = Context()

        if not statement.context.context_activities:
            statement.context.context_activities = ContextActivities()

            if not statement.context.context_activities.category:
                statement.context.context_activities.category = ActivityList()

            statement.context.context_activities.category.append(
                XAPIActivity.ubc_profile()
            )
            statement.context.context_activities.category.append(
                XAPIActivity.compair_source()
            )

        if not statement.context.extensions:
            statement.context.extensions = Extensions()

        browser_info_key = XAPIExtension.context_extensions.get('browser information')
        referer_key = XAPIExtension.context_extensions.get('referer')

        statement.context.extensions[browser_info_key] = request.environ.get('HTTP_USER_AGENT')
        statement.context.extensions[referer_key] = request.environ.get('HTTP_REFERER')

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
