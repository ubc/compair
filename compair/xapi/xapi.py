import socket

from flask import current_app, request
from tincan import RemoteLRS
from compair.models import XAPILog
from compair.core import db

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
        cls.send_statements([statement])

    @classmethod
    def send_statements(cls, statements):
        if not cls.enabled:
            return

        if current_app.config.get('LRS_STATEMENT_ENDPOINT') == 'local':
            xapi_logs = []
            for statement in statements:
                xapi_logs.append(XAPILog(
                    statement=statement.to_json(cls._version)
                ))
            db.session.add_all(xapi_logs)
            db.session.commit()

        else:
            from compair.tasks.xapi_statement import send_lrs_statements
            send_lrs_statements.delay(statements)

    @classmethod
    def _send_lrs_statements(cls, statements):
        if not cls.enabled:
            return

        # should only be called by delayed task send_lrs_statements
        lrs_settings = {
            'version': cls._version,
            'endpoint': current_app.config.get('LRS_STATEMENT_ENDPOINT')
        }

        if current_app.config.get('LRS_AUTH'):
            lrs_settings['auth'] = current_app.config.get('LRS_AUTH')
        else:
            lrs_settings['username'] = current_app.config.get('LRS_USERNAME')
            lrs_settings['password'] = current_app.config.get('LRS_PASSWORD')

        lrs =  RemoteLRS(**lrs_settings)
        try:
            lrs_response = lrs.save_statements(statements)

            if not lrs_response.success:
                current_app.logger.error("xAPI Failed with: " + str(lrs_response.data))
                current_app.logger.error("xAPI Request Body: " + lrs_response.request.content)

        except socket.error as error:
            if error.errno != socket.errno.ECONNREFUSED:
                raise error

            current_app.logger.error("xAPI Failed with: Connection refused")
            current_app.logger.error("xAPI Statements:")
            for statement in statements:
                current_app.logger.error(statement.to_json(cls._version))