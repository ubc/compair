from flask import Blueprint, jsonify
from sqlalchemy import text

from compair.core import db

healthz_api = Blueprint("healthz_api", __name__, url_prefix='/api')


@healthz_api.route('/healthz', methods=['GET'])
def healthz():
    checks = {}

    try:
        db.session.execute(text('SELECT 1'))
        checks['db'] = 'ok'
    except Exception as e:
        checks['db'] = 'error'

    healthy = all(v == 'ok' for v in checks.values())
    status_code = 200 if healthy else 503

    return jsonify({
        'status': 'ok' if healthy else 'error',
        'checks': checks,
    }), status_code
