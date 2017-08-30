from flask import current_app, request
from tincan import RemoteLRS
from compair.models import XAPILog
from compair.core import db
from six import text_type

from tincan import Statement

class XAPI(object):
    _version = '1.0.1'

    @classmethod
    def enabled(cls):
        return current_app.config.get('XAPI_ENABLED')

    @classmethod
    def get_base_url(cls):
        base_url = current_app.config.get('XAPI_APP_BASE_URL')

        if not base_url:
            base_url = request.url_root if request else ''

        return base_url

    @classmethod
    def send_statement(cls, statement):
        if not cls.enabled:
            return

        statement_string = statement.to_json(cls._version)

        if current_app.config.get('LRS_STATEMENT_ENDPOINT') == 'local':
            xapi_log = XAPILog(
                statement=statement_string
            )
            db.session.add(xapi_log)
            db.session.commit()

        else:
            from compair.tasks import send_lrs_statement
            send_lrs_statement.delay(statement_string)


    @classmethod
    def _trim_text_to_size(cls, text):
        size_limit = current_app.config.get('LRS_USER_INPUT_FIELD_SIZE_LIMIT')
        encoded_text = text.encode('utf-8')

        # if encoded_text is larger than size_limit, trim it
        if len(encoded_text) > size_limit:
            encoded_text = encoded_text[:size_limit]
            return text_type(encoded_text.decode('utf-8', 'ignore'))+" [TEXT TRIMMED]..."
        else:
            return text

    @classmethod
    def _send_lrs_statement(cls, statement_json):
        if not cls.enabled:
            return

        # should only be called by delayed task send_lrs_statement
        lrs_settings = {
            'version': cls._version,
            'endpoint': current_app.config.get('LRS_STATEMENT_ENDPOINT')
        }

        if current_app.config.get('LRS_AUTH'):
            lrs_settings['auth'] = current_app.config.get('LRS_AUTH')
        else:
            lrs_settings['username'] = current_app.config.get('LRS_USERNAME')
            lrs_settings['password'] = current_app.config.get('LRS_PASSWORD')

        statement = Statement(statement_json)
        # check statement.result.response, object.definition.name, object.definition.description
        if statement.result and statement.result.response:
            statement.result.response = cls._trim_text_to_size(statement.result.response)
        if statement.object and statement.object.definition and statement.object.definition.name:
            statement.object.definition.name['en-US'] = cls._trim_text_to_size(statement.object.definition.name['en-US'])
        if statement.object and statement.object.definition and statement.object.definition.description:
            statement.object.definition.description['en-US'] = cls._trim_text_to_size(statement.object.definition.description['en-US'])

        lrs = RemoteLRS(**lrs_settings)
        lrs_response = lrs.save_statement(statement)

        if not lrs_response.success:
            current_app.logger.error("xAPI Failed with: " + str(lrs_response.data))
            current_app.logger.error("xAPI Request Body: " + lrs_response.request.content)