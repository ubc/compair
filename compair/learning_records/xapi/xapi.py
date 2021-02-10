from flask import current_app, request
from tincan import RemoteLRS
from compair.models import XAPILog
from compair.core import db
from six import text_type

from compair.tasks import emit_lrs_xapi_statement

from tincan import Statement
from compair.learning_records.learning_record import LearningRecord

class XAPI(LearningRecord):
    _version = '1.0.3'

    @classmethod
    def enabled(cls):
        return current_app.config.get('XAPI_ENABLED')

    @classmethod
    def storing_locally(cls):
        return current_app.config.get('LRS_XAPI_STATEMENT_ENDPOINT') == 'local'

    @classmethod
    def emit(cls, statement):
        if not cls.enabled():
            return

        xapi_log = XAPILog(
            statement=statement.to_json(cls._version),
            transmitted=cls.storing_locally()
        )
        db.session.add(xapi_log)
        db.session.commit()

        if not cls.storing_locally():
            emit_lrs_xapi_statement.delay(xapi_log.id)

    @classmethod
    def _emit_to_lrs(cls, statement_json):
        if not cls.enabled:
            return

        # should only be called by delayed task send_lrs_statement
        lrs_settings = {
            'version': cls._version,
            'endpoint': current_app.config.get('LRS_XAPI_STATEMENT_ENDPOINT')
        }

        if current_app.config.get('LRS_XAPI_AUTH'):
            lrs_settings['auth'] = current_app.config.get('LRS_XAPI_AUTH')
        else:
            lrs_settings['username'] = current_app.config.get('LRS_XAPI_USERNAME')
            lrs_settings['password'] = current_app.config.get('LRS_XAPI_PASSWORD')

        statement = Statement(statement_json)
        lrs = RemoteLRS(**lrs_settings)
        lrs_response = lrs.save_statement(statement)

        if not lrs_response.success:
            current_app.logger.error("xAPI Failed with: " + str(lrs_response.data))
            current_app.logger.error("xAPI Request Body: " + lrs_response.request.content)