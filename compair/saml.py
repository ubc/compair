from flask import current_app, url_for, session as sess
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from lti.utils import urlparse
import requests
import json


def prepare_from_request(request):
    url_data = urlparse.urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }

def _get_saml_settings():
    # load settings from environment
    settings = current_app.config.get('SAML_SETTINGS')

    # if settings doesn't exist and a file is provided, load the file
    settings_file = current_app.config.get('SAML_SETTINGS_FILE')
    if not settings and settings_file:
        with open(settings_file, 'r') as json_data_file:
            settings = json.load(json_data_file)

    # if saml metadata url is provided, load idp settings via metadata
    idp_metadata_url = current_app.config.get('SAML_METADATA_URL')
    idp_metadata_entity_id = current_app.config.get('SAML_METADATA_ENTITY_ID', None)
    if idp_metadata_url:
        idp_settings = OneLogin_Saml2_IdPMetadataParser.parse_remote(
            idp_metadata_url,
            entity_id=idp_metadata_entity_id
        )

        settings = OneLogin_Saml2_IdPMetadataParser.merge_settings(settings, idp_settings)

    return settings

def _get_auth(request):
    req = prepare_from_request(request)
    auth = OneLogin_Saml2_Auth(req, _get_saml_settings())
    return auth

def get_saml_login_url(request):
    return _get_auth(request).login()

def get_saml_auth_response(request):
    auth = _get_auth(request)
    auth.process_response()
    return auth

def get_saml_logout_url(request):
    auth = _get_auth(request)

    # redirect user back to application is single sign out url is none
    logout_service_url = url_for('route_app', _external=True)
    if auth.get_slo_url() is None:
        return logout_service_url

    return auth.logout(
        name_id=sess.get('SAML_NAME_ID'),
        session_index=sess.get('SAML_SESSION_INDEX'),
        return_to=logout_service_url
    )
