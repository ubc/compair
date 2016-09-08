from flask import Blueprint, jsonify

healthz_api = Blueprint("healthz_api", __name__, url_prefix='/api')


@healthz_api.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'OK'})
